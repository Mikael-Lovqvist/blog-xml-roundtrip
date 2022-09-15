# In this test we are going to test the basic templating system
# The templating system will have a few different pieces it cares about which should be optional to use or not.
# For each feature we could define a function that would determin if that particular piece of data contains templating elements or not.


# In this first test the following will be cared about: tag, attribute, value, data and comment.

# <tag attribute="value">data</tag>
# <!--comment-->

from dataclasses import dataclass
import typing as T
from lxml import etree
import enum


class filter_context(enum.Enum):
	tag				= enum.auto()
	attribute		= enum.auto()
	value			= enum.auto()
	data			= enum.auto()
	comment			= enum.auto()

class filter_operation(enum.Enum):
	ignore			= enum.auto()
	remove			= enum.auto()

#We define this operation outside because enum.Enum will try to turn it into an enum member otherwise.
@dataclass
class replace:
	replacement:	object

filter_operation.replace = replace


@dataclass
class filter_configuration:
	tag: 		T.Callable = None
	attribute: 	T.Callable = None
	value: 		T.Callable = None
	data: 		T.Callable = None
	comment: 	T.Callable = None




def process_xml_tree(tree, filters):

	for node in tree.iter():
		if isinstance(node, etree._Comment):

			if filter_candidate := filters.comment:
				filter_result = filters.comment(filter_context.comment, node.text)
				print('.. comment', filter_result)
		else:

			node_info = dict(
				node = 		node,
				prefix = 	node.prefix,
				plain = 	node.tag.rsplit('}', 1)[-1],
				ns = 		node.nsmap.get(node.prefix)
			)

			if filter_candidate := filters.tag:
				filter_result = filters.tag(filter_context.tag, node.tag, **node_info)
				print('.. tag', filter_result)

			for key, value in node.items():
				attribute_info = dict(
					key = 		key,
					value = 	value,
				)

				if filter_candidate := filters.attribute:
					filter_result = filters.attribute(filter_context.attribute, key, **node_info, **attribute_info)
					print('.. attribute', filter_result)

				if filter_candidate := filters.value:
					filter_result = filters.value(filter_context.value, value, **node_info, **attribute_info)
					print('.. value', filter_result)

			if filter_candidate := filters.data:
				filter_result = filters.data(filter_context.data, node.text, **node_info)
				print('.. data', filter_result)

# https://lxml.de/apidoc/lxml.etree.html?highlight=_element#lxml.etree._Element
# Questions - Should we care about .tail?

def dummy_filter(context, data, node = None, prefix = None, plain = None, ns = None, key = None, value = None):
	print(locals())


tree = etree.parse('data/basic-test.xml')
process_xml_tree(tree, filter_configuration(tag=dummy_filter, attribute=dummy_filter, value=dummy_filter, data=dummy_filter, comment=dummy_filter))

#This is looking like a good start. We will continue in t3.py

