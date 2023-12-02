from fastapi import FastAPI
import uvicorn

class ApiServer:
    def __init__(self):
        # Create a FastAPI app instance
        self.app = FastAPI()

        @app.put("/deploy/") # (re)-deploy
        async def deploy(
            function_name: str = Form(...), 
            namespace: str = Form(...),
            function_configuration: UploadFile = File(None), # Optional
            function: UploadFile = File(None) # Optional
        ):
            if function_configuration:
                # TODO what path to save tmp config file?
                config_path = f"/path/to/save/config/{function_configuration.filename}"
                with open(config_path, "wb") as buffer:
                    buffer.write(function_configuration.file.read())

            if function:
                # TODO what path to save tmp function file?
                function_path = f"/path/to/save/functions/{function.filename}"
                with open(function_path, "wb") as buffer:
                    buffer.write(function.file.read())

            # TODO add deploy logic

            # TODO return invoke endpoint
            return {"status": "success"}

        @app.put("/delete/{function_name}")
        async def delete(function_name: str):
            # TODO add deletion logic
            return {"status": "success", "function_name": function_name}

    def run(self):
        # Start the Uvicorn server
        uvicorn.run(self.app, host="0.0.0.0", port=8000)