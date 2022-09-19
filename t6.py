from xml_templates import templates_from_xml_filename
import xml_types as T


#templates = templates_from_xml_filename('data/template1.graphml-template')

from xml_templates import local_xml_from_filename
templates = templates_from_xml_filename('data/template1.graphml-template')

# for t in templates.root.children:
# 	if isinstance(t, T.node):
# 		print(t.tag)
# 		for a in t.children[1].attributes:
# 			print(f'    {a}')


TM = templates.get_template_ns()

print(TM)

#print(dir(templates.get_template_ns()))



context = T.context(placeholder_data = dict(
	key_definitions = T.data('keydefs'),
	data_definitions = T.data('datadefs'),
	graph = T.node('y', 'graph', (), ()),
	tool = 'sometool',
))



g = TM.graph(context).as_root()


exit()


from lxml import etree
et = g.to_lxml_etree(context)
from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import Terminal256Formatter

original = str(etree.tostring(et, xml_declaration=True, standalone=False, encoding='UTF-8', pretty_print=True), 'utf-8')
print()
print(highlight(original, XmlLexer(), Terminal256Formatter(style='fruity')))


# for item in templates.walk_everything():
# 	if isinstance(item, T.text_sequence):
# 		print('TS', item)

# 	elif isinstance(item, T.template):
# 		print('TEMPLATE', item.id)