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

class AccessInterface(object):

	NOT_IMPLEMENTED_TEXT = "This interface is abstract and should not be used directly"

	def __init__(self, name, max_q=512):
		super(AccessInterface, self).__init__(name=name)
		self._alive = False
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

	def _config_interface(self, context):
		self._state = State.CONFIGURING
		return True

	def _start_interface(self, context):
		self._state = State.STARTING
		return True

	def _process_interface(self, context, *args, **kwargs):
		self._state = State.PROCESSING
		raise NotImplementedError(AccessInterface.NOT_IMPLEMENTED_TEXT)

	def _stop_interface(self, context):
		self._state = State.STOPPING
		return True

	def r_lock(self, timeout=None):
		return NotImplemented

	def r_unlock(self):
		return NotImplemented

	def r_wait(self, timeout=None):
		return NotImplemented

	def r_wake_up(self):
		return NotImplemented

	def r_receive_command(self, timeout=None):
		self.r_lock(timeout=timeout)
		if self._commands or self.q_wait(timeout=timeout):
			q = self._commands.pop(0)
			self.r_wake_up()
		else:
			q = None
		self.r_unlock()
		return q

	def r_process(self, context, q):
		if q is None:
			return False
		future, args, kwargs = q.get_args()
		if not future.cancelled():
			try:
				result = self._process_interface(context, *args, **kwargs)
			except Exception as err:
				future.set_exception(err)
			else:
				future.set_result(result)
				return True
		return False

	def r_done(self, context, q, r):
		return NotImplemented

	def q_lock(self, timeout=None):
		return NotImplemented

	def q_unlock(self):
		return NotImplemented

	def q_wait(self, timeout=None):
		self._state = State.WAITING
		if not self._alive:
			return self._commands
		return NotImplemented

	def q_wake_up(self):
		return NotImplemented

	def q_create(self, args, kwargs):
		return ResourceResult(self, args, kwargs)

	def q_get_place(self, timeout=None):
		while len(self._commands) >= self.max_q:
			self.r_wait(timeout=timeout)
		return self._alive

	def q_send_command(self, future):
		self._commands.append(future)
		self.q_wake_up()
		return future

	def q_process(self, args, kwargs, timeout=None):
		future = self.q_create(args, kwargs)
		self.q_lock(timeout=timeout)
		if self.q_get_place(timeout=timeout):
			future = self.q_send_command(future)
		else:
			self.q_unlock()
			if self._alive:
				raise InterfaceTimeoutError(self.name)
			else:
				raise InterfaceClosedError(self.name)
		self.q_unlock()
		return future

	def process(self, timeout=None):
		context = {}
		self._state = State.INITIALISED
		self.config_resource(context)
		self._state = State.CONFIGURED
		self.start_resource(context)
		self._state = State.STARTED
		while self._alive:
			q = self.r_receive_command(timeout=timeout)
			r = self.r_process(context, q)
			self.r_done(q, r)
		self.stop_resource(context)
		self._state = State.STOPPED

	def call(self, *args, **kwargs):
		return self.q_process(args, kwargs)

	def __call__(self, *args, **kwargs):
		return self.call(*args, **kwargs)

class ThreadedAccessInterface(threading.Thread):

	def __init__(self, name, max_q=512):
		super(ThreadedAccessInterface, self).__init__(name=name)
		self._edit_lock = threading.Lock()
		self._processing_cond = threading.Condition(self._edit_lock)
		self._q_cond = threading.Condition(self._edit_lock)
		self._resource = resource
		self._context_arg = bool(context_arg)

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
		if res_ob.cancelled():
			return False
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

	def stop_request(self):
		with self._edit_lock:
			self._alive = False
			self.p_wake_up()

	def stop(self, timeout=None):
		self.stop_request()
		self.join(timeout)
		return not(self.is_alive())
	
	def call(self, *args, **kwargs):
		res_ob = self.q_create(args, kwargs)
		with self._edit_lock:
			if self.q_get_place():
				return self.q_send_command(res_ob)
			else:
				raise InterfaceClosedError(self.name)

	def __call__(self, *args, **kwargs):
		return self.call(*args, **kwargs)
