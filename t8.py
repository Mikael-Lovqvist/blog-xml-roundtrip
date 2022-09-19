from pathlib import Path
import re
from collections import deque

WS_CHARS = set('\t\r\n ')

class XML_TOKEN:
	class meta_tag:
		def __init__(self, tag, attributes=None):
			self.tag = tag
			self.attributes = deque() if attributes is None else attributes

	class tag:
		def __init__(self, prefix, tag, attributes=None, children=None):
			self.prefix = prefix
			self.tag = tag
			self.attributes = deque() if attributes is None else attributes
			self.children = deque() if children is None else children

	class data:
		def __init__(self, value):
			self.value = value

	class comment:
		def __init__(self, value):
			self.value = value

	class document:
		def __init__(self, children=None):
			self.children = deque() if children is None else children

	class attribute_name:
		def __init__(self, prefix, name):
			self.prefix = prefix
			self.name = name

	class attribute:
		def __init__(self, prefix, name, value):
			self.prefix = prefix
			self.name = name
			self.value = value


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
				raise Exception('Unknown syntax',  self.position, self.text[self.position:self.position+100])

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
			parser.element.push(XML_TOKEN.meta_tag(match.group(1)))

		@rule(r'<(\w+)(?::(\w+))?')
		def start_tag(parser, rule, match):
			left, right = match.groups()
			if right is None:
				prefix, tag = None, left
			else:
				prefix, tag = left, right

			parser.position = match.end()
			parser.rule.push(rules.in_tag)
			parser.element.push(XML_TOKEN.tag(prefix, tag))

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
	if isinstance(item, XML_TOKEN.document):
		return ''.join(format_xml(c) for c in item.children)

	elif isinstance(item, XML_TOKEN.meta_tag):
		inner = ' '.join((item.tag, *(format_xml(c) for c in item.attributes)))
		return f'<?{inner}?>'

	elif isinstance(item, XML_TOKEN.data):
		#TODO - escapes?
		return item.value

	elif isinstance(item, XML_TOKEN.comment):
		#TODO - escapes?
		return f'<!--{item.value}-->'

	elif isinstance(item, XML_TOKEN.tag):
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
		value = item.value.replace('"', '\\"')	#TODO - make sure this is proper escapes
		if item.prefix is None:
			return f'{item.name}="{value}"'
		else:
			return f'{item.prefix}:{item.name}="{value}"'

	raise TypeError(item)


t = tokenizer(rules.main)
t.process(Path('data/test1.graphml').read_text())

[doc] = t.element.pop_all() #make sure w get exactly one thing
xml = format_xml(doc)

Path('out/test1-t8.graphml').write_text(xml)

print(xml)