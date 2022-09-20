from pathlib import Path
import re
from collections import deque

WS_CHARS = set('\t\r\n ')

def istype(item, type_or_tuple):
	item_type = type(item)
	if isinstance(type_or_tuple, (tuple, list)):
		for sub_type in type_or_tuple:
			if item_type is sub_type:
				return True
	else:
		if item_type is type_or_tuple:
			return True

	return False


class interface:
	class element_attributes:
		def process_attributes(self, processor):
			for attribute in self.attributes:
				yield processor(attribute)

	class element_children:
		def process_children(self, processor):
			for child in self.children:
				yield processor(child)

		def iter_children(self, instance_check=None, type_check=None):
			for child in self.children:
				def process_child():
					use_filtering = bool(instance_check or type_check)

					if instance_check:
						if isinstance(child, instance_check):
							yield child
							return
					elif type_check:
						if istype(child, type_check):
							yield child
							return

					else:
						yield child

				yield from process_child()



class XML_TOKEN:
	class meta_element(interface.element_attributes):
		def __init__(self, tag, attributes=None):
			self.tag = tag
			self.attributes = deque() if attributes is None else attributes

		def __repr__(self):
			return f'<{self.__class__.__qualname__} {self.tag!r} #A {len(self.attributes)}>'

	class element(interface.element_children, interface.element_attributes):
		def __init__(self, prefix, tag, attributes=None, children=None):
			self.prefix = prefix
			self.tag = tag
			self.attributes = deque() if attributes is None else attributes
			self.children = deque() if children is None else children

		def __repr__(self):
			return f'<{self.__class__.__qualname__} {self.prefix!r}:{self.tag!r} #A {len(self.attributes)} #C {len(self.children)}>'

	class data:
		def __init__(self, value):
			self.value = value

		def __repr__(self):
			return f'<{self.__class__.__qualname__} #D {len(self.value)}>'

	class reference:
		def __init__(self, id):
			self.id = id

		def __repr__(self):
			return f'<{self.__class__.__qualname__} {self.id!r}>'

	class comment:
		def __init__(self, value):
			self.value = value

		def __repr__(self):
			return f'<{self.__class__.__qualname__} #D {len(self.value)}>'

	class document(interface.element_children):
		def __init__(self, children=None):
			self.children = deque() if children is None else children

		def __repr__(self):
			return f'<{self.__class__.__qualname__} #C {len(self.children)}>'

	class fragment(interface.element_children):
		def __init__(self, children=None):
			self.children = deque() if children is None else children

		def __repr__(self):
			return f'<{self.__class__.__qualname__} #C {len(self.children)}>'

	class attribute_name:
		def __init__(self, prefix, name):
			self.prefix = prefix
			self.name = name

	class attribute:
		def __init__(self, prefix, name, value):
			self.prefix = prefix
			self.name = name
			self.value = value

		def __repr__(self):
			return f'<{self.__class__.__qualname__} {self.prefix!r}:{self.name!r} = {self.value!r}>'


class rule:
	def __init__(self, pattern):
		self.pattern = re.compile(pattern)

	def __call__(self, function):
		return registered_rule(self, function)

class registered_rule:
	def __init__(self, rule, function):
		self.pattern = rule.pattern
		self.function = function


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


class tokenizer:
	def __init__(self, initial_stack_entry):
		self.rule = stack()
		self.rule.push(initial_stack_entry)
		self.element = stack(XML_TOKEN.document())

	def emit_element(self, element):
		self.element.current.children.append(element)

	def emit_data(self, value):
		self.element.current.children.append(XML_TOKEN.data(value))

	def emit_comment(self, value):
		self.element.current.children.append(XML_TOKEN.comment(value))

	def emit_attribute_name(self, prefix, name):
		self.element.current.attributes.append(XML_TOKEN.attribute_name(prefix, name))

	def emit_attribute_value(self, value):

		an = self.element.current.attributes.pop()
		assert isinstance(an, XML_TOKEN.attribute_name)
		self.element.current.attributes.append(XML_TOKEN.attribute(an.prefix, an.name, value))

		#self.element.current.attributes.append(XML_TOKEN.attribute_value(value))

	def process(self, text):
		self.text = text
		self.position = 0


		while self.position < len(self.text):

			for rule in self.rule.current.__dict__.values():
				if isinstance(rule, registered_rule):
					if m := rule.pattern.match(self.text, self.position):
						result = rule.function(self, rule, m)
						break
			else:
				raise Exception(f'Unknown syntax ({self.rule.current})',  self.position, self.text[self.position:self.position+100])

class rules:
	class main:
		@rule(r'[^<]+')
		def data(parser, rule, match):
			parser.position = match.end()
			parser.emit_data(match.group())

		@rule(r'<!--(.*)-->')
		def comment(parser, rule, match):
			parser.position = match.end()
			parser.emit_comment(match.group(1))

		@rule(r'<\?(\w+)')	#Not sure if these could have namespaces so skipping that for now
		def start_meta_tag(parser, rule, match):
			parser.position = match.end()
			parser.rule.push(rules.in_meta_tag)
			parser.element.push(XML_TOKEN.meta_element(match.group(1)))

		@rule(r'<(\w+)(?::(\w+))?')
		def start_tag(parser, rule, match):
			left, right = match.groups()
			if right is None:
				prefix, tag = None, left
			else:
				prefix, tag = left, right

			parser.position = match.end()
			parser.rule.push(rules.in_tag)
			parser.element.push(XML_TOKEN.element(prefix, tag))

		@rule(r'</(\w+)(?::(\w+))?>')
		def end_tag(parser, rule, match):
			left, right = match.groups()
			if right is None:
				prefix, tag = None, left
			else:
				prefix, tag = left, right

			parser.position = match.end()

			pending = parser.element.pop()

			assert pending.prefix == prefix and pending.tag == tag

			parser.emit_element(pending)



	class in_tag:
		@rule(r'\s+')
		def ws(parser, rule, match):
			parser.position = match.end()

		@rule(r'>')
		def end_tag(parser, rule, match):
			parser.position = match.end()
			parser.rule.pop()

		@rule(r'/>')
		def closing_end_tag(parser, rule, match):
			parser.position = match.end()
			parser.rule.pop()
			parser.emit_element(parser.element.pop())


		@rule(r'([\w\.]+)(?::([\w\.]+))?')	#This is a bit of a hack since I am not sure if schemas can have dots or not but it will do for now
		def attribute_start(parser, rule, match):
			left, right = match.groups()
			if right is None:
				prefix, name = None, left
			else:
				prefix, name = left, right

			parser.position = match.end()
			parser.rule.push(rules.after_attribute_name)
			parser.emit_attribute_name(prefix, name)



	class in_meta_tag:
		@rule(r'\?>')
		def end_meta_tag(parser, rule, match):
			parser.position = match.end()
			parser.rule.pop()
			parser.emit_element(parser.element.pop())

		@rule(r'([\w\.]+)(?::([\w\.]+))?')	#This is a bit of a hack since I am not sure if schemas can have dots or not but it will do for now
		def attribute_start(parser, rule, match):
			left, right = match.groups()
			if right is None:
				prefix, name = None, left
			else:
				prefix, name = left, right

			parser.position = match.end()
			parser.rule.push(rules.after_attribute_name)
			parser.emit_attribute_name(prefix, name)

		@rule(r'\s+')
		def ws(parser, rule, match):
			parser.position = match.end()

	class after_attribute_name:
		@rule(r'\s*=\s*"')
		def assign_double_quoted_value(parser, rule, match):
			parser.position = match.end()
			parser.rule.pop()
			parser.rule.push(rules.double_quoted_value)

		@rule(r"\s*=\s*'")
		def assign_single_quoted_value(parser, rule, match):
			parser.position = match.end()
			parser.rule.pop()
			parser.rule.push(rules.single_quoted_value)

		@rule(r'\s*=\s*PLACEHOLDER:([\w\.]+)')	#TODO - should be configurable
		def placeholder(parser, rule, match):
			parser.position = match.end()
			parser.rule.pop()
			parser.emit_attribute_value(XML_TOKEN.reference(match.group(1)))

		@rule(r'>')
		def laxed_end(parser, rule, match):
			#TODO - this feature should be optional
			parser.position = match.end()
			parser.emit_attribute_value(None)
			parser.rule.pop()	#name
			parser.rule.pop()	#tag


		@rule(r'\s*([\w\.]+)(?::([\w\.]+))?')	#This is a bit of a hack since I am not sure if schemas can have dots or not but it will do for now
		def laxed_attribute_start(parser, rule, match):
			#TODO - this feature should be optional
			left, right = match.groups()
			if right is None:
				prefix, name = None, left
			else:
				prefix, name = left, right

			parser.position = match.end()
			parser.emit_attribute_value(None)
			parser.rule.pop()	#name

			parser.rule.push(rules.after_attribute_name)
			parser.emit_attribute_name(prefix, name)



	class double_quoted_value:
		#TODO - support escapes
		@rule(r'[^"]*')
		def value(parser, rule, match):
			parser.position = match.end() + 1	#include non consumed quotation mark

			parser.rule.pop()
			parser.emit_attribute_value(match.group(0))

	class single_quoted_value:
		#TODO - support escapes
		@rule(r"[^']*")
		def value(parser, rule, match):
			parser.position = match.end() + 1	#include non consumed quotation mark

			parser.rule.pop()
			parser.emit_attribute_value(match.group(0))


def format_xml(item):
	if isinstance(item, (XML_TOKEN.document, XML_TOKEN.fragment)):
		return ''.join(format_xml(c) for c in item.children)

	elif isinstance(item, XML_TOKEN.meta_element):
		inner = ' '.join((item.tag, *(format_xml(c) for c in item.attributes)))
		return f'<?{inner}?>'

	elif isinstance(item, XML_TOKEN.data):
		#TODO - escapes?
		return item.value

	elif isinstance(item, XML_TOKEN.comment):
		#TODO - escapes?
		return f'<!--{item.value}-->'

	elif isinstance(item, XML_TOKEN.element):
		if item.prefix is None:
			tag = item.tag
		else:
			tag = f'{item.prefix}:{item.tag}'

		tag_start = ' '.join((tag, *(format_xml(c) for c in item.attributes)))
		children = ''.join(format_xml(c) for c in item.children)

		if item.children:
			return f'<{tag_start}>{children}</{tag}>'
		else:
			return f'<{tag_start}/>'

	elif isinstance(item, XML_TOKEN.attribute):
		if item.value is None:
			#value = ''	#This should potentially raise an exception depending on options
			raise Exception(f'Found empty attribute value ({item}) in output meant to be formatted')
		elif isinstance(item.value, XML_TOKEN.reference):
			#value = f'MISSING PLACEHOLDER: {item.value.id}'	#TODO - this should perhaps raise exception
			raise Exception(f'Found reference {item.value} in output meant to be formatted')
		else:
			value = item.value.replace('"', '\\"')	#TODO - make sure this is proper escapes

		if item.prefix is None:
			return f'{item.name}="{value}"'
		else:
			return f'{item.prefix}:{item.name}="{value}"'

	raise TypeError(item)

def walk_xml(item):
	if isinstance(item, (XML_TOKEN.document, XML_TOKEN.fragment)):
		yield item
		for child in item.children:
			yield from walk_xml(child)

	elif isinstance(item, (XML_TOKEN.meta_element, XML_TOKEN.data, XML_TOKEN.comment, XML_TOKEN.attribute)):
		yield item

	elif isinstance(item, XML_TOKEN.element):
		yield item
		for attribute in item.children:
			yield from walk_xml(attribute)

		for child in item.children:
			yield from walk_xml(child)
	else:

		raise TypeError(item)



def dump(item, indent=''):
	if isinstance(item, (XML_TOKEN.document, XML_TOKEN.fragment)):
		print(f'{indent}{item!r}')
		for child in item.children:
			dump(child, f'{indent}  ')
	elif isinstance(item, (XML_TOKEN.comment, XML_TOKEN.data)):
		print(f'{indent}{item!r}: {item.value!r}')
	elif isinstance(item, XML_TOKEN.element):
		print(f'{indent}{item!r}')
		for attribute in item.attributes:
			dump(attribute, f'{indent}A ')
		for child in item.children:
			dump(child, f'{indent}C ')
	else:
		print(f'{indent}{item!r}')



def pretty_dump_xml(xml):
	from pygments import highlight
	from pygments.lexers import XmlLexer
	from pygments.formatters import Terminal256Formatter

	print(highlight(xml, XmlLexer(), Terminal256Formatter(style='fruity')))

