import time
import json
import threading
from abc import ABC, abstractmethod
from loguru import logger

from nuclio_fusionizer_server.mapper import Task, FusionGroup
from nuclio_fusionizer_server.optimizer import Optimizer


class BaseStrategy(ABC):
    """
    Abstract class representing a fusionize strategy.

    Args:
        optimizer: The optimizer that encapsulates this strategy.
    """

    @abstractmethod
    def __init__(self, optimizer: Optimizer):
        self.optimizer = optimizer

    @abstractmethod
    def get_new_configuration(self):
        """
        Abstract optimization method.

        The fusion group configurations are optimized using this strategy.

        Returns:
            List of FusionGroups in new configuration.
        """
        pass


class StaticStrategy(BaseStrategy):
    """
    Class representing a concrete fusionize strategy.

    Args:
        optimizer: The optimizer that encapsulates this strategy.
    """

    seconds: int

    def __init__(self, optimizer: Optimizer):
        super().__init__(optimizer)
        self.seconds = 0
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_strategy, daemon=True)
        self.start_strategy()

    def start_strategy(self):
        """Starts the strategy thread."""
        self.thread.start()

    def stop_strategy(self):
        """Stops the strategy thread."""
        self.stop_event.set()

    def _run_strategy(self):
        """Runs the strategy in a separate thread."""
        iterations = 0
        while not self.stop_event.is_set():
            self.seconds = iterations
            self.optimizer.optimize(self.get_new_configuration())
            iterations += 1
            time.sleep(1)

    def get_new_configuration(self):
        """
        Optimize fusion group configurations based on a static strategy.

        Returns:
            List of FusionGroups in new configuration.
        """

        # Read the JSON file
        with open('../test/static_strategy.json', 'r') as json_file:
            fusion_groups_config = json.load(json_file)

        # Access the fusion groups configurations
        fusion_groups_json = fusion_groups_config[
            self.seconds % len(fusion_groups_config)]

        # Parse fusion groups from json file
        fusion_groups = []
        for group_data in fusion_groups_json:
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
            fusion_group = FusionGroup(nuclio_endpoint=nuclio_endpoint, tasks=tasks)
            fusion_groups.append(fusion_group)

        return fusion_groups
