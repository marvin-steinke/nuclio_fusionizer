import threading
import time
from typing import Type, Generator
from loguru import logger

from api_server import ApiServer
from nuclio_fusionizer_server.mapper import Mapper
from strategies import BaseStrategy


class Optimizer(threading.Thread):
    """Optimizes fusion group configurations during runtime of the server.

    A specified strategy is necessary to perform the actual logic.

    Attributes:
        api_server: The api of the fusionize server.
        mapper: The mapper manages the fusion group configurations.
        strategy: The strategy used for the optimization.
        stop_event: Event to signal the strategy thread to stop.

    Methods:
        start: Starts the optimizer.
        stop: Stops the optimizer.
        run: The thread that runs continuously
        optimize: Optimizes the fusion group configurations.
        sleep_durations: Yields numbers to define optimization intervals.
    """
    api_server: ApiServer
    mapper: Mapper
    strategy: BaseStrategy
    stop_event: threading.Event

    def __init__(self, api_server, mapper,
                 strategy_implementation: Type[BaseStrategy]) -> None:
        super().__init__(daemon=True)
        self.api_server = api_server
        self.mapper = mapper
        self.strategy = strategy_implementation(mapper)
        self.stop_event = threading.Event()

    @staticmethod
    def sleep_durations() -> Generator[int, None, None]:
        """Yields numbers to define optimization intervals."""
        yield 5
        for i in range(1, 6):
            yield i
        while True:
            yield 5

    def run(self) -> None:
        """Runs the strategy in a separate thread.

            The optimize function is called at certain intervals.
        """
        sleep_durations = self.sleep_durations()
        time.sleep(next(sleep_durations))

        while not self.stop_event.is_set():
            self.optimize()
            time.sleep(next(sleep_durations))

    def stop(self) -> None:
        """Stops the thread."""
        self.stop_event.set()

    def optimize(self) -> None:
        """Optimizes the fusion group configurations."""
        self.mapper.update(self.strategy.get_new_configuration())
