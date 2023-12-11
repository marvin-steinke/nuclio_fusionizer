import time
import json
import threading
from abc import ABC, abstractmethod
from loguru import logger

from nuclio_fusionizer_server.mapper import Task, FusionGroup, Mapper
from nuclio_fusionizer_server.optimizer import Optimizer


class BaseStrategy(ABC):
    """Abstract class representing a fusionize strategy.

    Attributes:
        optimizer: The optimizer that encapsulates this strategy.
        mapper: The mapper manages the fusion group configurations.

    Methods:
        get_new_configuration: Calculates a new fusion group configuration.
    """
    optimizer: Optimizer
    mapper: Mapper

    @abstractmethod
    def __init__(self, optimizer: Optimizer, mapper: Mapper) -> None:
        self.optimizer = optimizer
        self.mapper = mapper

    @abstractmethod
    def get_new_configuration(self) -> list[FusionGroup]:
        """Calculates a new fusion group configuration using this strategy.

        Returns:
            List of FusionGroups in new configuration.
        """
        pass


class StaticStrategy(BaseStrategy):
    """Class representing a static fusionize strategy.

    Predetermined fusion group configurations are read from a json file.

    Attributes:
        optimizer: The optimizer that encapsulates this strategy.
        mapper: The mapper manages the fusion group configurations.
        seconds: The total seconds the strategy has been running.
        stop_event: Event to signal the strategy thread to stop.
        thread: Thread object representing the strategy execution.

    Methods:
        get_new_configuration: Calculates a new fusion group configuration.
    """
    seconds: int
    stop_event: threading.Event
    thread: threading.Thread

    def __init__(self, optimizer: Optimizer, mapper: Mapper) -> None:
        super().__init__(optimizer, mapper)
        self.seconds = 0
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_strategy, daemon=True)
        self.start_strategy()

    def start_strategy(self) -> None:
        """Starts the strategy thread."""
        self.thread.start()

    def stop_strategy(self) -> None:
        """Stops the strategy thread."""
        self.stop_event.set()

    def _run_strategy(self) -> None:
        """Runs the strategy in a separate thread."""
        iterations = 0
        while not self.stop_event.is_set():
            self.seconds = iterations
            self.optimizer.optimize(self.get_new_configuration())
            iterations += 1
            time.sleep(1)

    def get_new_configuration(self) -> list[FusionGroup]:
        """Calculates a new fusion group configuration using a static strategy.

        Returns:
            List of FusionGroups in new configuration.
        """

        # Read the JSON file
        with open('../test/static_strategy.json', 'r') as json_file:
            fusion_groups_config = json.load(json_file)

        # Access the fusion groups configurations
        fusion_groups_json = fusion_groups_config[
            self.seconds % len(fusion_groups_config)]

        # Get the current tasks from the mapper
        current_tasks = self.mapper.tasks()

        # Populate fusion groups with the data from the respective tasks
        fusion_groups = []
        for group_data in fusion_groups_json:
            fusion_group = FusionGroup(
                nuclio_endpoint=group_data["nuclio_endpoint"],
                tasks=[
                    task for task in current_tasks if
                    task.name in [t["name"] for t in group_data["tasks"]]
                ]
            )
            fusion_groups.append(fusion_group)

        return fusion_groups
