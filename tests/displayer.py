import AsyncRAI

def displayer(*args, **kwargs):
	print("Args : {}".format(", ".join([str(a) for a in args])))
	print("Kwargs : {}".format(", ".join(["{} = {}".format(k,v) for k,v in kwargs.items()])))
	return "Displayed {} args and {} kwargs".format(len(args), len(kwargs))

if __name__ == "__main__":
	rai = AsyncRAI.ResourceAccessInterface("Displayer", displayer)
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
	rai.join()