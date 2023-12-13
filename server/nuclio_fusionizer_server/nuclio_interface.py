from loguru import logger
import subprocess


class Nuctl:
    """Wrapper Class for nuctl, the nuclio cli utility.

    Attributes:
        namespace: The Kubernetes namespace to operate within.
        registry: The Docker registry to use for function deployments.
        kubeconfig: Path to Kubeconfig file.
        platform: The Nuclio platform to use (default is `auto`)

    Methods;
        _gloabl_flags() -> list[str]:
            Returns the global flags used for nuctl commands.
        _exec_cmd(command: list[str]) -> str:
            Executes a Nuclio CLI ('nuctl') command.
        deploy(name: str, src_path: str, config: str) -> str
            Deploy a Nuclio function.
        delete(name: str) -> str
            Deletes a Nuclio function.
        get(kind: str) -> str
            Returns information about a Nuclio 'kind'.
        invoke(name: str, body: str, content_type: str, headers: str, method: str) -> str
            Invokes a Nuclio function with some payload.
        update(name: str, src_path: str, config: str) -> str
            Updates a Nuclio function.
    """
    def __init__(
        self,
        namespace: str,
        registry: str,
        kubeconfig: str | None = None,
        platform: str = "auto",
    ) -> None:
        # Check if nuctl is installed
        try:
            subprocess.run(["nuctl"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError as e:
            err_msg = "nuctl utility not found. Please install nuclio cli."
            logger.critical(err_msg)
            raise EnvironmentError(err_msg) from e
        self.namespace = namespace
        self.registry = registry
        self.kubeconfig = kubeconfig
        self.platform = platform

    def _gloabl_flags(self) -> list[str]:
        """Generates and returns the global flags used for nuctl commands.

        Returns:
            The list of global flags for nuctl commands.
        """
        flags = [
            "--namespace", self.namespace,
            "--registry", self.registry,
            "--platfrom", self.platform,
        ]
        if self.kubeconfig:
            flags += ["--kubeconfig", self.kubeconfig]
        return flags

    def _exec_cmd(self, command: list[str]) -> str:
        """Executes a Nuclio CLI ('nuctl') command and returns the command output.

        Args:
            command: The command that will be executed.

        Returns:
            The command output.
        """
        command += self._gloabl_flags()
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode("utf-8")

    def deploy(
        self,
        name: str,
        src_path: str,
        config: str,
    ) -> str:
        """Deploys a Nuclio function.

        Args:
        name: The name of function to deploy.
        src_path: The path to the source code.
        config: The function configuration file.

        Returns:
            The server response.
        """
        command = [
            "nuctl", "deploy", name, 
            "--path", src_path, 
            "--file", config
        ]
        return self._exec_cmd(command)

    def delete(self, name: str) -> str:
        """Deletes a Nuclio function.

        Args:
            name: The name of the function to delete.

        Returns:
            The server response.
        """
        command = ["nuctl", "delete", name]
        return self._exec_cmd(command)

    def get(self, kind: str) -> str:
        """Provides information about a Nuclio 'kind'.

        Args:
            kind: The type of Nuclio resource (e.g., function, trigger, etc.).

        Returns;
            The server response.
        """
        command = ["nuctl", "get", kind]
        return self._exec_cmd(command)

    def invoke(
        self, name: str, body: str, content_type: str, headers: str, method: str
    ) -> str:
        """Invokes a Nuclio function with a specified payload.

        Args:
            name: The name of the function to invoke.
            body: The request body.
            content_type: HTTP type of content in the request body.
            headers: HTTP request headers.
            method: HTTP request method (e.g., GET, POST, etc.).

        Returns:
            The server response.
        """
        command = [
            "nuctl", "invoke", name,
            "--body", body,
            "--content-type", content_type,
            "--headers", headers,
            "--method", method,
        ]
        return self._exec_cmd(command)

    def update(
        self,
        name: str,
        src_path: str,
        config: str,
    ) -> str:
        """Updates a Nuclio function.

        Args:
            name: The name of function to update.
            src_path: The path to the source code.
            config: The function configuration file.

        Returns:
            The server response.
        """
        command = [
            "nuctl", "update", name, 
            "--path", src_path, 
            "--file", config
        ]
        return self._exec_cmd(command)
