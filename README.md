# Async Resource Access Interface (AsyncRAI)
A very lightweight interface to manage and use resource asynchronously.

The goal of the AsyncRAI is to provide a simple interface standard to manage and use resource and a very lightweight implementation of it.

## The standard
Derived from the ASGI standard, ARAI goal is to provide a standard way to access a "resource" where a resource can be any object that take one or more input data, use them asyncronously in their own thread or process, and return one or more output data.
More detail in the spec folder.

## The package
The content of the package is very minimale :
	- A very barebone implementation of the base interface from the spec in the rai.py module
	- An asyncio compatible implementation of the base interface inheritead from the previous one in the asyncrai.py module
	- Exceptions needed by the both module in errors.py

## Usage
Here is an usage example for the base implementation :

```python


```