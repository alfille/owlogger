# logger.py
#
# HTTP server program for logging data and serving pages
# Uses putter.py on data upload side
# Stores data in sqlite3
#
# by Paul H Alfille 2025
# MIT License

import sqlite3

# Strategy
# Database
#  Open if exists
#  Else create
# Table format:
#  Time = datatime
#  Data = text

# Wait for put input
# Add to database


from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
import time
import json

hostName = "localhost"
serverPort = 8001


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        body2 = json.loads(body)
        body3 = json.loads(body2)
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        response.write(body)
        self.wfile.write(response.getvalue())
        print(f"request {self.requestline}")
        print(f"path {self.path}")
        print(f"command {self.command}")
        print(f"headers {self.headers}")
        print(f"body {body}")
        print(f"body2 {body2}")
        print(body3['data'])

    def do_PUT(self):
        self.do_POST()


if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
 
