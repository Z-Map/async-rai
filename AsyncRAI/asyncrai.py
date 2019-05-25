from AsyncRAI import ResourceAccessInterface

class AsyncResourceAccessInterface(ResourceAccessInterface):

	def __init__(self, name, resource):
		super(AsyncResourceAccessInterface, self).__init__(name, resource)

