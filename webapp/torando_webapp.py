'''
Prototyping which framework makes most sense for this application. This may be throw-away code.
'''


import json
import time

import tornado.ioloop
import tornado.web

import asyncio
import asyncpg

import log_event

# import orm

class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE')
        self.set_header('Access-Control-Allow-Credentials', 'True')

    def get(self, url):
        self.set_header("Content-Type", "text/plain")
        self.write("okay")
        print(url)
        print("GET")
        print(self.request.body)

    def post(self, url):
        self.write("okay")
        print(url)
        print("POST")
        client_data = json.loads(self.request.body)
        server_data = {
            'time': time.time(),
            'executable': 'tornado_webapp'
        }
        event = {
            'server': server_data,
            'client': client_data
        }

        log_event.log_event(event)
        print(event)

    def options(self):
        # no body
        print("CORS Request!")
        self.set_status(204)
        self.finish()

def make_app():
    return tornado.web.Application([
        (r"/(.*)", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Starting event loop")
    tornado.ioloop.IOLoop.current().start()
