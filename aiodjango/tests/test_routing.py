import asyncio

from unittest.mock import Mock, patch

from django.conf.urls import url
from django.http import HttpResponse
from django.test import override_settings, SimpleTestCase

from aiohttp.web import Response, Application

from .. import routing


@asyncio.coroutine
def example(request):
    return Response(text='Ok')


@override_settings(ROOT_URLCONF='aiodjango.tests.urls')
class GetRoutesTestCase(SimpleTestCase):
    """Discover async routes including in Django URL patterns."""

    def test_use_root_conf(self):
        """If patterns aren't given then they are discovered from the ROOT_URLCONF."""
        router = Application().router
        routes = routing.init_routes(router)
        self.assertEqual(len(routes), 1)

    def test_no_patterns(self):
        """Handle no patterns given."""
        router = Application().router
        routes = routing.init_routes(router, patterns=[])
        self.assertEqual(len(routes), 0)

    def test_no_coroutines(self):
        """Handle no async callbacks given in the patterns."""
        patterns = (
            url(r'^$', lambda x: HttpResponse('Ok'), name='example'),
        )
        router = Application().router
        routes = routing.init_routes(router, patterns=patterns)
        self.assertEqual(len(routes), 0)

    def test_simple_regex(self):
        """Handle regex with no variable matching."""
        patterns = (
            url(r'^/$', example, name='example'),
        )
        router = Application().router
        routes = routing.init_routes(router, patterns=patterns)
        self.assertEqual(len(routes), 1)
        route = routes._routes.pop()
        assert route.resource._match('/') is not None
        self.assertFalse(route.resource._match('/foo/'))


    def test_regex_grouping(self):
        """Handle regex with named variable groups."""
        patterns = (
            url(r'^/foo/(?P<foo>[0-9]+)/$', example, name='example'),
        )

        router = Application().router
        routes = routing.init_routes(router, patterns=patterns)
        self.assertEqual(len(routes), 1)
        route = routes._routes.pop()
        assert route.resource._match('/foo/123/') is not None
        assert route.resource._match('/foo/') is None


    def test_leading_slash(self):
        """aiohttp expects a leading slash so it is automatically added."""
        patterns = (
            url(r'^$', example, name='example-no-slash'),
            url(r'^foo/(?P<foo>[0-9]+)/$', example, name='variable-no-slash'),
        )
        router = Application().router
        routes = routing.init_routes(router, patterns=patterns)
        self.assertEqual(len(routes), 2)
        route = routes._routes[0]
        self.assertIsNotNone(route.resource._match('/'))
        route = routes._routes[1]
        self.assertIsNotNone(route.resource._match('/foo/123/'))


class DjangoDynamicResource(SimpleTestCase):
    """Wrapping aiohttp routing through Django's URL routing."""

    def test_build_simple_url(self):
        """Build URL with no parameters."""
        route = routing.DjangoRegexRoute('GET', Mock(), 'test', r'^$')
        with patch('aiodjango.routing.reverse') as mock_reverse:
            mock_reverse.return_value = '/test/'
            url = route.url()
            self.assertEqual(url, '/test/')
            mock_reverse.assert_called_with('test', kwargs={})

    def test_build_dynamic_url(self):
        """Build URL with dynamic path parameters."""
        route = routing.DjangoRegexRoute('GET', Mock(), 'test', r'^(?P<name>\w+)$')
        with patch('aiodjango.routing.reverse') as mock_reverse:
            mock_reverse.return_value = '/foo/'
            url = route.url(name='foo')
            self.assertEqual(url, '/foo/')
            mock_reverse.assert_called_with('test', kwargs={'name': 'foo'})

    def test_build_with_query(self):
        """Build URL with query arguments."""
        route = routing.DjangoRegexRoute('GET', Mock(), 'test', r'^$')
        with patch('aiodjango.routing.reverse') as mock_reverse:
            mock_reverse.return_value = '/test/'
            url = route.url(query={'foo': 'bar'})
            self.assertEqual(url, '/test/?foo=bar')
            mock_reverse.assert_called_with('test', kwargs={})
