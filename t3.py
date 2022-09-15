
from local_types import etree, filter_configuration, filter_context, filter_operation
from collections import deque

#While working on this I just realized that we can't use tree.iter() because if we are replacing a node we should not go into that nodes children.
#We will start a new function for this

def process_xml_tree2(node, filters):
	if isinstance(node, etree._Comment):	#TODO - underscore?

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

			if filter_result is None or filter_result is filter_operation.ignore:
				pass
			elif filter_result is filter_operation.remove:
				return None
			elif isinstance(filter_result, filter_operation.replace):
				return filter_result.replacement
			else:
				raise NotImplementedError(filter_result)

		#If we got here, we kept the node but are going to check the attributes for it

		new_items = dict()

		for key, value in node.items():
			attribute_info = dict(
				key = 		key,
				value = 	value,
			)
			pending_key, pending_value = key, value

			if filter_candidate := filters.attribute:
				filter_result = filters.attribute(filter_context.attribute, key, **node_info, **attribute_info)
				print('.. attribute', filter_result)

				if filter_result is None or filter_result is filter_operation.ignore:
					pass
				elif filter_result is filter_operation.remove:
					continue
				elif isinstance(filter_result, filter_operation.replace):
					pending_key = filter_result.replacement
				else:
					raise NotImplementedError(filter_result)



		if filter_candidate := filters.data:
			filter_result = filters.data(filter_context.data, node.text, **node_info)
			print('.. data', filter_result)


		#We should replicate the new node here
		replacement_element = node.makeelement(node.tag, new_items, node.nsmap)

		for sub_element in node.getchildren():
			if (new_sub_element := process_xml_tree2(sub_element, filters)) is not None:
				replacement_element.append(new_sub_element)

		return replacement_element




def process_xml_tree(tree, filters):

	mutations = deque()

	for node in tree.iter():
		if isinstance(node, etree._Comment):	#TODO - underscore?

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

				if filter_result is None or filter_result is filter_operation.ignore:
					pass
				else:
					mutations.append((node, filter_result))

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

	return mutate_tree(tree, mutations)


def mutate_tree(tree, mutations):
	for subject, mutation in mutations:
		if isinstance(subject, etree._Element):

			pass

		else:
			raise NotImplementedError(subject)





#Note - in this version we will not try the amend feature since it can get a bit nitty gritty with what exactly we are amending within the tag (children, attributes etc)
#Note - Not sure if we should refer to node in this implementation since we do not wish any mutations of node to occur here
def tag_filter(context, tag, node = None, prefix = None, plain = None, ns = None, key = None, value = None):
	if plain == 'remove_me':
		return filter_operation.remove
	elif plain == 'replace_me':
		return filter_operation.replace(etree.Element('new_thing'))

def attribute_filter(context, key, value, node = None, prefix = None, plain = None, ns = None):
	if key == 'remove_me':
		return filter_operation.remove
	elif key == 'change_me':
		return filter_operation.replace(('hello', 'world'))



tree = etree.parse('data/basic-test.xml')
ptree = process_xml_tree2(tree.getroot(), filter_configuration(tag=tag_filter, attribute=attribute_filter))



print(etree.tostring(ptree, xml_declaration=True, standalone=tree.docinfo.standalone, encoding=tree.docinfo.encoding))
