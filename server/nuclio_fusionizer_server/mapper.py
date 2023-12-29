from dataclasses import dataclass, field, asdict
from copy import deepcopy
from typing import Union
import json

from nuclio_fusionizer_server.nuclio_interface import Nuctl


@dataclass
class Task:
    """Class representing a single task.

    Attributes:
        name: Name of the task.
        nuclio_endpoint: Connection endpoint of the task.
        fusionizer_endpoint: Connection endpoint of the fusionizer.

    Methods:
        __eq__: Equality comparison handler that compares tasks by name.
    """

    name: str
    dir_path: str = field(default="")
    nuclio_endpoint: str = field(default="")

    def __eq__(self, other) -> bool:
        """Equality comparison method that compares tasks by name.

        Args:
            other: Other object to compare with.

        Returns:
            True if other is a Task and has the same name, False otherwise.
        """
        if not isinstance(other, Task):
            return NotImplemented
        return self.name == other.name


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

    nuclio_endpoint: str = field(default="")
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


class Mapper:
    """Class that handles the management of Fusion Groups.

    Args:
        nuctl: Nuclio cli utility.

    Methods:
        tasks: Return all tasks in a Fusion Setup.
        get: Return deepcopy of the current Fusion Setup.
        update: Replace the current Fusion Setup with the new setup provided.
        get_group: Return the group where the task is present.
    """

    def __init__(self, nuctl: Nuctl) -> None:
        self._nuctl = nuctl
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
        task_dict = {task.name: task for task in self.tasks(old_setup)}
        for group_config in json_config:
            group = FusionGroup()
            for task_name in group_config:
                task = (
                    Task(task_name)
                    if task_name not in task_dict
                    else task_dict[task_name]
                )
                group.tasks.append(task)
            if group in old_setup:
                group = old_setup[old_setup.index(group)]
            new_setup.append(group)
        return new_setup

    def update(self, new_setup: list[list[str]] | list[FusionGroup]) -> None:
        """Updates the Fusion Setup with the new setup provided.

        Altered or new Fusion Groups are deployed while old groups are deleted.

        Args:
            new_setup: A list of Fusion Groups to become the new setup.
        """
        if new_setup is list[list[str]]:
            new_setup = self.json_to_setup(new_setup)
        assert new_setup is list[FusionGroup]

        intersection = set(new_setup) & set(self._fusion_setup)
        to_deploy = set(new_setup) - intersection
        to_delete = set(self._fusion_setup) - intersection
        # TODO add deploy and delete logic via nuclio_interface.py
        self._fusion_setup = new_setup

    def get_group(
        self, setup: list[FusionGroup], task: Task
    ) -> Union[FusionGroup, None]:
        """Returns the group in which the task is present.

        Args:
            task: Task to find the group for.
            setup: A list of Fusion Groups.

        Returns:
            The FusionGroup object in which the task is present or None if not found.
        """
        for group in setup:
            if task in group.tasks:
                return group
        return None
