# -*- coding: utf-8 -*-

from enum import Enum

import inspect
import threading
import queue

from .errors import ResourceTypeError, ResourceError, ResourceConfigError, ResourceStartError, ResourceStopError
from .interface import ThreadedAccessInterface, State

class ResourceAccessInterface(ThreadedAccessInterface):

	def __init__(self, resource, name=None, max_q=512, context_arg=None):
		if name is None:
			name = resource.__name__ or "Unknown"
		super(ResourceAccessInterface, self).__init__(name=name, max_q=512)
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
		self._resource = resource
		self._context_arg = bool(context_arg)

	def config_resource(self, context):
		if hasattr(self._resource, "configure") and callable(self._resource.configure):
			if not self._resource.configure(context):
				raise ResourceConfigError(self.name)
		return True

	def start_resource(self, context):
		if hasattr(self._resource, "start") and callable(self._resource.start):
			if not self._resource.start(context):
				raise ResourceStartError(self.name)
		return True

	def process_resource(self, context, args, kwargs):
		if self._context_arg:
			result = self._resource(context, *args, **kwargs)
		else:
			result = self._resource(*args, **kwargs)
		return result

	def stop_resource(self, context):
		if hasattr(self._resource, "stop") and callable(self._resource.stop):
			if not self._resource.stop(context):
				raise ResourceStopError(self.name)
		return True
