from AsyncRAI import ResourceAccessInterface

class AsyncResourceAccessInterface(ResourceAccessInterface):

	def __init__(self, name, resource, max_q=512):
		super(AsyncResourceAccessInterface, self).__init__(name, resource)
		
