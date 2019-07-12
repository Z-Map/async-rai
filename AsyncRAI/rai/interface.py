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
		super(AccessInterface, self).__init__()
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
		return True

	def _stop_interface(self, context):
		self._state = State.STOPPING
		return True

	def r_lock(self, timeout=None):
		return NotImplemented

	def r_unlock(self):
		return NotImplemented

	def r_wait(self, timeout=None):
		if not self._alive:
			return False
		return NotImplemented

	def r_wake_up(self):
		return NotImplemented

	def r_receive_command(self, timeout=None):
		if not self.r_lock(timeout=timeout):
			raise InterfaceTimeoutError(self.name)
		if self._commands or (self.q_wait(timeout=timeout) and self._commands):
			q = self._commands.pop(0)
			self.r_wake_up()
		else:
			q = None
		self.r_unlock()
		return q

	def r_process(self, context, q) -> bool:
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
		if self.q_lock(timeout=timeout):
			if self.q_get_place(timeout=timeout):
				future = self.q_send_command(future)
			else:
				self.q_unlock()
				if self._alive:
					raise InterfaceTimeoutError(self.name)
				else:
					raise InterfaceClosedError(self.name)
			self.q_unlock()
		else:
			raise InterfaceTimeoutError(self.name)
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
			self.r_done(context, q, r)
		self.stop_resource(context)
		self._state = State.STOPPED

	def call(self, *args, **kwargs):
		raise NotImplementedError(AccessInterface.NOT_IMPLEMENTED_TEXT)

	def __call__(self, *args, **kwargs):
		return self.call(*args, **kwargs)

class ThreadedAccessInterface(threading.Thread, AccessInterface):

	def __init__(self, name, max_q=512):
		threading.Thread.__init__(self, name=name)
		AccessInterface.__init__(self, name, max_q=max_q)
		self._edit_lock = threading.Lock()
		self._processing_cond = threading.Condition(self._edit_lock)
		self._q_cond = threading.Condition(self._edit_lock)

	def r_lock(self, timeout=None):
		if not self._edit_lock.locked():
			if timeout is None:
				timeout = -1
			return self._edit_lock.acquire(timeout=timeout)
		return True

	def r_unlock(self):
		if self._edit_lock.locked():
			self._edit_lock.release()

	def r_wait(self, timeout = None):
		self._state = State.WAITING
		return self._processing_cond.wait(timeout=timeout)

	def r_wake_up(self):
		self._processing_cond.notify_all()

	def q_lock(self, timeout=None):
		if not self._edit_lock.locked():
			if timeout is None:
				timeout = -1
			return self._edit_lock.acquire(timeout=timeout)
		return True

	def q_unlock(self):
		if self._edit_lock.locked():
			self._edit_lock.release()

	def q_wait(self, timeout = None):
		return self._q_cond.wait(timeout=timeout)

	def q_wake_up(self):
		self._q_cond.notify()

	def config_resource(self, context):
		return NotImplemented

	def start_resource(self, context):
		return NotImplemented

	def process_resource(self, context, args, kwargs):
		return NotImplemented

	def stop_resource(self, context):
		return NotImplemented


	def _config_interface(self, context):
		if super()._config_interface(context):
			return self.config_resource()
		return False

	def _start_interface(self, context):
		if super()._start_interface(context):
			return self.start_resource()
		return False

	def _process_interface(self, context, *args, **kwargs):
		if super()._process_interface(context, *args, **kwargs):
			ret = self.process_resource(context, args, kwargs)
			if ret is NotImplemented:
				raise NotImplementedError(AccessInterface.NOT_IMPLEMENTED_TEXT)
			else:
				return ret
		return False

	def _stop_interface(self, context):
		if super()._stop_interface(context):
			return self.stop_resource()
		return False

	def run(self):
		self._state = State.INITIALISING
		with self._edit_lock:
			self._alive = True
		self.process()

	def stop_request(self):
		with self._edit_lock:
			self._alive = False
			self.q_wake_up()

	def stop(self, timeout=None):
		self.stop_request()
		self.join(timeout)
		return not(self.is_alive())

	def call(self, *args, **kwargs):
		return self.q_process(args, kwargs)