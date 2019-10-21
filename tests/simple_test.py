import asyncio
import asyncrai
import pytest

def addition(a, b):
	return a + b

class TestClass:

	int_lst_a = [5, 96, 856, 5, 12, 34, -45]
	int_lst_b = [8, -71, -68, 1, 777, -36, 78]

	def test_add(self):
		rai = asyncrai.ResourceAccessInterface(addition, "Adder")
		rai.start()
		good_results = []
		rai_results = []
		for a,b in zip(self.int_lst_a, self.int_lst_b):
			good_results.append(a + b)
			rai_results.append(rai(a, b))
		rai_results = [res.get() for res in rai_results]
		rai.stop()
		assert good_results == rai_results

	async def get_results(self, args_lst: list):
		arai = asyncrai.AsyncInterface(addition, "Tester")
		arai.start()
		results = []
		for args in args_lst:
			results.append(await arai.async_call(*args))
		results = [ await r for r in results ]
		arai.stop()
		return results

	def test_async_add(self):
		good_results = []
		args_lst = []
		for a,b in zip(self.int_lst_a, self.int_lst_b):
			good_results.append(a + b)
			args_lst.append((a,b))
		arai_results = asyncio.run(self.get_results(args_lst))
		assert good_results == arai_results