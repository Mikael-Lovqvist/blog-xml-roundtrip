import xml_types as XML
from local_types import stack
import re

class rule:
	def __init__(self, pattern):
		self.pattern = re.compile(pattern)

	def __call__(self, function):
		return registered_rule(self, function)

class registered_rule:
	def __init__(self, rule, function):
		self.pattern = rule.pattern
		self.function = function


class tokenizer:
	def __init__(self, root_rules):
		self.rule = stack(root_rules)
		self.element = stack(XML.document())

	def emit_element(self, element):
		self.element.current.children.append(element)

	def emit_data(self, value):
		self.element.current.children.append(XML.data(value))

	def emit_comment(self, value):
		self.element.current.children.append(XML.comment(value))

	def emit_attribute_name(self, prefix, name):
		self.element.current.attributes.append(XML.attribute_name(prefix, name))

	def emit_attribute_value(self, value):

		an = self.element.current.attributes.pop()
		assert isinstance(an, XML.attribute_name)
		self.element.current.attributes.append(XML.attribute(an.prefix, an.name, value))

		#self.element.current.attributes.append(XML.attribute_value(value))

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
