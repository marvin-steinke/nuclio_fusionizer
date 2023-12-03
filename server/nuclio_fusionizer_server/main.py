from server.nuclio_fusionizer_server.api_server import ApiServer


def main():
    api_server = ApiServer()
    api_server.run()

if __name__ == "__main__":
    main()
