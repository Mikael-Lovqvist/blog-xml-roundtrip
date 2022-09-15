from dataclasses import dataclass
from lxml import etree
from collections import deque


class symbol:
	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return self.name

def tuple_without_none(iterable):
	return tuple(i for i in iterable if i is not None)

def iter_wihtout_none(iterable):
	return (i for i in iterable if i is not None)


@dataclass
class node:
	prefix: str
	tag: str
	attributes: tuple
	children: tuple

	def filter(self, configuration):

		#First we check if the node was replaced
		if (candidate := configuration.node(self)) is not self:
			return candidate

		#If not we will filter the attributes and children
		new_node = node(
			self.prefix,
			self.tag,
			(),
			(),
		)

		with configuration.node_stack(new_node):
			new_node.attributes = tuple_without_none(a.filter(configuration) for a in self.attributes)
			new_node.children = tuple_without_none(c.filter(configuration) for c in self.children)

		return new_node


	def to_lxml_etree(self, context):
		tree = context.get_tree()
		element = etree.Element(
			f'{{{tree.namespace_map[self.prefix]}}}{self.tag}' if self.prefix else self.tag,
			dict(iter_wihtout_none(a.to_lxml_etree(context) for a in self.attributes)),
			tree.namespace_map,
		)

		for child_candidate in self.children:

			child = context.resolve_placeholder(child_candidate)
			if child is None:
				continue

			if isinstance(child, (node, comment)):
				element.append(child.to_lxml_etree(context))
			elif isinstance(child, data):
				if len(element) == 0:
					if element.text is None:
						element.text = child.value
					else:
						element.text += child.value
				else:
					tail_element = element[-1]
					if tail_element.tail is None:
						tail_element.tail = child.value
					else:
						tail_element.tail += child.value
			else:
				raise NotImplementedError(child)

		return element


@dataclass
class tree:
	namespace_map: dict
	root: node

	def filter(self, configuration):
		new_tree = tree(self.namespace_map, None)
		with configuration.tree_context(new_tree):
			new_tree.root = self.root.filter(configuration)

		return new_tree

	def to_lxml_etree(self, context):
		with context.tree_context(self):
			return etree.ElementTree(
				self.root.to_lxml_etree(context),
			)



@dataclass
class attribute:
	key: str
	value: str

	def filter(self, configuration):
		return configuration.attribute(self)

	def to_lxml_etree(self, context):

		key = context.resolve_placeholder(self.key)
		if key is None:
			return

		value = context.resolve_placeholder(self.value)
		if value is None:
			return

		return (key, value)

@dataclass
class placeholder:
	id: str


@dataclass
class data:
	value: str

	def filter(self, configuration):
		return configuration.data(self)

@dataclass
class comment:
	value: str

	def filter(self, configuration):
		return configuration.comment(self)


	def to_lxml_etree(self, context):
		return etree.Comment(self.value)



RAISE_EXCEPTION = symbol('RAISE_EXCEPTION')
MISS = symbol('MISS')

class simple_stack(deque):
	def __call__(self, value):
		return pending_stack_value(self, value)

	def get(self, default=RAISE_EXCEPTION):
		if self:
			return self[-1]
		elif default is RAISE_EXCEPTION:
			raise Exception('Stack underflow')
		else:
			return default

class simple_context:
	def __call__(self, value):
		return pending_context_value(self, value)

	def get(self, default=RAISE_EXCEPTION):
		if (value := getattr(self, 'value', MISS)) is not MISS:
			return value
		elif default is RAISE_EXCEPTION:
			raise Exception('Context not available')
		else:
			return value


@dataclass
class pending_context_value:
	context: simple_context
	value: object

	def __enter__(self):
		self.context.value = self.value
		return self.context

	def __exit__(self, ev, et, tb):
		del self.context.value



@dataclass
class pending_stack_value:
	stack: simple_stack
	value: object

	def __enter__(self):
		self.stack.append(self.value)
		return self.stack

	def __exit__(self, ev, et, tb):
		self.stack.pop()

class filter_configuration:

	def __init__(self):
		self.node_stack = simple_stack()
		self.tree_context = simple_context()

	#Helper property
	@property
	def tree(self):
		return self.tree_context.get(None)

	@property
	def parent(self):
		return self.node_stack.get(None)

	def node(self, node):
		return node

	def attribute(self, attribute):
		return attribute

	def data(self, data):
		return data

	def comment(self, comment):
		return comment


class context:
	def __init__(self, placeholder_data=None):
		self.tree_context = simple_context()
		self.get_tree = self.tree_context.get
		self.placeholder_data = placeholder_data if placeholder_data is not None else dict()

	def resolve_placeholder(self, candidate_placeholder):
		if isinstance(candidate_placeholder, placeholder):
			return self.placeholder_data[candidate_placeholder.id]
		else:
			return candidate_placeholder