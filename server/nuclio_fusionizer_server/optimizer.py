from loguru import logger
from abc import ABC, abstractmethod
import threading
import bisect
import json
import time

from nuclio_fusionizer_server import Mapper, FusionGroup


class Optimizer(ABC, threading.Thread):
    """An abstract threading class to optimize a Fusion Setup.

    This class is to be further specified in child classes inheriting from it.
    Optimizes the setup and updates the mapper accordingly in a loop until
    stopped.

    Args:
        mapper: Mapper object that handles the management of Fusion Groups.
    """

    def __init__(self, mapper: Mapper) -> None:
        super().__init__()
        self.mapper = mapper
        self.stop_event = threading.Event()

    def run(self) -> None:
        """The main loop of the thread.

        Continuously operates the optimization process until the stop event is
        set. Each iteration includes a sleep time, optimization and mapper
        update.
        """
        while not self.stop_event.is_set():
            self._sleep()
            new_setup = self._optimize()
            self.mapper.update(new_setup)

    def stop(self) -> None:
        """Sets the stop event to terminate the thread."""
        self.stop_event.set()

    @abstractmethod
    def _sleep(self) -> None:
        """Determines the sleep time until the next optimizing iteration."""
        pass

    @abstractmethod
    def _optimize(self) -> list[FusionGroup] | list[list[str]]:
        """Generates a new Fusion Setup.

        Returns:
            List of Fusion Groups in new configuration.
        """
        pass


class StaticOptimizer(Optimizer):
    """Class representing a static Fusionize strategy.

    Predetermined Fusion Group configurations are read from a JSON file.

    Args:
        mapper: Mapper object that handles the management of Fusion Groups.
        config_file: JSON file of the form:
            {<time after start up in seconds>: <list of list of task names},
            e.g.: {
                60: [["Task1", "Task2"], ["Task3", "Task4"]],
                120: [["Task1", "Task3"], ["Task2", "Task4"]]
            }
    """

    def __init__(self, mapper: Mapper, config_file: str) -> None:
        super().__init__(mapper)
        # Read and parse JSON file
        self.config: dict[int, list[list[str]]] = {}
        self.time_stamp = None
        try:
            with open(config_file, "r") as file:
                self.config = json.load(file)
                self.config = {int(k): v for k, v in self.config.items()}
        except Exception as e:
            logger.exception(e)
            logger.error(f"Failed to load Fusion Setups from file '{config_file}'")

    def _sleep(self) -> None:
        """Pauses the execution for a time duration defined by a timestamp.

        This method calculates the time to pause execution (sleep) based on the
        timestamps in the configuration. On the first run, it will sleep for the
        minimum time stamp value. In subsequent iterations, it sleeps for the
        time difference between the next greater timestamp and the current one.
        If no greater timestamp exists, the method stops the thread.
        """
        # Take the min time stamp for first iter
        if self.time_stamp is None:
            min_key = min(self.config.keys())
            self.time_stamp = min_key
            time.sleep(min_key)
            return

        # Get the next bigger time stamp
        time_stamps = sorted(self.config.keys())
        index = bisect.bisect_right(time_stamps, self.time_stamp)
        # No bigger time stamp exists -> stop thread
        if index == len(time_stamps):
            self.time_stamp = None
            self.stop()
            return
        next_time_stamp = time_stamps[index]

        # Determine sleep duration by substracting from current time stamp
        sleep_dur = next_time_stamp - self.time_stamp
        self.time_stamp = next_time_stamp
        time.sleep(sleep_dur)

    def _optimize(self) -> list[list[str]]:
        """Loads Fusion Setup from JSON file depending on time passed.

        Returns:
            List of FusionGroups in new configuration.
        """
        if self.time_stamp is None:
            return []
        return self.config[self.time_stamp]
