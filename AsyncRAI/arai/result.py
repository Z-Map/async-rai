# -*- coding: utf-8 -*-

import asyncio

from .errors import *
from AsyncRAI.rai.result import ResourceResult, State

class AsyncResourceResult(ResourceResult):

	def __init__(self, interface, args, kwargs):
		self._loop = asyncio.get_running_loop()
		self._fut = self._loop.create_future()
		self.interface = interface
		self._args: tuple= args or ()
		self._kwargs: dict= kwargs or {}
		self._state: State= 0
		self._result = None
		self._exception = None

	def _state_raise(self):
		msg = ResourceResult.RESULT_MESSAGES[self._state]
		if self._state == State.CANCELLED:
			ResultCancelled(msg)
		elif self._state:
			ResultInvalidState(msg)

	def _set_future(self):
		if self._state == State.RESULT:
			self._fut.set_result(self._result)
		elif self._state == State.EXCEPTION:
			self._fut.set_exception(self._exception)
		elif self._state == State.CANCELLED:
			self._fut.cancel()
		else:
			raise InterfaceResultError("This error should never be raised ! the internal state of the result is compromised")

	def _set_state(self, state):
		self._state = state
		self._loop.call_soon_threadsafe(self._set_future)

	def get_args(self):
		return (self, self._args, self._kwargs)

	async def wait(self):
		try:
			await self._fut
		except asyncio.CancelledError:
			return False
		return True

	async def get(self):
		return await self._fut

	@property
	def future(self):
		return self._fut