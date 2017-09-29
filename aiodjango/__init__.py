"""
Utilities for running async aiohttp based routes in the context of a Django project.
"""

__version__ = '0.2.0+mp1'

from .api import get_aio_application  # noqa
