from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import PlainTextResponse
from zipfile import ZipFile
from typing import Any
import os
import uvicorn
import shutil

from nuclio_fusionizer import Mapper, Task, Nuctl


class ApiServer:
    """API Server for handling Fusionizer Requests.

    This server receives HTTP requests to perform operations on Tasks and Fusion
    Groups, which include deploying, deleting, retrieving information and
    invoking, and return appropriate responses.

    Args:
        nuctl: A Nuctl interface for deploying/deleting/invoking/getting Nuclio
            functions.
        mapper: A Mapper for mapping between Tasks and Fusion Groups.
    """

    def __init__(self, nuctl: Nuctl, mapper: Mapper) -> None:
        self.nuctl = nuctl
        self.mapper = mapper
        self.app = FastAPI()
        self.task_dir = "tasks"
        if not os.path.exists(self.task_dir):
            os.makedirs(self.task_dir)

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(
            request: Request, exc: HTTPException
        ) -> PlainTextResponse:
            return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

        @self.app.put("/{task_name}")  # (re)-deploy
        async def deploy(
            task_name: str, zip_file: UploadFile = File(...)
        ) -> PlainTextResponse:
            """Deploys a new task or redeploys an existing one.

            Args:
                task_name: The name of the Task to (re)deploy.
                zip_file: The zip file containing code for the Rask.

            Returns:
                Confirmation message of successful deployment.

            Raises:
                HTTPException if an error occurred during the deployment.
            """
            dest_dir = os.path.join(self.task_dir, task_name)
            # If path exists, user wants to redeploy
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
                os.makedirs(dest_dir)
            # Unpack zip
            with ZipFile(zip_file.file, "r") as zip_ref:
                zip_ref.extractall(dest_dir)

            # Create Task and deploy it
            task = Task(task_name, dir_path=dest_dir)
            try:
                self.mapper.deploy_single(task)
            except Exception as e:
                raise HTTPException(status_code=422, detail=str(e))

            return PlainTextResponse(f"Successfully deployed Task '{task_name}'")

        @self.app.delete("/{task_name}")
        async def delete(task_name: str) -> PlainTextResponse:
            """Deletes an existing task.

            Args:
                task_name: The name of the Task to delete.

            Returns:
                Confirmation message of successful deletion.

            Raises:
                HTTPException if the Task to delete could not be found.
            """
            try:
                self.mapper.delete(task_name)
            except Exception as e:
                raise HTTPException(status_code=422, detail=str(e))

            return PlainTextResponse(f"Successfully deleted Task '{task_name}'")

        @self.app.get("/{task_name}")
        async def get(task_name: str) -> PlainTextResponse:
            """Retrieves information about a Task.

            Args:
                task_name: The name of the Task to get information about.

            Returns:
                A dict with Task information.

            Raises:
                HTTPException if the Task could not be found or the nuctl
                command fails.
            """
            group = self.mapper.group(task_name)
            if not group:
                raise HTTPException(
                    status_code=422, detail=f"No Task '{task_name}' could be found"
                )
            try:
                group_info = self.nuctl.get(group)
            except Exception as e:
                raise HTTPException(status_code=422, detail=str(e))

            other_groups = str(group) if len(group.tasks) > 1 else "None"

            return PlainTextResponse(
                f"Task {task_name}:\n"
                f"Currently deployed with other Tasks: {other_groups}\n"
                f"Status: {group_info["status"]["state"]}\n"
                f"HTTP port: {group_info["status"]["httpPort"]}"
            )

        @self.app.post("/{task_name}")
        async def invoke(task_name: str, args: dict[str, Any] = {}) -> PlainTextResponse:
            """Invokes a Task.

            Args:
                task_name: The name of the Task to invoke.
                args: A dictionary of arguments to pass to the Task.

            Returns:
                A dict with the output of the Task.

            Raises:
                HTTPException if the Task could not be found or the nuctl
                command fails.
            """
            # Find group associated with Task
            group = self.mapper.group(task_name)
            if not group:
                raise HTTPException(
                    status_code=422, detail=f"No Task '{task_name}' could be found"
                )

            # Find Task of group
            task = None
            for group_task in group.tasks:
                if group_task.name == task_name:
                    task = group_task
            assert task is not None

            # Invoke Task
            try:
                result = self.nuctl.invoke(group, task, args)
            except Exception as e:
                raise HTTPException(status_code=422, detail=str(e))

            return PlainTextResponse(result)

    def run(self):
        """Starts the Uvicorn server for handling HTTP requests."""
        uvicorn.run(self.app, host="0.0.0.0", port=8000)
