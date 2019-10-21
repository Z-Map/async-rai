# -*- coding: utf-8 -*-
"""Async Resource Access Interface
A very lightweight interface to manage and use resource asynchronously.
"""

__version__ = "0.2.0"

from .arai import errors
from .rai import ResourceAccessInterface
from .arai.arai import AsyncResourceAccessInterface as AsyncInterface
