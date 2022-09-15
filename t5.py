from xml_utils import lxml_etree_to_local_xml, local_xml_from_filename
import xml_types as T
from lxml import etree

r = local_xml_from_filename('data/basic-test.xml')


class filter_configuration(T.filter_configuration):
	def node(self, node):

		if not self.parent: #Preserve root
			return node
		else:
			return T.placeholder(node.tag)

	def attribute(self, attribute):
		#return T.attribute(attribute.key, attribute.value + ' (was visited)')

		return T.attribute(attribute.key, T.placeholder(attribute.key))

	def data(self, data):
		return T.placeholder('das_data')
		#return T.data(data.value + ' (was visited)')

	def comment(self, comment):
		#return T.comment(comment.value + ' (was visited)')
		return



#print(r)

#print()
fr = r.filter(filter_configuration())
#print(fr)


context = T.context(placeholder_data = dict(
	attribute = 'mah-attribute',
	remove_me = None,
	change_me = 'CHANGE',
	das_data = T.data('yo!\n'),
	tag = T.node(None, 'better_node', (), ()),
	ammend_me = T.node('blargh', 'ammended', (), ()),
	replace_me = T.data('Hahahaha'),
))


et = fr.to_lxml_etree(context)
#print(et)

from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import Terminal256Formatter

original = str(etree.tostring(et, xml_declaration=True, standalone=et.docinfo.standalone, encoding=et.docinfo.encoding, pretty_print=True), 'utf-8')
print()
print(highlight(original, XmlLexer(), Terminal256Formatter(style='fruity')))
