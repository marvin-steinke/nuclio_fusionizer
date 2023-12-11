import uvicorn
from fastapi import Body, FastAPI, Form, UploadFile, File
from typing import Annotated
from pydantic import BaseModel


class ApiServer:
    """Class representing the fusionize FastAPI server.

     Possible actions are deploying, deleting, getting, and invoking functions.

     Attributes:
         app: the FastAPI instance
     """

    def __init__(self) -> None:
        # Create a FastAPI app instance
        self.app = FastAPI()

        class DeployRequest(BaseModel):
            """Data model for the deploy endpoint request."""
            function_name: str = Form(...)
            namespace: str = Form(...)
            function_configuration: UploadFile = None  # Optional
            function: UploadFile = None  # Optional

        @self.app.put("/deploy/")  # (re)-deploy
        async def deploy(deploy_request: Annotated[DeployRequest, Body()]):
            """Deploy endpoint for deploying functions.

            Args:
                deploy_request: Annotated request object containing function deployment details.

            Returns:
                A dictionary indicating the status of the deployment.
            """
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
            """Delete endpoint for deleting functions.

            Args:
                function_name: Name of the function to be deleted.

            Returns:
                A dictionary indicating the status of the deletion.
            """
            # TODO add deletion logic
            return {"status": "success", "function_name": function_name}

        @self.app.get("/get/{function_name}")
        async def get(function_name: str):
            """Get endpoint for retrieving information about functions.

            Args:
                function_name: Name of the function to retrieve information for.

            Returns:
                A dictionary containing information about the specified function.
            """
            # TODO add logic to get resource information
            return {"status": "success", "function_name": function_name}

        @self.app.post("/invoke/{function_name}")
        async def invoke(function_name: str):
            """Invoke endpoint for invoking functions.

            Args:
                function_name: Name of the function to be invoked.

            Returns:
                A dictionary indicating the status of the function invocation.
            """
            # TODO add logic to invoke a function
            return {"status": "success", "function_name": function_name}

    def run(self):
        """Method to start the Uvicorn server."""
        # Start the Uvicorn server
        uvicorn.run(self.app, host="0.0.0.0", port=8000)
