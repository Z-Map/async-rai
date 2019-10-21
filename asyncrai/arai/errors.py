# -*- coding: utf-8 -*-
""" Async specific error module
"""

import asyncio

from asyncrai.rai.errors import *

class ResultInvalidState(asyncio.InvalidStateError, InterfaceResultError):
	""" Result is in an invalid state
	"""

	def __init__(self, msg, *args, **kwargs):
		asyncio.InvalidStateError.__init__(self)
		InterfaceResultError.__init__(self, msg, *args, **kwargs)

class ResultCancelled(asyncio.CancelledError, InterfaceResultCancelled):
	""" Result has been cancelled
	"""

	def __init__(self, msg, *args, **kwargs):
		asyncio.CancelledError.__init__(self)
		InterfaceResultCancelled.__init__(self, msg, *args, **kwargs)
