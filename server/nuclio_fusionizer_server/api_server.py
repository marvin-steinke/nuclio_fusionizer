import os

import uvicorn
from fastapi import Body, FastAPI, Form, UploadFile, File, Query
from typing import Annotated

from loguru import logger
from pydantic import BaseModel
from typing import Dict

from mapper import Mapper
from nuclio_interface import Nuctl


class ApiServer:
    """Class representing the fusionize FastAPI server.

     Possible actions are deploying, deleting, getting, and invoking functions.

     Attributes:
         app: The FastAPI instance.
         nuctl: The nuctl wrapper.
         mapper: Handles the management of fusion groups.
     """

    def __init__(self, nuctl: Nuctl) -> None:
        # Create a FastAPI app instance
        self.nuctl = nuctl
        self.mapper = Mapper()
        self.app = FastAPI()

        @self.app.put("/{function_name}/deploy/")  # (re)-deploy
        async def deploy(
                function_name: str = Form(...),
                namespace: str = Form(...),
                function_configuration: UploadFile = File(None),  # Optional
                function: UploadFile = File(None)  # Optional
        ) -> Dict[str, str]:
            """Deploy endpoint for deploying functions.

            Args:
                function_name: The name of the function.
                namespace: The namespace.
                function_configuration: The function configuration file.
                function: The function source file.

            Returns:
                A dictionary indicating the status of the deployment.
            """
            config_path = f"/path/to/save/config/{function_configuration.filename}"
            if function_configuration:
                # TODO what path to save tmp config file?
                with open(config_path, "wb") as buffer:
                    buffer.write(function_configuration.file.read())

            function_path = f"/path/to/save/functions/{function.filename}"
            if function:
                # TODO what path to save tmp function file?
                with open(function_path, "wb") as buffer:
                    buffer.write(function.file.read())

            task = self.mapper.get_task(function_name)
            if task:  # redeploy function
                pass  # TODO redeploy function in the same fusion group
            else:  # deploy function
                pass  # TODO deploy function in a new fusion group

            fusion_group = self.mapper.get_group(task)

            result = self.nuctl.deploy(
                fusion_group.name, function_path, config_path)
            return {"status": "success",
                    "function_name": function_name,
                    "result": result}

        @self.app.delete("/{function_name}/delete")
        async def delete(function_name: str) -> Dict[str, str]:
            """Delete endpoint for deleting functions.

            Args:
                function_name: Name of the function to be deleted.

            Returns:
                A dictionary indicating the status of the deletion.
            """
            task = self.mapper.get_task(function_name)
            if not task:
                err_msg = "function not found."
                logger.error(err_msg)
                return {"status": "failure", "error": err_msg}

            fusion_group = self.mapper.get_group(task)

            # TODO calculate and save new fusion setup from mapper
            # TODO update the fusion group with nuctl

            # TODO or, if fusion group is empty, then delete it in mapper
            # TODO then delete fusion group from nuctl as well

            result = self.nuctl.delete(fusion_group.name)
            return {"status": "success",
                    "function_name": function_name,
                    "result": result}

        @self.app.get("/{function_name}/get")
        async def get(function_name: str) -> Dict[str, str]:
            """Get endpoint for retrieving information about functions.

            Args:
                function_name: Name of the function to retrieve information for.

            Returns:
                A dictionary containing information about the specified function.
            """
            task = self.mapper.get_task(function_name)
            if not task:
                err_msg = "function not found."
                logger.error(err_msg)
                return {"status": "failure", "error": err_msg}

            fusion_group = self.mapper.get_group(task)

            result = self.nuctl.get(fusion_group.name)
            return {"status": "success",
                    "function_name": function_name,
                    "result": result}

        @self.app.post("/{function_name}")
        async def invoke(
                function_name: str,
                body: str = Body(...,
                                 description="Contains the function parameters"),
                content_type: str = Query("application/json"),
                headers: str = Query("",
                                     description="Comma-separated list of key-value pairs"),
                method: str = Query("POST")
        ) -> Dict[str, str]:
            """Invoke endpoint for invoking functions.

            Args:
                function_name: The name of the function to invoke.
                body: The request body.
                content_type: HTTP type of content in the request body.
                headers: HTTP request headers.
                method: HTTP request method (e.g., GET, POST, etc.).

            Returns:
                A dictionary indicating the success of the function invocation.
            """
            task = self.mapper.get_task(function_name)
            if not task:
                err_msg = "function not found."
                logger.error(err_msg)
                return {"status": "failure", "error": err_msg}

            fusion_group = self.mapper.get_group(task)

            result = self.nuctl.invoke(
                fusion_group.name, body, content_type, headers, method)
            return {"status": "success",
                    "function_name": function_name,
                    "result": result}

        @self.app.post("/{function_name}/update")
        async def update(
                function_name: str = Form(...),
                namespace: str = Form(...),
                function_configuration: UploadFile = File(None),  # Optional
                function: UploadFile = File(None)  # Optional
        ) -> (
                Dict)[str, str]:
            """Update endpoint for updating functions.

            Args:
                deploy_request: Annotated request object containing function deployment details.

            Returns:
                A dictionary indicating the status of the function invocation.
            """
            task = self.mapper.get_task(function_name)
            if not task:
                err_msg = "function not found."
                logger.error(err_msg)
                return {"status": "failure", "error": err_msg}

            config_path = os.path.join(task.dir_path, "function.yaml")
            if function_configuration:
                with open(config_path, "wb") as buffer:
                    buffer.write(function_configuration.file.read())

            function_path = os.path.join(task.dir_path, "dispatcher.py")
            if function:
                with open(function_path, "wb") as buffer:
                    buffer.write(function.file.read())

            fusion_group = self.mapper.get_group(task)

            result = self.nuctl.update(
                fusion_group.name, function_path, config_path)
            return {"status": "success",
                    "function_name": function_name,
                    "result": result}

    def run(self):
        """Method to start the Uvicorn server."""
        # Start the Uvicorn server
        uvicorn.run(self.app, host="0.0.0.0", port=8000)
