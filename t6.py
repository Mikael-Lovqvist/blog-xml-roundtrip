from xml_templates import templates_from_xml_filename
import xml_types as T


#templates = templates_from_xml_filename('data/template1.graphml-template')

from xml_templates import local_xml_from_filename
templates = local_xml_from_filename('data/template1.graphml-template')

for t in templates.root.children:
	if isinstance(t, T.node) and t.tag == '_T_graph':
		print(t.children[1].attributes)


#TM = templates.get_template_ns()

#print(dir(templates.get_template_ns()))

#print(TM.graph())

# for item in templates.walk_everything():
# 	if isinstance(item, T.text_sequence):
# 		print('TS', item)

# 	elif isinstance(item, T.template):
# 		print('TEMPLATE', item.id)