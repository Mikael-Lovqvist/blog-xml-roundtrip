import xml_types as T
from lxml import etree

def lxml_etree_to_local_xml(node, tree=None):
	if node.__class__ is etree._Comment:
		yield T.comment(node.text)

	elif node.__class__ is etree._Element:

		plain = node.tag.rsplit('}', 1)[-1]

		children = tuple()

		if node.text:
			children += (T.data(node.text),)

		for child in node.getchildren():
			children += tuple(lxml_etree_to_local_xml(child))

		attributes = tuple(T.attribute(key, value) for key, value in node.items())

		yield T.node(node.prefix, plain, attributes, children)


	elif node.__class__ is etree._ElementTree:
		#TODO - maybe copy some stuff from node.docinfo here
		root = node.getroot()
		#children = tuple()
		#for child in root.getchildren():
			#children += tuple(lxml_etree_to_local_xml(child))

		[local_root] = lxml_etree_to_local_xml(root)

		yield T.tree(dict(root.nsmap), local_root)
		return #tree has no tail

	else:
		raise TypeError(node)

	if node.tail:
		yield T.data(node.tail)


def local_xml_from_filename(filename):
	[r] = lxml_etree_to_local_xml(etree.parse('data/basic-test.xml'))
	return r

