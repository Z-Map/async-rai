# -*- coding: utf-8 -*-
""" Error module
"""

class InterfaceError(Exception):
	def __init__(self, msg, *args, **kwargs):
		super(InterfaceError, self).__init__()
		if args or kwargs:
			msg = msg.format(*args, **kwargs)
		self.msg = msg

	def __str__(self):
		return str(self.msg)


class InterfaceClosedError(InterfaceError):

	def __init__(self, name="unknown resource"):
		super(InterfaceClosedError, self).__init__("Interface for {} is closed", name)


class InterfaceTimeoutError(TimeoutError, InterfaceError):

	def __init__(self, name="unknown resource", msg="Timeout during operation on {} interface"):
		TimeoutError.__init__(self)
		InterfaceError.__init__(msg, name)


class InterfaceResultError(InterfaceError):
	pass

class InterfaceResultCancelled(InterfaceResultError):
	pass

class ResourceError(Exception):

	def __init__(self, msg, *args, **kwargs):
		super(ResourceError, self).__init__()
		if args or kwargs:
			msg = msg.format(*args, **kwargs)
		self.msg = msg

	def __str__(self):
		return str(self.msg)


class ResourceTypeError(TypeError, ResourceError):

	def __init__(self, name="Unknown resource", msg="{} has a wrong type"):
		TypeError.__init__(self)
		ResourceError.__init__(self, msg, name)


class ResourceConfigError(ResourceError):

	def __init__(self, name="Unknown resource"):
		super(ResourceConfigError, self).__init__("Configuration error for {}", name)


class ResourceStartError(ResourceError):

	def __init__(self, name="Unknown resource"):
		super(ResourceStartError, self).__init__("{} failed to start", name)


class ResourceProcessingError(ResourceError):

	def __init__(self, name="Unknown resource"):
		super(ResourceProcessingError, self).__init__("{} failed to process", name)


class ResourceStopError(ResourceError):

	def __init__(self, name="Unknown resource"):
		super(ResourceStopError, self).__init__("{} failed to stop", name)
