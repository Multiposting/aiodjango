import asyncio
import inspect
import re

from importlib import import_module
from yarl import URL

from django.conf import settings
from django.contrib.admindocs.views import extract_views_from_urlpatterns
from django.core.urlresolvers import reverse

from aiohttp.web import DynamicResource

PATH_SEP = re.escape('/')

class DjangoDynamicResource(DynamicResource):

    def __init__(self, regex, *, name=None):
        if not regex.lstrip('^').startswith(PATH_SEP):
            regex = PATH_SEP + regex.lstrip('^').lstrip('/')
        pattern = re.compile(regex)
        super().__init__(pattern, '/', name=name)

    def url_for(self, **kwargs):
        url = reverse(self.name, kwargs=kwargs)
        return URL(url)

def init_routes(app_router, patterns=None):
    """Walk the URL patterns to find any coroutine views."""
    if patterns is None:
        urlconf = import_module(settings.ROOT_URLCONF)
        patterns = urlconf.urlpatterns
    view_functions = extract_views_from_urlpatterns(patterns)
    for (func, regex, namespace, name) in view_functions:
        if asyncio.iscoroutinefunction(func) or inspect.isgeneratorfunction(func):
            resource = DjangoDynamicResource(regex, name=name)
            app_router.register_resource(resource)
            resource.add_route('*', func)
    return app_router.routes()
