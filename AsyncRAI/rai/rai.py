# -*- coding: utf-8 -*-

from enum import Enum

import inspect
import threading
import queue

from .errors import *
from .result import ResourceResult

class State(Enum):
	STOPPED = 0
	CREATED = 10
	INITIALISING = 15
	INITIALISED = 20
	CONFIGURING = 25
	CONFIGURED = 30
	STARTING = 35
	STARTED = 40
	WAITING = 42
	PROCESSING = 45
	STOPPING = 49

	def __str__(self):
		return self.name

class ResourceAccessInterface(threading.Thread):

	def __init__(self, resource, name=None, max_q=512, context_arg=None):
		if name is None:
			name = resource.__name__ or "Unknown"
		super(ResourceAccessInterface, self).__init__(name=name)
		if not callable(resource):
			raise ResourceTypeError(name, "Resource {} is not callable")
		if context_arg is None:
			try:
				sig = inspect.signature(resource)
			except (ValueError, TypeError):
				context_arg = False
			else:
				if sig.parameters and tuple(sig.parameters.keys())[0] == 'context':
					context_arg = True
				else:
					context_arg = False
		self._alive = False
		self._edit_lock = threading.Lock()
		self._processing_cond = threading.Condition(self._edit_lock)
		self._q_cond = threading.Condition(self._edit_lock)
		self._resource = resource
		self._context_arg = bool(context_arg)
		self._commands = []
		self._max_q = max_q if max_q > 0 else 1
		self._state = State.CREATED

	@property
	def state(self):
		return self._state

	@property
	def max_q(self):
		return self._max_q

	@max_q.setter
	def max_q(self, v):
		if v > 0:
			self._max_q = v
		else:
			self._max_q = 1
		return self._max_q

	def p_lock(self):
		self._edit_lock.acquire()

	def p_unlock(self):
		self._edit_lock.release()

	def p_wait(self):
		self._state = State.WAITING
		self._processing_cond.wait()

	def p_wake_up(self):
		self._processing_cond.notify_all()

	def q_wait(self):
		self._q_cond.wait()

	def q_wake_up(self):
		self._q_cond.notify()

	def q_create(self, args, kwargs):
		return ResourceResult(self, args, kwargs)

	def q_get_place(self):
		while len(self._commands) >= self.max_q:
			self.q_wait()
		return self._alive

	def q_send_command(self, res_ob):
		self._commands.append(res_ob)
		self.p_wake_up()
		return res_ob

	def config_resource(self, context):
		self._state = State.CONFIGURING
		if hasattr(self._resource, "configure"):
			if not self._resource.configure(context):
				raise ResourceConfigError(self.name)
		return True

	def start_resource(self, context):
		self._state = State.STARTING
		if hasattr(self._resource, "start"):
			if not self._resource.start(context):
				raise ResourceStartError(self.name)
		return True

	def process_resource(self, context, res_call):
		self._state = State.PROCESSING
		res_ob, args, kwargs = res_call.get_args()
		ret = True
		try:
			if self._context_arg:
				result = self._resource(context, *args, **kwargs)
			else:
				result = self._resource(*args, **kwargs)
		except Exception as err:
			res_ob.set_exception(err)
			ret = False
		else:
			res_ob.set_result(result)
		return ret

	def stop_resource(self, context):
		self._state = State.STOPPING
		if hasattr(self._resource, "stop"):
			if not self._resource.stop(context):
				raise ResourceStartError(self.name)
		return True

	def run(self):
		self._state = State.INITIALISING
		with self._edit_lock:
			self._alive = True
		context = {}
		self._state = State.INITIALISED
		self.config_resource(context)
		self._state = State.CONFIGURED
		self.start_resource(context)
		self._state = State.STARTED
		self.p_lock()
		while self._alive:
			while self._commands:
				res_call = self._commands.pop(0)
				self.q_wake_up()
				self.p_unlock()
				self.process_resource(context, res_call)
				self.p_lock()
			self.p_wait()
		self.p_unlock()
		self.stop_resource(context)
		self._state = State.STOPPED

	def stop(self):
		with self._edit_lock:
			self._alive = False
			self.p_wake_up()
	
	def call(self, *args, **kwargs):
		res_ob = self.q_create(args, kwargs)
		with self._edit_lock:
			if self.q_get_place():
				return self.q_send_command(res_ob)
			else:
				raise InterfaceClosedError(self.name)

	def __call__(self, *args, **kwargs):
		return self.call(*args, **kwargs)
