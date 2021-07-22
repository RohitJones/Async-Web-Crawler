from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8080
DIRECTORY = "html"


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):  # type: ignore
        super().__init__(*args, directory=DIRECTORY, **kwargs)


def server() -> None:
    http_server = HTTPServer(("localhost", PORT), RequestHandler)
    http_server.serve_forever()


if __name__ == "__main__":
    server()
