from abc import ABC, abstractmethod
import threading
import time
import json

from server.nuclio_fusionizer_server.mapper import Task, FusionGroup


class BaseStrategy(ABC):
    """Abstract class representing a fusionize strategy."""

    @abstractmethod
    def optimize(self, seconds: int):
        """
        Abstract method for optimizing fusion group configurations based on the strategy.

        Args:
            seconds: Number of seconds/iterations since the thread has started.

        Returns:
            List of FusionGroups in new configuration.
        """
        pass


class StaticStrategy(BaseStrategy):
    """Class representing a concrete fusionize strategy."""

    def optimize(self, seconds: int):
        """
        Optimize fusion group configurations based on a static strategy.

        Args:
            seconds: Number of seconds/iterations since the thread has started.

        Returns:
            List of FusionGroups in new configuration.
        """
        # Read the JSON file
        with open('staticStrategy.json', 'r') as json_file:
            fusion_groups_config = json.load(json_file)

        # Access the fusion groups configurations
        fusion_groups_json = fusion_groups_config[seconds % len(fusion_groups_config)]

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


class Optimizer:
    """The optimizer uses a specified strategy to optimize the FusionGroup setup during runtime."""

    def __init__(self, strategy, api_server, mapper):
        self.strategy = strategy
        self.api_server = api_server
        self.mapper = mapper
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_optimizer, daemon=True)

    def start_optimizer(self):
        """Starts the optimizer thread."""
        self.thread.start()

    def stop_optimizer(self):
        """Stops the optimizer thread."""
        self.stop_event.set()

    def _run_optimizer(self):
        """Runs the optimizer in a separate thread."""
        iterations = 0
        while not self.stop_event.is_set():
            self.optimize(iterations)
            iterations += 1
            time.sleep(1)

    def optimize(self, seconds: int):
        """
        Optimizes fusion group configurations using the provided strategy and updates the mapper.

        Args:
            seconds: Number of seconds/iterations since the thread has started.
        """
        self.mapper.update(self.strategy.optimize(seconds))
