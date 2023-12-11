from typing import Type
from loguru import logger

from api_server import ApiServer
from nuclio_fusionizer_server.strategies import BaseStrategy
from nuclio_fusionizer_server.mapper import FusionGroup, Mapper


class Optimizer:
    """Optimizes fusion group configurations during runtime of the server.

    A specified strategy is necessary to perform the actual logic.

    Attributes:
        api_server: The api of the fusionize server.
        mapper: The mapper manages the fusion group configurations.
        strategy: The strategy used for the optimization.

    Methods:
        optimize: Optimizes the fusion group configurations.
    """
    api_server: ApiServer
    mapper: Mapper
    strategy: BaseStrategy

    def __init__(self, api_server, mapper,
                 strategy_implementation: Type[BaseStrategy]) -> None:
        self.api_server = api_server
        self.mapper = mapper
        self.strategy = strategy_implementation(self, mapper)

    def optimize(self, new_setup: list[FusionGroup] = None) -> None:
        """Optimizes the fusion group configurations.

        Uses the strategy of the instance to acquire a new setup if none is specified.

        Args:
            new_setup: A list of FusionGroups to replace the old setup.
        """
        if not new_setup:
            new_setup = self.strategy.get_new_configuration()
        self.mapper.update(new_setup)
