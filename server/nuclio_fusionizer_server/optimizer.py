from typing import Type
from loguru import logger

from nuclio_fusionizer_server.Strategies import BaseStrategy
from nuclio_fusionizer_server.mapper import FusionGroup


class Optimizer:
    """
    Optimizes fusion group configurations during runtime of the server.
    A specified strategy is necessary to perform the actual logic.

    Attributes:
        api_server: The api of the fusionize server.
        mapper: The mapper manages the fusion group configurations.
        strategy: The strategy used for the optimization.
    """

    def __init__(self, api_server, mapper, strategy_implementation: Type[BaseStrategy]):
        self.api_server = api_server
        self.mapper = mapper
        self.strategy = strategy_implementation(self)

    def optimize(self, new_setup: list[FusionGroup] = None):
        """
        Optimizes fusion group configurations.

        Uses the strategy to acquire a new setup, if none is specified.
        """
        if not new_setup:
            new_setup = self.strategy.optimize()
        self.mapper.update(new_setup)
