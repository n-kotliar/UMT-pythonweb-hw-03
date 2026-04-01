import json
import mimetypes
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE = BASE_DIR / "storage" / "data.json"

env = Environment(loader=FileSystemLoader(str(BASE_DIR / "templates")))


def load_data():
    if STORAGE.exists():
        with open(STORAGE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_message(username: str, message: str):
    data = load_data()
    key = str(datetime.now())
    data[key] = {"username": username, "message": message}
    STORAGE.parent.mkdir(exist_ok=True)
    with open(STORAGE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/":
            self.send_html_file("index.html")

        elif pr_url.path == "/message" or pr_url.path == "/message.html":
            self.send_html_file("message.html")

        elif pr_url.path == "/read":
            self.send_read_page()  

        elif Path(BASE_DIR / pr_url.path[1:]).exists():
            self.send_static() 

        else:
            self.send_html_file("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value
            for key, value in [el.split("=") for el in data_parse.split("&")]
        }
        save_message(data_dict.get("username", ""), data_dict.get("message", ""))

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(BASE_DIR / "templates" / filename, "rb") as f:
            self.wfile.write(f.read())

    def send_read_page(self):
        template = env.get_template("read.html")
        messages = load_data()
        output = template.render(messages=messages) 

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(output.encode("utf-8"))

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(BASE_DIR / self.path[1:], "rb") as f:
            self.wfile.write(f.read())

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()