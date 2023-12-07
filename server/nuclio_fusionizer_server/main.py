from nuclio_fusionizer_server.Strategies import StaticStrategy
from nuclio_fusionizer_server.api_server import ApiServer
from nuclio_fusionizer_server.mapper import Mapper
from nuclio_fusionizer_server.optimizer import Optimizer


def main():
    """
    Starts the Nuclio-Fusionizer.

    The server, mapper, and optimizer are instantiated and started.
    """
    api_server = ApiServer()
    api_server.run()

    mapper = Mapper()

    optimizer = Optimizer(api_server, mapper, StaticStrategy)


if __name__ == "__main__":
    main()
