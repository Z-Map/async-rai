import asyncio

import tests

if __name__ == "__main__":
	for mod in [getattr(tests, k) for k in dir(tests) if not k.startswith("_")]:
		if hasattr(mod, 'sync_test'):
			print(f"================== Starting {mod.__name__} sync test ==================")
			mod.sync_test()
			print(f"=================== End of {mod.__name__} sync test ===================")
		if hasattr(mod, 'sync_test'):
			print(f"================= Starting {mod.__name__} async test ==================")
			asyncio.run(mod.async_test())
			print(f"================== End of {mod.__name__} async test ===================")
