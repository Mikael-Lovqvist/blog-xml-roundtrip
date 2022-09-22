from xml_tokenizer import rule
import xml_types as XML

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
		parser.rule.push(in_meta_tag)
		parser.element.push(XML.meta_element(match.group(1)))

	@rule(r'<(\w+)(?::(\w+))?')
	def start_tag(parser, rule, match):
		left, right = match.groups()
		if right is None:
			prefix, tag = None, left
		else:
			prefix, tag = left, right

		parser.position = match.end()
		parser.rule.push(in_tag)
		parser.element.push(XML.element(prefix, tag))

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
		parser.rule.push(after_attribute_name)
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
		parser.rule.push(after_attribute_name)
		parser.emit_attribute_name(prefix, name)

	@rule(r'\s+')
	def ws(parser, rule, match):
		parser.position = match.end()

class after_attribute_name:
	@rule(r'\s*=\s*"')
	def assign_double_quoted_value(parser, rule, match):
		parser.position = match.end()
		parser.rule.pop()
		parser.rule.push(double_quoted_value)

	@rule(r"\s*=\s*'")
	def assign_single_quoted_value(parser, rule, match):
		parser.position = match.end()
		parser.rule.pop()
		parser.rule.push(single_quoted_value)

	@rule(r'\s*=\s*PLACEHOLDER:([\w\.]+)')	#TODO - should be configurable
	def placeholder(parser, rule, match):
		parser.position = match.end()
		parser.rule.pop()
		parser.emit_attribute_value(XML.reference(match.group(1)))

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

		parser.rule.push(after_attribute_name)
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

