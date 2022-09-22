'''
Example serving the Dash app through aiohttp server
'''
from aiohttp import web
from aiohttp_wsgi import WSGIHandler
from app import app

wsgi_handler = WSGIHandler(app.server)
webapp = web.Application()
webapp.router.add_route("*", "/{path_info:.*}", wsgi_handler)
web.run_app(webapp)
