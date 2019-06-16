import asyncio

from .errors import *
from .result import AsyncResourceResult
from AsyncRAI.rai import ResourceAccessInterface

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
				self.p_unlock()
				self._loops[loop][0].clear()
				await self._loops[loop][0].wait()
				self.p_lock()
			self._loops[loop][1] -= 1
			if self._loops[loop][1] <= 0:
				del self._loops[loop]
		return self._alive

	async def async_call(self, *args, **kwargs):
		res_ob = await self.async_q_create(args, kwargs)
		with self._edit_lock:
			if await self.async_q_get_place():
				return self.q_send_command(res_ob).future
			else:
				raise InterfaceClosedError(self.name)

	async def __call__(self, *args, **kwargs):
		fut = await self.async_call(*args, **kwargs)
		return await fut