from __future__ import annotations
from typing import TYPE_CHECKING
from loguru import logger
import subprocess
import json
import requests

if TYPE_CHECKING:
    from nuclio_fusionizer import FusionGroup, Task


class NuctlError(Exception):
    def __init__(self, message: str, cpe: subprocess.CalledProcessError) -> None:
        super().__init__(message + ":\n" + cpe.stderr.decode("utf-8"))


class Nuctl:
    """Wrapper Class for nuctl, the nuclio cli utility.

    Attributes:
        fusionizer_address: Public or private address of the Fusionizer Server.
        namespace: The Kubernetes namespace to operate within.
        registry: The Docker registry to use for function deployments.
        kubeconfig: Path to Kubeconfig file.
        platform: The Nuclio platform to use (default is `auto`)

    Methods;
        _gloabl_flags: Returns the global flags used for nuctl commands.
        _exec_cmd: Executes a Nuclio CLI ('nuctl') command.
        deploy: Deploys a Fusion Group as a Nuclio function.
        delete: Deletes a Fusion Group deployed as a Nuclio function.
        get: Provides information about a Fusion Group deployed as a Nuclio function.
        invoke: Invokes a Task in a Fusion Group deployed as a Nuclio function.
    """

    def __init__(
        self,
        fusionizer_address: str,
        namespace: str | None = None,
        registry: str | None = None,
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
        self.fusionizer_address = fusionizer_address
        self.namespace = namespace
        self.registry = registry
        self.kubeconfig = kubeconfig
        self.platform = platform

    def _gloabl_flags(self) -> list[str]:
        """Generates and returns the global flags used for nuctl commands.

        Returns:
            The list of global flags for nuctl commands.
        """
        flags = []
        for var in ["namespace", "registry", "kubeconfig", "platform"]:
            value = getattr(self, var)
            if value:
                flags += [f"--{var}", value]
        return flags

    def _exec_cmd(self, command: list[str]) -> str:
        """Executes a Nuclio CLI ('nuctl') command and returns the command output.

        Args:
            command: The command that will be executed.

        Returns:
            The command output.
        """
        command = ["sudo"] + command + self._gloabl_flags()
        result = subprocess.run(command, check=True, capture_output=True)
        return result.stdout.decode("utf-8")

    def deploy(self, group: FusionGroup) -> None:
        """Deploys a Fusion Group as a Nuclio function.

        Args:
            group: Fusion Group object with finished build process.

        Raises:
            NuctlError if nuctl command failed.
        """
        command = [
            "nuctl", "deploy", group.name,
            "--path", group.build_dir,
        ]
        try:
            self._exec_cmd(command)
        except subprocess.CalledProcessError as e:
            nuctl_err = NuctlError(
                f"Failed to deploy Fusion Group with Tasks {str(group)}", e
            )
            logger.error(str(nuctl_err))
            raise nuctl_err
        logger.info(f"Successfully deployed Fusion Group with Tasks {str(group)}")

    def delete(self, group: FusionGroup) -> None:
        """Deletes a Fusion Group deployed as a Nuclio function.

        Args:
            group: Previously deployed Fusion Group.

        Raises:
            NuctlError if nuctl command failed.
        """
        command = ["nuctl", "delete", group.name]
        try:
            self._exec_cmd(command)
        except subprocess.CalledProcessError as e:
            nuctl_err = NuctlError(
                f"Failed to delete Fusion Group with Tasks {str(group)}", e
            )
            logger.error(str(nuctl_err))
            raise nuctl_err
        logger.info(f"Successfully deleted Fusion Group with Tasks {str(group)}")

    def get(self, group: FusionGroup) -> dict:
        """Provides information about a Fusion Group deployed as a Nuclio function.

        Args:
            group: Previously deployed Fusion Group.

        Returns:
            Fusion Group info as a dict.

        Raises:
            NuctlError if nuctl command failed.
        """
        command = ["nuctl", "get", "function", group.name, "--output", "json"]
        try:
            result = self._exec_cmd(command)
        except subprocess.CalledProcessError as e:
            nuctl_err = NuctlError(
                f"Failed to get information about Fusion Group with Tasks {str(group)}", e
            )
            logger.error(str(nuctl_err))
            raise nuctl_err
        return json.loads(result)

    def invoke(self, group: FusionGroup, task: Task, args: dict | None = None) -> str:
        """Invokes a Task in a Fusion Group deployed as a Nuclio function.

        Args:
            group: Previously deployed Fusion Group.
            task: Specific Task of group to invoke.
            args: Arguments to call the task with.

        Returns:
            The server response, i.e. the result of the Task invocation.

        Raises:
            NuctlError if nuctl command failed.
            requests.RequestException if the http invocation fails.
        """
        # Get function address
        address = "http://" + self.get(group)["status"]["internalInvocationUrls"][0]
        # Create HTML header to specify Task to call
        header = {
            "Content-Type": "application/json",
            "Task-Name": task.name,
            "Fusionizer-Server-Address": self.fusionizer_address
        }

        fail = (
            f"Failed to invoke Task {task.name} with args {args} of Fusion "
            f"Group with Tasks {str(group)}:\n"
        )
        try:
            response = requests.post(address, headers=header, json=args)
        except requests.RequestException as e:
            logger.error(fail + str(e))
            raise
        if response.status_code != 200:
            raise Exception(fail + response.text)

        logger.info(
            f"Successfully invoked Task {task.name} with args {args} of Fusion "
            f"Group with Tasks {str(group)}:\nResult: {response.text}"
        )
        return response.text
