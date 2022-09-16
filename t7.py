#Experiments to understand nsmap better

from lxml import etree
xml = etree.fromstring('''
  <outer xmlns:hello="...">
    <inner xmlns:world="...">
    	<hello:stuff/>
    	<world:stuff/>
    </inner>
  </outer>
''')

print('outer', xml.nsmap)
print('inner', xml[0].nsmap)
print(str(etree.tostring(xml, xml_declaration=True, standalone='no', encoding='UTF-8', pretty_print=True), 'utf-8'))

outer = etree.Element('outer', nsmap=dict(hello='...'))
tree = etree.ElementTree(outer)
inner = etree.Element('inner', nsmap=dict(hello='...', world='...'))

tree.getroot().append(inner)

print(str(etree.tostring(tree, xml_declaration=True, standalone='no', encoding='UTF-8', pretty_print=True), 'utf-8'))
