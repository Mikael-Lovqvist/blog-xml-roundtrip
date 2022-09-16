import xml_types as T
from lxml import etree


def ns_diff(old, new):
	#Note - we do not check if new is missing something from old - this is assumed to not happen
	result = dict()
	for key, value in new.items():
		if (key not in old) or (value != old[key]):
			result[key] = value

	return result


def lxml_etree_to_local_xml(node, parent=None):
	if node.__class__ is etree._Comment:
		yield T.comment(node.text)

	elif node.__class__ is etree._Element:

		plain = node.tag.rsplit('}', 1)[-1]

		children = tuple()

		#if node.tag == '_T_graph':
		#	print(node.getchildren()[0].nsmap)

		if node.text:
			children += (T.data(node.text),)

		for child in node.getchildren():
			children += tuple(lxml_etree_to_local_xml(child, node))

		if parent is not None:
			ns_attributes = tuple(T.ns_attribute(f'xmlns:{key}' if key is not None else 'xmlns', value) for key, value in ns_diff(parent.nsmap, node.nsmap).items())

		else:
			ns_attributes = tuple(T.ns_attribute(f'xmlns:{key}' if key is not None else 'xmlns', value) for key, value in node.nsmap.items())

		attributes = tuple(T.attribute(key, value) for key, value in node.items()) + ns_attributes

		yield T.node(node.prefix, plain, attributes, children)


	elif node.__class__ is etree._ElementTree:
		#TODO - maybe copy some stuff from node.docinfo here
		root = node.getroot()
		#children = tuple()
		#for child in root.getchildren():
			#children += tuple(lxml_etree_to_local_xml(child))

		[local_root] = lxml_etree_to_local_xml(root, None)

		yield T.tree(local_root)
		return #tree has no tail

	else:
		raise TypeError(node)

	if node.tail:
		yield T.data(node.tail)


def local_xml_from_filename(filename):
	[r] = lxml_etree_to_local_xml(etree.parse(filename))
	return r

def local_xml_from_string(data):
	[r] = lxml_etree_to_local_xml(etree.fromstring(data))
	return r

