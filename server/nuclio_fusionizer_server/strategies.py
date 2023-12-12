import time
import json
from abc import ABC, abstractmethod
from loguru import logger

from nuclio_fusionizer_server.mapper import Task, FusionGroup, Mapper


class BaseStrategy(ABC):
    """Abstract class representing a fusionize strategy.

    Attributes:
        mapper: The mapper manages the fusion group configurations.

    Methods:
        get_new_configuration: Calculates a new fusion group configuration.
    """
    mapper: Mapper

    @abstractmethod
    def __init__(self, mapper: Mapper) -> None:
        self.mapper = mapper

    @abstractmethod
    def get_new_configuration(self, *args) -> list[FusionGroup]:
        """Calculates a new fusion group configuration using this strategy.

        Args: any number of parameters

        Returns:
            List of FusionGroups in new configuration.
        """
        pass


class StaticStrategy(BaseStrategy):
    """Class representing a static fusionize strategy.

    Predetermined fusion group configurations are read from a json file.

    Attributes:
        mapper: The mapper manages the fusion group configurations.
        cnt: The total number of calls to get_new_configuration.

    Methods:
        get_new_configuration: Calculates a new fusion group configuration.
    """
    cnt: int

    def __init__(self, mapper: Mapper) -> None:
        super().__init__(mapper)
        self.cnt = 0

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
            int(self.cnt) % len(fusion_groups_config)]
        self.cnt += 1

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
