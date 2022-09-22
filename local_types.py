from collections import deque

class stack:
	def __init__(self, *initial):
		self._stack = deque(initial)

	def push(self, value):
		self._stack.append(value)

	def pop(self):
		return self._stack.pop()

	def pop_all(self):
		result = tuple(self._stack)
		self._stack.clear()
		return result


	@property
	def current(self):
		if self._stack:
			return self._stack[-1]

