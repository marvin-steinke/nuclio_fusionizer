from fastapi import Body, FastAPI, Form, UploadFile, File
import uvicorn
from typing import Annotated
from pydantic import BaseModel


class ApiServer:
    def __init__(self):
        # Create a FastAPI app instance
        self.app = FastAPI()

        class DeployRequest(BaseModel):
            function_name: str = Form(...)
            namespace: str = Form(...)
            function_configuration: UploadFile = None  # Optional
            function: UploadFile = None  # Optional

        @self.app.put("/deploy/")  # (re)-deploy
        async def deploy(deploy_request: Annotated[DeployRequest, Body()]):
            if deploy_request.function_configuration:
                # TODO what path to save tmp config file?
                config_path = f"/path/to/save/config/{deploy_request.function_configuration.filename}"
                with open(config_path, "wb") as buffer:
                    buffer.write(deploy_request.function_configuration.file.read())

            if deploy_request.function:
                # TODO what path to save tmp function file?
                function_path = f"/path/to/save/functions/{deploy_request.function.filename}"
                with open(function_path, "wb") as buffer:
                    buffer.write(deploy_request.function.file.read())

            # TODO add deploy logic

            # TODO return invoke endpoint
            return {"status": "success"}

        @self.app.delete("/delete/{function_name}")
        async def delete(function_name: str):
            # TODO add deletion logic
            return {"status": "success", "function_name": function_name}

        @self.app.get("/get/{function_name}")
        async def get(function_name: str):
            # TODO add logic to get resource information
            return {"status": "success", "function_name": function_name}

        @self.app.put("/invoke/{function_name}")
        async def invoke(function_name: str):
            # TODO add logic to invoke a function
            return {"status": "success", "function_name": function_name}

    def run(self):
        # Start the Uvicorn server
        uvicorn.run(self.app, host="0.0.0.0", port=8000)
