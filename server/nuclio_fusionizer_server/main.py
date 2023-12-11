from fastapi import FastAPI

from nuclio_fusionizer_server.strategies import StaticStrategy
from nuclio_fusionizer_server.api_server import ApiServer
from nuclio_fusionizer_server.mapper import Mapper
from nuclio_fusionizer_server.optimizer import Optimizer


def main() -> FastAPI:
    """Starts the Nuclio-Fusionizer.

    The server, mapper, and optimizer are instantiated and started.
    """
    api_server = ApiServer()
    api_server.run()

    mapper = Mapper()

    optimizer = Optimizer(api_server, mapper, StaticStrategy)

    return api_server.app


if __name__ == "__main__":
    main()
