# -*- coding: utf-8 -*-

class InterfaceError(Exception):
	def __init__(self, msg, *args, **kwars):
		if args or kwars:
			msg = msg.format(*args, **kwars)
		self.msg = msg

	def __str__(self):
		return (str(self.msg))

class InterfaceClosedError(InterfaceError):

	def __init__(self, name = "unknown resource"):
		super(InterfaceClosedError, self).__init__("Interface for {} is closed", name)

class InterfaceTimeoutError(TimeoutError, InterfaceError):
	
	def __init__(self, name = "unknown resource", msg = "Timeout during operation on {} interface"):
		TimeoutError.__init__(self)
		InterfaceError.__init__(msg, name)


class ResourceError(Exception):
	def __init__(self, msg, *args, **kwars):
		if args or kwars:
			msg = msg.format(*args, **kwars)
		self.msg = msg

	def __str__(self):
		return (str(self.msg))

class ResourceConfigError(ResourceError):

	def __init__(self, name = "Unknown resource"):
		super(ResourceConfigError, self).__init__("configuration error for {}", name)

class ResourceStartError(ResourceError):

	def __init__(self, name = "Unknown resource"):
		super(ResourceStartError, self).__init__("{} failed to start", name)

class ResourceStopError(ResourceError):

	def __init__(self, name = "Unknown resource"):
		super(ResourceStopError, self).__init__("{} failed to stop", name)