from AsyncRAI import ResourceAccessInterface

class AsyncResourceAccessInterface(ResourceAccessInterface):

	def __init__(self, name, manager=None, constructor=None):
		super(AsyncResourceAccessInterface, self).__init__(name=name, manager=manager, constructor=constructor)

