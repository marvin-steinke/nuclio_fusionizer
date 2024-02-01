import argparse
from loguru import logger

from nuclio_fusionizer import Nuctl, Fuser, Mapper, ApiServer, StaticOptimizer


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--address",
        help=(
            "Private address of the Nuclio Fusionizer server, available to "
            "deployed Tasks as HTTP header 'Fusionizer-Server-Address' to "
            "invoke other Tasks"
        ),
        type=str,
        required=True,
    )
    parser.add_argument(
        "-p",
        "--platform",
        help="The Nuclio platform to use, can be 'local', 'kube' or 'auto'. "
        "Default is 'auto'",
        type=str,
        default="auto",
    )
    parser.add_argument(
        "-r",
        "--registry",
        help="The Docker registry to use for function deployments. Defaults to "
        "'localhost:5000' if the platform is 'kube'",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-n", "--namespace", help="Nuclio namespace", type=str, default="nuclio"
    )
    parser.add_argument(
        "-k",
        "--kubeconfig",
        help="Path to a Kubernetes configuration file (admin.conf)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to a static optimizers configuration file",
        type=str,
        default="config.json",
    )
    return parser


def main():
    logger.add("logs.txt")
    args = create_parser().parse_args()
    nuctl = Nuctl(
        args.address,
        namespace=args.namespace,
        registry=args.registry,
        kubeconfig=args.kubeconfig,
        platform=args.platform,
    )
    fuser = Fuser()
    mapper = Mapper(nuctl, fuser)
    api_server = ApiServer(nuctl, mapper)
    optimizer = StaticOptimizer(mapper, args.config)
    optimizer.start()
    api_server.run()


if __name__ == "__main__":
    main()
