import asyncio
import asyncrai

def displayer(context, *args, **kwargs):
	print("Args : {}".format(", ".join([str(a) for a in args])))
	print("Kwargs : {}".format(", ".join(["{} = {}".format(k,v) for k,v in kwargs.items()])))
	return "Displayed {} args and {} kwargs".format(len(args), len(kwargs))

def sync_test():
	rai = asyncrai.ResourceAccessInterface(displayer, "Displayer")
	rai.start()
	r = rai("hello")
	print(r.get())
	r = rai("hello two", test=42)
	print(r.get())
	r = []
	for i in range(50):
		r.append(rai("Req n°{}".format(i), idx=i))
		print("sent commad {}".format(i))
	for res in r:
		print(res.get())
	rai.stop()

async def async_test():
	arai = asyncrai.AsyncInterface(displayer, "Displayer")
	arai.start()
	print(await arai("hello"))
	r = await arai.async_call("hello two", test=42)
	print(await r)
	r = []
	for i in range(50):
		r.append(await arai.async_call("Req n°{}".format(i), idx=i))
		print("sent commad {}".format(i))
	for res in r:
		print(await res)
	arai.stop()

if __name__ == "__main__":
	sync_test()
	asyncio.run(async_test())
