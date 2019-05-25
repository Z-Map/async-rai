# -*- coding: utf-8 -*-

from enum import Enum

import threading
import queue
import uuid

from AsyncRAI.errors import *

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

class ResourceResult(object):

	def __init__(self, interface):
		self.interface = interface
		self.evt = threading.Event()

	def wait(self, timeout=None):
		if not self.evt.wait(timeout=timeout):
			return False
		return True

	def get(self, timeout=None):
		if self.wait():
			if isinstance(self.result, BaseException):
				raise ResourceProcessingError(self.interface.name) from self.result
			return self.result
		else:
			raise InterfaceTimeoutError()

	def set(self, result):
		self.result = result
		self.evt.set()

	@property
	def available(self):
		return self.evt.is_set()

	

class ResourceAccessInterface(threading.Thread):

	def __init__(self, name, resource, max_q=512):
		super(ResourceAccessInterface, self).__init__(name=name)
		self._alive = False
		self._edit_lock = threading.Lock()
		self._processing_cond = threading.Condition(self._edit_lock)
		self._q_cond = threading.Condition(self._edit_lock)
		self._resource = resource
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
		res_ob, args, kwargs = res_call
		ret = True
		try:
			result = self._resource(*args, **kwargs)
		except Exception as err:
			result = err
			ret = False
		res_ob.set(result)
		return ret

	def stop_resource(self, context):
		self._state = State.STOPPING
		if hasattr(self._resource, "stop"):
			if not self._resource.stop(context):
				raise ResourceStartError(self.name)
		return True

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

		res_ob = ResourceResult(self)
		with self._edit_lock:
			while len(self._commands) >= self.max_q:
				self.q_wait()
			if self._alive:
				self._commands.append((res_ob, args, kwargs))
				self.p_wake_up()
				return res_ob
			else:
				raise InterfaceClosedError(self.name)

	def __call__(self, *args, **kwargs):
		return self.call(*args, **kwargs)
