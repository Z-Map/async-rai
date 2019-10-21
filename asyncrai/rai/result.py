# -*- coding: utf-8 -*-
""" Result module
"""

from enum import Enum, auto
import threading

from .errors import InterfaceResultCancelled,\
	InterfaceResultError, InterfaceTimeoutError

class State(Enum):
	UNSET = 0
	CANCELLED = 1
	EXCEPTION = -1
	RESULT = auto()

	def __str__(self):
		return self.name

class ResourceResult():

	RESULT_MESSAGES = ("Result is not done yet",
					   "Result is cancelled",
					   "Result is already set")

	def __init__(self, interface, args, kwargs):
		self.interface = interface
		self.evt = threading.Event()
		self._args: tuple = args or ()
		self._kwargs: dict = kwargs or {}
		self._state: State = 0
		self._result = None
		self._exception = None

	def _state_raise(self):
		msg = ResourceResult.RESULT_MESSAGES[self._state]
		if self._state == State.CANCELLED:
			raise InterfaceResultCancelled(msg)
		elif self._state:
			raise InterfaceResultError(msg)
		else:
			return None

	def _set_state(self, state):
		self._state = state
		self.evt.set()

	def get_args(self):
		return (self, self._args, self._kwargs)

	def wait(self, timeout: float =None):
		if not self.evt.wait(timeout=timeout):
			return False
		return True

	def get(self, timeout: float =None):
		if self.wait(timeout=timeout):
			if self._state == State.RESULT:
				return self._result
			elif self._state == State.EXCEPTION:
				raise self._exception
			elif self._state == State.CANCELLED:
				return self._state_raise()
			else:
				raise InterfaceResultError(
					"This error should never be raised !"
					" the internal state of the result is compromised")
		else:
			raise InterfaceTimeoutError()

	def result(self):
		if self._state == State.RESULT:
			return self._result
		elif self._state == State.EXCEPTION:
			raise self._exception
		else:
			return self._state_raise()

	def exception(self):
		if self.available:
			return self._exception
		else:
			return self._state_raise()

	def set_result(self, result):
		if self._state:
			self._state_raise()
		self._result = result
		self._set_state(State.RESULT)

	def set_exception(self, exception):
		if self._state:
			self._state_raise()
		self._exception = exception
		self._set_state(State.EXCEPTION)

	def cancel(self):
		if self._state:
			return False
		else:
			self._set_state(State.CANCELLED)
			return True

	def cancelled(self):
		return self._state == State.CANCELLED

	def done(self):
		return bool(self._state)

	@property
	def available(self):
		return self._state not in (State.CANCELLED, State.UNSET)

	@property
	def args(self):
		return self._args

	@property
	def kwargs(self):
		return self._kwargs
