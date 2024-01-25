from __future__ import annotations
from loguru import logger
from typing import TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from copy import deepcopy
from typing import Union
import json

if TYPE_CHECKING:
    from nuclio_fusionizer import Nuctl, Fuser, NuctlError


@dataclass
class Task:
    """Class representing a single task.

    Attributes:
        name: Name of the task.
        dir_path: Path to the Tasks implementation.

    Methods:
        __eq__: Equality comparison handler that compares tasks by name.
    """

    name: str
    dir_path: str = field(default="")

    def __eq__(self, other) -> bool:
        """Equality comparison method that compares tasks by name.

        Args:
            other: Other object to compare with.

        Returns:
            True if other is a Task and has the same name, False otherwise.
        """
        if not isinstance(other, Task):
            return NotImplemented
        return str(self) == str(other)

    def __str__(self) -> str:
        """String representation for a Task.

        Returns:
            The name of the Task.
        """
        return self.name

    def __hash__(self) -> int:
        """Hash method, uses the Tasks name to return hash value.

        Returns:
            Integer hash value of the Tasks name.
        """
        return hash(str(self))


@dataclass
class FusionGroup:
    """Class representing a group of tasks that get fused together.

    Attributes:
        nuclio_endpoint: Connection endpoint for the fusion.
        tasks: A list of tasks included in the fusion.

    Methods:
        to_json: Converts the object into a JSON string.
        __eq__: Equality comparison handler that compares tasks as sets.
    """

    name: str = field(default="")
    build_dir: str = field(default="")
    tasks: list[Task] = field(default_factory=list)

    def to_json(self) -> str:
        """Converts the class instance into a JSON string.

        Returns:
           JSON string of the class instance.
        """
        # Convert to JSON, handling nested Task objects
        return json.dumps(asdict(self), default=lambda o: o.__dict__)

    def __eq__(self, other) -> bool:
        """Equality comparison method that compares tasks as sets.

        Args:
            other: Other object to compare with.

        Returns:
            True if other is a FusionGroup and has the same tasks, False otherwise.
        """
        if not isinstance(other, FusionGroup):
            return NotImplemented
        # Compare tasks as sets
        return set(self.tasks) == set(other.tasks)

    def gen_name(self) -> None:
        """Generates the groups name based on names of the tasks."""
        self.name = "".join(str(task) for task in self.tasks)

    def __str__(self) -> str:
        """Returns a comma separated string of the names of all the tasks.

        Return:
            The name string.
        """
        return str([str(task) for task in self.tasks])

    def __hash__(self) -> int:
        """Hash method, uses the Fusion Group's name to return hash value.

        Returns:
            Integer hash value of the Fusion Group's name.
        """
        return hash(self.name)


class Mapper:
    """Class that handles the management of Fusion Groups.

    Args:
        nuctl: Nuclio cli utility.
        fuser: Fuser object, that handles the fusion of Tasks.

    Methods:
        tasks: Return all tasks in a Fusion Setup.
        get: Return deepcopy of the current Fusion Setup.
        update: Replace the current Fusion Setup with the new setup provided.
        get_group: Return the group where the task is present.
    """

    def __init__(self, nuctl: Nuctl, fuser: Fuser) -> None:
        self._nuctl = nuctl
        self._fuser = fuser
        self._fusion_setup: list[FusionGroup] = []

    def tasks(self, setup: list[FusionGroup]) -> list[Task]:
        """Return all tasks in a Fusion Setup.

        Args:
            setup: A list of Fusion Groups.

        Returns:
            List of all tasks in the Fusion Setup.
        """
        return [task for group in setup for task in group.tasks]

    def get(self) -> list[FusionGroup]:
        """Returns a deep copy of the Fusion Setup.

        Returns:
            Deepcopy of the Fusion Setup.
        """
        # Fusion Setup may not be trivially changed, use self.update()
        return deepcopy(self._fusion_setup)

    def json_to_setup(self, json_config: list[list[str]]) -> list[FusionGroup]:
        """Recreates list of FusionGroup instances from JSON input.

        This function initializes FusionGroups using the configurations defined
        in the input JSON file. For each group in the json_config, it appends
        the appropriate task to the group. If the group already exists in the
        current setup, then the old group is used instead of creating a new one.

        Args:
            json_config: A list of lists where each inner list comprises strings
                representing task names, which together define a FusionGroup.

        Returns:
            A list of FusionGroups as defined in the json_config.
        """
        new_setup: list[FusionGroup] = []
        old_setup = self.get()
        task_dict = {str(task): task for task in self.tasks(old_setup)}
        for group_config in json_config:
            group = FusionGroup()
            for task_name in group_config:
                if task_name in task_dict:
                    group.tasks.append(task_dict[task_name])
            group.gen_name()
            # Preserve group build dir if unchanged
            if group in old_setup:
                group = old_setup[old_setup.index(group)]
            if group.tasks:
                new_setup.append(group)
        return new_setup

    def _is_listliststr(self, var) -> bool:
        """Check if the input is a list of lists of strings.

        Args:
            var: The input variable to be checked.

        Returns:
            True if var is a list of lists of strings, False otherwise.
        """
        if isinstance(var, list):
            for item in var:
                if not isinstance(item, list):
                    return False
                for sub_item in item:
                    if not isinstance(sub_item, str):
                        return False
            return True
        return False

    def _setup_to_str(self, setup: list[FusionGroup]) -> str:
        """Converts a FusionSetup to a comma-separated string.

        Args:
            setup: The Fusion setup to be converted.

        Returns:
            A string representation of the setup, with groups separated by commas.
        """
        return f"[{", ".join([str(group) for group in setup])}]"

    def update(self, new_setup: list[list[str]] | list[FusionGroup]) -> None:
        """Updates the Fusion Setup with the new setup provided.

        Altered or new Fusion Groups are deployed while old groups are deleted.

        Args:
            new_setup: A list of Fusion Groups to become the new setup.
        """
        logger.info(
            f"Received new Fusion Setup: {new_setup}. Current Fusion Setup:"
            f"{self._setup_to_str(self._fusion_setup)}. Starting update process."
        )
        if self._is_listliststr(new_setup):
            new_setup = self.json_to_setup(new_setup)  # type: ignore

        if not new_setup:
            logger.info(
                "Fusion Setup does not contain any deployed Tasks. Cancelling "
                "update process."
            )
            return

        intersection = set(new_setup) & set(self._fusion_setup)
        logger.debug(
            "The following Fusion Groups remain intact: "
            f"{self._setup_to_str(list(intersection))}"  # type: ignore
        )
        to_deploy = set(new_setup) - intersection
        logger.debug(
            "The following new Fusion Groups are deployed: "
            f"{self._setup_to_str(list(to_deploy))}"  # type: ignore
        )
        to_delete = set(self._fusion_setup) - intersection  # type: ignore
        logger.debug(
            "The following Fusion Groups are deleted: "
            f"{self._setup_to_str(list(to_delete))}"  # type: ignore
        )
        # Deploy and delete
        for group in to_delete:
            try:
                self._nuctl.delete(group)
            except NuctlError:
                # Failures are logged in Nuctl
                pass
        for group in to_deploy:
            try:
                self._fuser.fuse(group)  # type: ignore
                self._nuctl.deploy(group)  # type: ignore
            except NuctlError:
                # Failures are logged in Nuctl
                pass
        self._fusion_setup = new_setup  # type: ignore
        logger.info(
            "Update process completed. New Fusion Setup: "
            f"{self._setup_to_str(self._fusion_setup)}"  # type: ignore
        )

    def group(self, task_name: str) -> Union[FusionGroup, None]:
        """Returns the group in which the task is present.

        Args:
            task_name: Name of the Task to find the group for.

        Returns:
            The FusionGroup object in which the task is present or None if not found.
        """
        for group in self._fusion_setup:
            for task in group.tasks:
                if str(task) == task_name:
                    return group
        return None

    def deploy_single(self, task: Task) -> None:
        """Deploys a single Task to nuclio.

        Every Task initially gets its own Fusion Group, until changed by
        Optimizer. This Fusion Group is then built and deployed to nuclio using
        nuctl.

        Args:
            task: Task to be deployed.

        Returns:
            The ouptut from nuctl.
        """
        logger.debug(f"Starting deployment process of single Task '{str(task)}'")
        group = FusionGroup()
        group.tasks.append(task)
        group.gen_name()
        self._fusion_setup.append(group)

        # Build the Fusion Group
        self._fuser.fuse(group)

        # Actually deploy the Fusion Group
        self._nuctl.deploy(group)

    def delete(self, task_name) -> None:
        """Deletes a previously deployed Task.

        To delete a deployed Task, its whole Fusion Group must be deleted from
        nuclio. Since other Tasks should remain available, the Fusion Group is
        copied and deployed w/out the to be deleted Task. After successfull
        deployment, the old Fusion Group can be deleted.

        Args:
            task_name: Name of the to be deleted Task.

        Returns:
            The ooutput from nuctl.
        """
        logger.debug(f"Starting deletion process of Task '{task_name}'")
        # Get tasks group, make deepcopy
        old_group = self.group(task_name)
        if not old_group:
            raise ValueError(f"Task '{task_name}' does not exist.")
        logger.debug(f"Current Fusion Group of '{task_name}': {str(old_group)}")

        group = deepcopy(old_group)
        # Get task in group
        task = None
        for task_ in group.tasks:
            if str(task_) == task_name:
                task = task_
                break
        assert task is not None
        # Remove task from group
        group.tasks.remove(task)
        group.gen_name()
        group.build_dir = ""

        # Check group is not empty now
        if group.name:
            # Build and deploy the new group w/out task
            logger.debug(
                f"Starting (re-)deployment process of Fusion Group {str(group)} "
                f"without Task '{task_name}'"
            )
            self._fuser.fuse(group)
            self._nuctl.deploy(group)
            # Add new group to setup
            self._fusion_setup.append(group)

        # Remove old group from setup
        self._fusion_setup.remove(old_group)
        logger.debug(
            f"State of Fusion Setup after deletion of Task '{task_name}':"
            f"{self._setup_to_str(self._fusion_setup)}"
        )

        # and delete from nuclio
        self._nuctl.delete(old_group)
