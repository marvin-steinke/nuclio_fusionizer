import json
from dataclasses import dataclass, field, asdict
from copy import deepcopy


@dataclass
class Task:
    """Class representing a single task.

    Attributes:
        name: Name of the task.
        dir_path: The path to the directory containing the tasks files.
        nuclio_endpoint: Connection endpoint of the task.

    Methods:
        __eq__: Equality comparison handler that compares tasks by name.
    """
    name: str
    dir_path: str
    nuclio_endpoint: str

    def __init__(self, name: str = None, dir_path: str = None,
                 nuclio_endpoint: str = None, json_data: dict = None) -> None:
        """Initialize Task.

        name, dir_path, and nuclio_endpoint should be provided;
        either as parameters or as JSON data.

        Args:
            name: Name of the task.
            dir_path: Path of the source code file.
            nuclio_endpoint: Connection endpoint of the task.
            json_data: Optional JSON data for initialization.
        """

        required_params = ["name", "dir_path", "nuclio_endpoint"]

        if json_data:
            missing_params = [param for param in required_params if
                              param not in json_data]

            if missing_params:
                raise ValueError(
                    f"Missing required parameter(s) in JSON data: "
                    f"{', '.join(missing_params)}")

            self.name = json_data.get("name", "")
            self.dir_path = json_data.get("dir_path", "")
            self.nuclio_endpoint = json_data.get("nuclio_endpoint", "")
        else:
            missing_params = [param for param in required_params if
                              locals()[param] is None]

            if missing_params:
                raise ValueError(
                    f"Missing required parameter(s): {', '.join(missing_params)}")

            self.name = name
            self.dir_path = dir_path
            self.nuclio_endpoint = nuclio_endpoint

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
        build_dir: The path to the directory containing the build files.
        tasks: A list of tasks included in the fusion.

    Methods:
        to_json: Converts the object into a JSON string.
        __eq__: Equality comparison handler that compares tasks as sets.
    """
    nuclio_endpoint: str
    build_dir: str
    tasks: list[Task] = field(default_factory=list)

    def __init__(self, nuclio_endpoint: str = None, build_dir: str = None,
                 tasks=None, json_data=None) -> None:
        """Initialize FusionGroup.

        nuclio_endpoint and build_dir should be provided;
        either as parameters or as JSON data.

        Args:
            nuclio_endpoint: Connection endpoint for the fusion.
            build_dir: The path to the directory containing the build files.
            json_data: Optional JSON data for initialization.
        """

        required_params = ["nuclio_endpoint", "build_dir"]

        if json_data:
            missing_params = [param for param in required_params if
                              param not in json_data]

            if missing_params:
                raise ValueError(
                    f"Missing required parameter(s) in JSON data: "
                    f"{', '.join(missing_params)}")

            self.nuclio_endpoint = json_data.get("nuclio_endpoint", "")
            self.build_dir = json_data.get("build_dir", "")
            tasks_data = json_data.get("tasks", [])
            self.tasks = [Task(task_data) for task_data in tasks_data]
        else:
            missing_params = [param for param in required_params if
                              locals()[param] is None]

            if missing_params:
                raise ValueError(
                    f"Missing required parameter(s): {', '.join(missing_params)}")
            if tasks is None:
                tasks = field(default_factory=list)

            self.nuclio_endpoint = nuclio_endpoint
            self.build_dir = build_dir
            self.tasks = tasks

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
