# -*- coding: utf-8 -*-
""" Async RAI module
"""
import asyncio

from .errors import InterfaceClosedError
from .result import AsyncResourceResult
from asyncrai.rai import ResourceAccessInterface

class AsyncResourceAccessInterface(ResourceAccessInterface):

	def __init__(self, resource, name=None, max_q=512, context_arg=None):
		super().__init__(resource, name=name, max_q=max_q, context_arg=context_arg)
		self._loops = {}

	def async_l_wake_up(self):
		loop = asyncio.get_running_loop()
		self._loops[loop][0].set()

	def q_wake_up(self):
		self._q_cond.notify()
		for loop in self._loops.keys():
			loop.call_soon_threadsafe(self.async_l_wake_up)

	async def async_q_create(self, args, kwargs):
		return AsyncResourceResult(self, args, kwargs)

	async def async_q_get_place(self):
		if len(self._commands) >= self.max_q:
			loop = asyncio.get_running_loop()
			if loop not in self._loops:
				self._loops[loop] = [asyncio.Event(), 1]
			else:
				self._loops[loop][1] += 1
			while len(self._commands) >= self.max_q:
				self.q_unlock()
				self._loops[loop][0].clear()
				await self._loops[loop][0].wait()
				self.q_lock()
			self._loops[loop][1] -= 1
			if self._loops[loop][1] <= 0:
				del self._loops[loop]
		return self._alive

	async def async_call(self, *args, **kwargs):
		res_ob = await self.async_q_create(args, kwargs)
		self.q_lock()
		if await self.async_q_get_place():
			res_ob = self.q_send_command(res_ob).future
		else:
			self.q_unlock()
			raise InterfaceClosedError(self.name)
		self.q_unlock()
		return res_ob

	async def __call__(self, *args, **kwargs):
		fut = await self.async_call(*args, **kwargs)
		return await fut
