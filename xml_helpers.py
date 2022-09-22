import xml_types as XML

def split_prefix(item):
	pieces = item.split(':', 1)
	if len(pieces) == 1:
		return None, pieces[0]
	else:
		return pieces


def fragment(*children):
	return XML.fragment(children)

def element(tag, attributes=None, children=(), **additional_attributes):


	if isinstance(attributes, dict):
		final_attributes = dict(attributes, **additional_attributes)
	elif attributes is None:
		final_attributes = additional_attributes

	return XML.element(*split_prefix(tag), tuple(XML.attribute(*split_prefix(k), v) for k, v in final_attributes.items()), children)


def make_xml_pretty(item):
	#TODO - figure out what we want to do here

	raise NotImplementedError
	# if isinstance(item, (XML.document, XML.fragment)):
	# 	pending_children = deque()

	# 	for child in item.children:


	# else:
	# 	raise TypeError(item)

def walk_xml(item, attributes=False):
	if isinstance(item, (XML.document, XML.fragment)):
		yield item
		for child in item.children:
			yield from walk_xml(child)

	elif isinstance(item, (XML.meta_element, XML.data, XML.comment, XML.attribute)):
		yield item

	elif isinstance(item, XML.element):
		yield item
		if attributes:
			for attribute in item.children:
				yield from walk_xml(attribute)

		for child in item.children:
			yield from walk_xml(child)
	else:

		raise TypeError(item)

def walk_xml_data(item):
	for item in walk_xml(item):
		if isinstance(item, XML.data):
			yield item




