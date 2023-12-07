from server.nuclio_fusionizer_server.api_server import ApiServer
from server.nuclio_fusionizer_server.mapper import Mapper
from server.nuclio_fusionizer_server.optimizer import Optimizer, StaticStrategy


def main():
    api_server = ApiServer()
    api_server.run()

    mapper = Mapper()

    optimizer = Optimizer(StaticStrategy(), api_server, mapper)
    optimizer.start_optimizer()


if __name__ == "__main__":
    main()
