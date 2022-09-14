# This would not preserve namespaces and it would also not preserve the metatag in the beginning
# It seems this requires some work¹ with xml.etree.ElementTree so let's try something else
# ¹ https://stackoverflow.com/questions/67508370/does-elementtree-generate-its-own-nsmap-while-lxml-etree-does-not?noredirect=1&lq=1

#  _____       _     _
# |_   _|__ __| |_  / |
#   | |/ -_|_-<  _| | |
#   |_|\___/__/\__| |_|


# from xml.etree import ElementTree
# tree = ElementTree.parse('data/test1.graphml')
# tree.write('out/test1-roundtrip.graphml')


#  _____       _     ___
# |_   _|__ __| |_  |_  )
#   | |/ -_|_-<  _|  / /
#   |_|\___/__/\__| /___|


from lxml import etree
tree = etree.parse('data/test1.graphml')
# tree.write('out/test1-roundtrip.graphml')

# This was much better! But we still didn't get the meta tag

#  _____       _     ____
# |_   _|__ __| |_  |__ /
#   | |/ -_|_-<  _|  |_ \
#   |_|\___/__/\__| |___/


#tree.write('out/test1-roundtrip.graphml', xml_declaration=True)
#Almost! → <?xml version='1.0' encoding='ASCII'?>

#  _____       _     _ _
# |_   _|__ __| |_  | | |
#   | |/ -_|_-<  _| |_  _|
#   |_|\___/__/\__|   |_|


tree.write('out/test1-roundtrip.graphml', xml_declaration=True, standalone=tree.docinfo.standalone, encoding=tree.docinfo.encoding)
#Roundtrip achieved!

