# -*- coding: utf-8 -*-
import asyncio

from AsyncRAI.rai.errors import *

class ResultInvalidState(asyncio.InvalidStateError, InterfaceResultError):

	def __init__(self, msg, *args, **kwargs):
		asyncio.InvalidStateError.__init__(self)
		InterfaceResultError.__init__(self, msg, *args, **kwargs)

class ResultCancelled(asyncio.CancelledError, InterfaceResultCancelled):

	def __init__(self, msg, *args, **kwargs):
		asyncio.CancelledError.__init__(self)
		InterfaceResultCancelled.__init__(self, msg, *args, **kwargs)
