from __future__ import annotations
from typing import TYPE_CHECKING
from loguru import logger
import subprocess
import os
import json

if TYPE_CHECKING:
    from nuclio_fusionizer_server.mapper import FusionGroup, Task


class Nuctl:
    """Wrapper Class for nuctl, the nuclio cli utility.

    Attributes:
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

    def deploy(self, group: FusionGroup) -> str:
        """Deploys a Fusion Group as a Nuclio function.

        Args:
            group: Fusion Group object with finished build process.

        Returns:
            The server response.
        """
        command = [
            "nuctl",
            "deploy",
            group.name,
            "--path",
            group.build_dir,
            "--file",
            os.path.join(group.build_dir, "function.yaml"),
        ]
        try:
            result = self._exec_cmd(command)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy Fusion Group with Tasks {str(group)}:\n{e}")
            raise e
        logger.info(
            f"Successfully deployed Fusion Group with Tasks {str(group)}:\n{result}"
        )
        return result

    def delete(self, group: FusionGroup) -> str:
        """Deletes a Fusion Group deployed as a Nuclio function.

        Args:
            group: Previously deployed Fusion Group.

        Returns:
            The server response.
        """
        command = ["nuctl", "delete", group.name]
        try:
            result = self._exec_cmd(command)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete Fusion Group with Tasks {str(group)}:\n{e}")
            raise e
        logger.info(
            f"Successfully deleted Fusion Group with Tasks {str(group)}:\n{result}"
        )
        return result

    def get(self, group: FusionGroup) -> str:
        """Provides information about a Fusion Group deployed as a Nuclio function.

        Args:
            group: Previously deployed Fusion Group.

        Returns;
            The server response.
        """
        command = ["nuctl", "get", "function", group.name]
        try:
            result = self._exec_cmd(command)
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to retrieve information about Fusion Group with "
                f"Tasks {str(group)}:\n{e}"
            )
            raise e
        logger.info(
            "Successfully retrieved information about Fusion Group with Tasks "
            f"{str(group)}:\n{result}"
        )
        return result

    def invoke(self, group: FusionGroup, task: Task, args: dict) -> str:
        """Invokes a Task in a Fusion Group deployed as a Nuclio function.

        Args:
            group: Previously deployed Fusion Group.
            task: Specific Task of group to invoke.
            args: Arguments to call the task with.

        Returns:
            The server response.
        """
        # TODO create HTML header to specify Task to call
        header = task.name
        body = json.dumps(args)
        command = [
            "nuctl", "invoke", group.name,
            "--content-type", "application/json",
            "--body", body,
            "--headers", header,
        ]
        try:
            result = self._exec_cmd(command)
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to invoke Task {task.name} with args {body} of Fusion "
                f"Group with Tasks {str(group)}:\n{e}"
            )
            raise e
        logger.info(
            f"Successfully invoked Task {task.name} with args {body} of Fusion "
            f"Group with Tasks {str(group)}:\n{result}"
        )
        return result
