import json
from dataclasses import dataclass, field, asdict
from copy import deepcopy


@dataclass
class Task:
    """Class representing a single task.

    Attributes:
        name: Name of the task.
        code_path: Path of the source code file.
        config_path: Path of the configuration file.
        nuclio_endpoint: Connection endpoint of the task.
        fusionizer_endpoint: Connection endpoint of the fusionizer.

    Methods:
        __eq__: Equality comparison handler that compares tasks by name.
    """
    name: str
    code_path: str
    config_path: str
    nuclio_endpoint: str
    fusionizer_endpoint: str

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
    nuclio_endpoint: str
    tasks: list[Task] = field(default_factory=list)

    def to_json(self) -> str:
        """Converts the class instance into a JSON string.

        Returns:
           JSON string of the class instance.
        """
        # Convert to JSON, handling nested Task objects
        return json.dumps(asdict(self), default=lambda o: o.__dict__)

    @classmethod
    def from_json(cls, group_data: dict) -> 'FusionGroup':
        """Create a FusionGroup instance from JSON data.

        Args:
            group_data: Dictionary containing fusion group configuration.

        Returns:
            FusionGroup instance.
        """
        nuclio_endpoint = group_data["nuclio_endpoint"]
        tasks_data = group_data.get("tasks", [])
        tasks = [
            Task(
                name=task_data["name"],
                code_path=task_data["code_path"],
                config_path=task_data["config_path"],
                nuclio_endpoint=task_data["nuclio_endpoint"],
                fusionizer_endpoint=task_data["fusionizer_endpoint"],
            )
            for task_data in tasks_data
        ]
        return cls(nuclio_endpoint=nuclio_endpoint, tasks=tasks)

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


@dataclass
class Mapper:
    """Singleton class that handles the management of fusion groups.

    Attributes:
        _instance: Stores the instance of the class.
        _fusion_setup: A list of fusion groups. 

    Methods:
        tasks: Return all tasks in the fusion setup.
        get: Return deepcopy of the current fusion setup.
        update: Replace the current fusion setup with the new setup provided.
        get_group: Return the group where the task is present.
    """
    _instance = None
    _fusion_setup: list[FusionGroup] = field(default_factory=list)

    def __new__(cls) -> 'Mapper':
        """Singleton implementation, handles the creation of the class instance.
    
        Returns:
            Same instance if it's already been created else it creates a new one.
        """
        if cls._instance is None:
            cls._instance = super(Mapper, cls).__new__(cls)
        return cls._instance

    @classmethod
    def parse_fusion_groups_from_json(cls, json_path: str) -> list[FusionGroup]:
        """Parse fusion groups from a JSON file.

        Args:
            json_path: Path to the JSON file containing fusion group configurations.

        Returns:
            List of FusionGroups parsed from the JSON file.
        """
        with open(json_path, 'r') as json_file:
            fusion_groups_config = json.load(json_file)

        fusion_groups = [FusionGroup.from_json(group_data) for group_data in
                         fusion_groups_config]

        return fusion_groups

    def tasks(self) -> list[Task]:
        """Return all tasks in the fusion setup.

        Returns:
            List of all tasks in the fusion setup.
        """
        return [task for group in self._fusion_setup for task in group.tasks]

    def get(self) -> list[FusionGroup]:
        """Returns a deep copy of the fusion setup.

        Returns:
            Deepcopy of the fusion setup.
        """
        # fuison setup may not be trivially changed, use self.update()
        return deepcopy(self._fusion_setup)

    def update(self, new_setup: list[FusionGroup]) -> None:
        """Updates the fusion setup with the new setup provided.

        Altered or new fusion groups are deployed while old groups are deleted.

        Args:
            new_setup: A list of fusion groups to become the new setup.
        """
        intersection = set(new_setup) & set(self._fusion_setup)
        to_deploy = set(new_setup) - intersection
        to_delete = set(self._fusion_setup) - intersection
        # TODO add deploy and delete logic via nuclio_interface.py
        # assume the nuclio_endpoints are conserved by caller
        self._fusion_setup = new_setup

    def get_group(self, task: Task) -> FusionGroup | None:
        """Returns the group in which the task is present.

        Args:
            task: Task to find the group for.

        Returns:
            The FusionGroup object in which the task is present or None if not found.
        """
        for group in self._fusion_setup:
            if task in group.tasks:
                return group
        return None
