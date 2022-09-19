from dataclasses import dataclass, field
from lxml import etree
from collections import deque

class symbol:
	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return self.name


RAISE_EXCEPTION = symbol('RAISE_EXCEPTION')
MISS = symbol('MISS')

class stacked_dict(deque):
	def __call__(self, sub_dict):
		return pending_stacked_dict(self, sub_dict)

	def get_dict(self):
		result = dict()
		for item in self:
			result.update(item)

		return result


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


def get_ns_key(item):
	if item == 'xmlns':
		return None

	assert item.startswith('xmlns'), '{item!r} is not a proper namespace identifier.'
	_, tail = item.split(':')
	return tail


def tuple_without_none(iterable):
	return tuple(i for i in iterable if i is not None)

def iter_without_none(iterable):
	return (i for i in iterable if i is not None)


@dataclass
class node:
	prefix: str
	tag: str
	attributes: tuple
	children: tuple

	def as_root(self):
		#We will ignore any data here - potentially later on we could decide if we should ignore all data or only whitespace or not at all
		root = None
		for child in self.children:
			if isinstance(child, node):
				if root:
					raise Exception('Too many child nodes')
				else:
					root = child

		assert root, 'Too few child nodes'
		return root

	def walk_everything(self):
		yield self
		for attribute in self.attributes:
			yield from attribute.walk_everything()

		for child in self.children:
			yield from child.walk_everything()

	def filter(self, configuration):

		#Set temporary state
		configuration.process_child_node = None

		#First we check if the node was replaced
		if (candidate := configuration.node(self)) is not self:
			if child_node := configuration.process_child_node:

				source = child_node.get()

				new_node = node(
					source.prefix,
					source.tag,
					(),
					(),
				)

				with configuration.node_stack(new_node):
					new_node.attributes = tuple_without_none(a.filter(configuration) for a in source.attributes)
					new_node.children = tuple_without_none(c.filter(configuration) for c in source.children)

				child_node.set(new_node)

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
		child_attributes = tuple(a for a in self.attributes if type(a) is attribute)
		ns_attributes = tuple(a for a in self.attributes if type(a) is ns_attribute)

		with context.stack_namespace({get_ns_key(a.key): a.value for a in ns_attributes}) as namespace_map:

			#tree = context.get_tree()
			element = etree.Element(
				f'{{{namespace_map[self.prefix]}}}{self.tag}' if self.prefix else self.tag,
				#f'{self.prefix}:{self.tag}' if self.prefix else self.tag,
				dict(iter_without_none(a.to_lxml_etree(context) for a in child_attributes)),
				namespace_map,
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
	root: node

	def walk_everything(self):
		yield self
		yield from self.root.walk_everything()

	def filter(self, configuration):
		return tree(self.root.filter(configuration))
		# new_tree = tree(None)
		# with configuration.tree_context(new_tree):
		# 	new_tree.root = self.root.filter(configuration)

		# return new_tree

	def to_lxml_etree(self, context):
		# with context.tree_context(self):
		# 	return etree.ElementTree(
		# 		self.root.to_lxml_etree(context),
		# 	)

		return etree.ElementTree(
			self.root.to_lxml_etree(context),
		)


@dataclass
class attribute:
	key: str
	value: str


	def walk_everything(self):
		yield self

		if not isinstance(self.key, str):
			yield from self.key.walk_everything()

		if not isinstance(self.value, str):
			yield from self.value.walk_everything()


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
class ns_attribute(attribute):
	pass


@dataclass
class placeholder:
	id: str

	def walk_everything(self):
		yield self


@dataclass
class data:
	value: str


	def walk_everything(self):
		yield self

		if not isinstance(self.value, str):
			yield from self.value.walk_everything()

	def filter(self, configuration):
		return configuration.data(self)

@dataclass
class text_sequence:
	sequence: deque = field(default_factory=deque)


	def walk_everything(self):
		yield self

		for item in self.sequence:
			if not isinstance(item, str):
				yield from item.walk_everything()


@dataclass
class template_collection:
	tree: tree

	# def __post_init__(self):
	# 	global_ns_attributes = tuple(a for a in self.tree.root.attributes if type(a) is ns_attribute)
	# 	for t in self.walk_everything():
	# 		if isinstance(t, template):
	# 			t.root.attributes += global_ns_attributes

	def walk_everything(self):
		yield self
		yield from self.tree.walk_everything()

	def get_template_ns(self, name='templates'):
		return type(name, (), {t.id: t for t in self.walk_everything() if isinstance(t, template)})


@dataclass
class fragment:
	children: deque = field(default_factory=deque)

@dataclass
class template:
	id: str
	root: node
	context: simple_context = field(default_factory=simple_context)

	def walk_everything(self):
		yield self
		yield from self.root.walk_everything()

	def __call__(self, context):
		with self.context(context):
			return self.format(self.root)


	def format(self, item):
		ic = type(item)
		if ic is str:
			return item
		elif ic is node:
			return node(
				item.prefix,
				item.tag,
				tuple(self.format(attribute) for attribute in item.attributes),
				tuple(self.format(child) for child in item.children),
			)
		elif ic is data:
			return data(self.format(item.value))
		elif ic is comment:
			return comment(self.format(item.value))
		elif ic in (attribute, ns_attribute):
			return ic(
				self.format(item.key),
				self.format(item.value),
			)
		elif ic is text_sequence:
			return ''.join(self.format(p) for p in item.sequence)
		elif ic is placeholder:
			return self.context.value.resolve_placeholder(item)
		else:
			raise NotImplementedError(ic)

@dataclass
class comment:
	value: str

	def walk_everything(self):
		yield self

		if not isinstance(self.value, str):
			yield from self.value.walk_everything()


	def filter(self, configuration):
		return configuration.comment(self)


	def to_lxml_etree(self, context):
		return etree.Comment(self.value)




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


@dataclass
class pending_stacked_dict:
	stack: simple_stack
	value: object

	def __enter__(self):
		self.stack.append(self.value)
		return self.stack.get_dict()

	def __exit__(self, ev, et, tb):
		self.stack.pop()


@dataclass
class access_attribute:
	target: object
	name: str

	def get(self):
		return getattr(self.target, self.name)

	def set(self, value):
		setattr(self.target, self.name, value)

@dataclass
class filter_configuration:
	node_stack: object = field(default_factory=simple_stack)
	#tree_context: object = field(default_factory=simple_context)

	process_child_node = None

	#Helper property
	# @property
	# def tree(self):
	# 	return self.tree_context.get(None)

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
		#self.tree_context = simple_context()
		#self.get_tree = self.tree_context.get
		self.placeholder_data = placeholder_data if placeholder_data is not None else dict()
		self.stack_namespace = stacked_dict()

	def resolve_placeholder(self, candidate_placeholder):
		if isinstance(candidate_placeholder, placeholder):
			return self.placeholder_data[candidate_placeholder.id]
		else:
			return candidate_placeholder