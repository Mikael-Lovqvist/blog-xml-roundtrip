import xml_types as XML

def format(item):
	if isinstance(item, (XML.document, XML.fragment)):
		return ''.join(format(c) for c in item.children)

	elif isinstance(item, XML.meta_element):
		inner = ' '.join((item.tag, *(format(c) for c in item.attributes)))
		return f'<?{inner}?>'

	elif isinstance(item, XML.data):
		#TODO - escapes?
		return item.value

	elif isinstance(item, XML.comment):
		#TODO - escapes?
		return f'<!--{item.value}-->'

	elif isinstance(item, XML.element):
		if item.prefix is None:
			tag = item.tag
		else:
			tag = f'{item.prefix}:{item.tag}'

		tag_start = ' '.join((tag, *(format(c) for c in item.attributes)))
		children = ''.join(format(c) for c in item.children)

		if item.children:
			return f'<{tag_start}>{children}</{tag}>'
		else:
			return f'<{tag_start}/>'

	elif isinstance(item, XML.attribute):
		if item.value is None:
			#value = ''	#This should potentially raise an exception depending on options
			raise Exception(f'Found empty attribute value ({item}) in output meant to be formatted')
		elif isinstance(item.value, XML.reference):
			#value = f'MISSING PLACEHOLDER: {item.value.id}'	#TODO - this should perhaps raise exception
			raise Exception(f'Found reference {item.value} in output meant to be formatted')
		else:
			value = item.value.replace('"', '\\"')	#TODO - make sure this is proper escapes

		if item.prefix is None:
			return f'{item.name}="{value}"'
		else:
			return f'{item.prefix}:{item.name}="{value}"'

	raise TypeError(item)



def terminal_highlight(xml):
	from pygments import highlight
	from pygments.lexers import XmlLexer
	from pygments.formatters import Terminal256Formatter

	if isinstance(xml, str):
		return highlight(xml, XmlLexer(), Terminal256Formatter(style='fruity'))
	elif isinstance(xml, XML.base_element):
		return highlight(format(xml), XmlLexer(), Terminal256Formatter(style='fruity'))
	else:
		raise TypeError(xml)


