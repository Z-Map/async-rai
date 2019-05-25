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
		if self.wait:
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

	def __init__(self, name, resource=None):
		super(ResourceAccessInterface, self).__init__(name=name)
		self._alive = False
		self._edit_lock = threading.Lock()
		self._processing_cond = threading.Condition(self._edit_lock)
		self._resource = resource
		self._id = 0
		self._commands = []
		self._state = State.CREATED

	@property
	def state(self):
		return self._state

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
		self._edit_lock.acquire()
		while self._alive:
			while self._commands:
				res_call = self._commands.pop(0)
				self._edit_lock.release()
				self.process_resource(context, res_call)
				self._edit_lock.acquire()
			self._state = State.WAITING
			self._processing_cond.wait()
		self._edit_lock.release()
		self.stop_resource(context)
		self._state = State.STOPPED

	def stop(self):
		with self._edit_lock:
			self._alive = False

	def call(self, *args, **kwargs):
		res_ob = ResourceResult(self)
		with self._edit_lock:
			if self._alive:
				self._commands.append((res_ob, args, kwargs))
				return res_ob
			else:
				raise InterfaceClosedError(self.name)

	def __call__(self, *args, **kwargs):
		return self.call(*args, **kwargs)
