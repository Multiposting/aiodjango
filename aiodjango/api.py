from django.conf import settings
from django.core.wsgi import get_wsgi_application

from aiohttp import web
from aiohttp_wsgi import WSGIHandler

from .routing import init_routes


def get_aio_application(wsgi=None, include_static=False):
    """Builds a aiohttp application wrapping around a Django WSGI server."""

    handler = WSGIHandler(wsgi or get_wsgi_application())
    app = web.Application()
    init_routes(app.router)

    app.router.add_route("*", "/{path_info:.*}", handler.handle_request, name='wsgi-app')
    return app
