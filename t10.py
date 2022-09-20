from t8_types import tokenizer, rules, Path, format_xml, XML_TOKEN, dump, pretty_dump_xml, walk_xml
from t10_templates import template_processor, positional_template, template
#Continuation of t9 - focusing on representing the yed graph part of things

t = tokenizer(rules.main)
t.process(Path('data/template2.xml').read_text())

[doc] = t.element.pop_all() #make sure w get exactly one thing

context = template_processor(
	template_factory = positional_template,
	placeholder_prefix = 'PLACEHOLDER',
	template_prefix = 'TEMPLATE',
)

TPL = context(doc)


def xml_element(tag, attributes, children=()):

	def split_prefix(item):

		pieces = item.split(':', 1)
		if len(pieces) == 1:
			return None, pieces[0]
		else:
			return pieces

	return XML_TOKEN.element(*split_prefix(tag), tuple(XML_TOKEN.attribute(*split_prefix(k), v) for k, v in attributes.items()), children)

class prefixed_key_registry:
	def __init__(self, prefix, start=0):
		self.prefix = prefix
		self.pending = start
		self.by_identity = dict()
		self.by_id = dict()

	def register(self, identity):
		id = f'{self.prefix}{self.pending}'
		self.by_identity[identity] = id
		self.by_id[id] = identity
		self.pending += 1
		return id

	def register_using_factory(self, factory):
		id = f'{self.prefix}{self.pending}'
		identity = factory(id)
		self.by_identity[identity] = id
		self.by_id[id] = identity
		self.pending += 1
		return id

	def __iter__(self):
		yield from self.by_identity


data_keys = prefixed_key_registry('d')
nodes = prefixed_key_registry('n')

node_graphics = data_keys.register_using_factory(lambda id: xml_element('key', {'for': 'node', 'id': id, 'yfiles.type': 'nodegraphics'}))

test_node_labels = (
	('#FF00FF', 'First'),
	('#FFFF00', 'Second'),
	('#00FFFF', 'Third'),
)

def rectangle_node(color, label):
	return nodes.register_using_factory(lambda id:
		TPL.node(id,
			XML_TOKEN.fragment((
				xml_element('data', {'key': node_graphics}, (
					TPL.shape_node(color, XML_TOKEN.data(label)),
				)),
			)),
		)
	)


for c, l in test_node_labels:
	rectangle_node(c, l)



xml_output = TPL.graph(
	XML_TOKEN.fragment((
		*data_keys,
		XML_TOKEN.comment('Experimental'), XML_TOKEN.data('\n'),
		TPL.graph_def('G',
			XML_TOKEN.fragment((
				*nodes,
			)),
		),
	))
)



#Clean up whitespace
for data in walk_xml(xml_output):
	if isinstance(data, XML_TOKEN.data):
		data.value = data.value.strip('\r\n\t ')

pure_result = format_xml(xml_output)


#Pretty print
from lxml import etree
tree = etree.fromstring(bytes(pure_result, 'utf-8'))
result = etree.tostring(tree, encoding='unicode', pretty_print=True)




# from xml.etree import ElementTree
# tree = ElementTree.fromstring(result)
# ElementTree.indent(tree)
# print(ElementTree.tostring(tree, 'unicode'))

pretty_dump_xml(result)
Path('out/t10-out.graphml').write_text(pure_result)


# print(format_xml(positional.key_def('Description', 'string', 'graph', 'd0')))
# print(format_xml(positional.data_ref('d0')))

# print(format_xml(positional.node('d0', XML_TOKEN.data('hello'))))


#pretty_dump_xml(format_xml(r))