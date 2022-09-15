#Things got a bit messy in t3 so we will refactor the handler to instead be a class and at that point the transformer might as well just be implemented in that class as well.

#Even if this is an improvement there is a fundamental issue here in how we deal with data in the xml.
#Here each node has a tail segment that can contain data which is fine as long as the point is to replace data with data and node with node.
#But if we want to replace a particular data with another node this won't work
#We should try to make an improved version of this that deals with data more consistently no matter if it is in .tail or .text but before we do that we will just get this working.
#For the purpose of messing with graphml we don't need to deal with that and I am not even sure if the xml specification mentions data between siblings

#Another thing we have not considered here is when we want to use custom placeholders for things after the processing step.
#If we have our own tree representation we can contain this and also solve the previous data/tail issue - but still, we should finish this experiment up

from lxml import etree
import enum

class operation:
	nop = enum.auto()
	remove = enum.auto()


class xml_transformer:
	def process(self, tree_or_node):
		if isinstance(tree_or_node, etree._ElementTree):
			return etree.ElementTree(self.process_node(tree_or_node.getroot()))
		else:
			print('node')

	def process_attributes(self, node):
		for key, value in node.items():
			attribute_result = self.filter_attribute(node, key, value)

			if attribute_result is None or attribute_result is operation.nop:
				yield key, value
			elif attribute_result is operation.remove:
				continue
			elif attribute_result:
				yield attribute_result


	def process_node(self, node):
		if isinstance(node, etree._Comment):

			comment_result = self.filter_comment(node)

			if comment_result is None or comment_result is operation.nop:
				pass
			elif comment_result is operation.remove:
				return
			elif isinstance(comment_result, etree._Comment):
				return comment_result
			else:
				raise NotImplementedError()

			pending_comment = etree.Comment(node.text)
			pending_comment.tail = node.tail
			return pending_comment
		else:

			#First we check if the entire node needs replacing
			node_result = self.filter_node(node, plain = node.tag.rsplit('}', 1)[-1], ns = node.nsmap.get(node.prefix))

			if node_result is None or node_result is operation.nop:
				pass
			elif node_result is operation.remove:
				return
			elif isinstance(node_result, etree._Element):
				return node_result
			else:
				raise NotImplementedError()


			pending_tag = node.tag
			pending_attributes = {key: value for key, value in self.process_attributes(node)}
			pending_nsmap = node.nsmap

			text_result = self.filter_data(node)

			if text_result is None or text_result is operation.nop:
				pending_text = node.text
			elif text_result is operation.remove:
				pending_text = None
			elif isinstance(text_result, str):
				pending_text = text_result
			else:
				raise NotImplementedError()

			pending_tail = node.tail

			pending_node = etree.Element(pending_tag, pending_attributes, pending_nsmap)
			pending_node.text = pending_text
			pending_node.tail = pending_tail

			for sub_node in node.getchildren():
				if (filtered_sub_node := self.process_node(sub_node)) is not None:
					pending_node.append(filtered_sub_node)

			return pending_node

	def filter_node(self, node, plain, ns):
		pass

	def filter_comment(self, comment):
		pass

	def filter_attribute(self, node, key, value):
		pass

	def filter_data(self, node):
		if node.text == 'data to remove':
			return operation.remove
		if node.text == 'data to change':
			return 'New Data'

class test_xml_transformer(xml_transformer):

	def filter_node(self, node, plain, ns):
		if plain == 'remove_me':
			return operation.remove
		elif plain == 'replace_me':
			replacement = etree.Element('new_element')
			replacement.tail = node.tail
			return replacement

	def filter_comment(self, comment):
		if comment.text == 'remove this comment':
			return operation.remove

		elif comment.text == 'replace this comment':
			replacement = etree.Comment('Hello World!')
			replacement.tail = comment.tail
			return replacement

	def filter_attribute(self, node, key, value):
		if key == 'remove_me':
			return operation.remove
		elif key == 'change_me':
			return ('new_key',  'new_data')



tree = etree.parse('data/basic-test.xml')
ptree = test_xml_transformer().process(tree)

from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import Terminal256Formatter

original = str(etree.tostring(tree, xml_declaration=True, standalone=tree.docinfo.standalone, encoding=tree.docinfo.encoding, pretty_print=True), 'utf-8')
print('-- ORIGINAL --')
print(highlight(original, XmlLexer(), Terminal256Formatter(style='fruity')))

result = str(etree.tostring(ptree, xml_declaration=True, standalone=tree.docinfo.standalone, encoding=tree.docinfo.encoding, pretty_print=True), 'utf-8')
print('-- MODIFIED --')
print(highlight(result, XmlLexer(), Terminal256Formatter(style='fruity')))

