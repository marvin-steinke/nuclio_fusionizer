import argparse

from nuclio_fusionizer import Nuctl, Fuser, Mapper, ApiServer, StaticOptimizer


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--address",
        help="Public or private address of the Nuclio Fusionizer server",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-n", "--namespace", help="Nuclio namespace", type=str, default=None
    )
    parser.add_argument(
        "-k",
        "--kubeconfig",
        help="Path to a Kubernetes configuration file (admin.conf)",
        type=str,
        default=None,
    )
    return parser


def main():
    args = create_parser().parse_args()
    nuctl = Nuctl(args.address, namespace=args.namespace, kubeconfig=args.kubeconfig)
    fuser = Fuser()
    mapper = Mapper(nuctl, fuser)
    api_server = ApiServer(nuctl, mapper)
    optimizer = StaticOptimizer(mapper, "config.json")
    optimizer.start()
    api_server.run()


if __name__ == "__main__":
    main()
