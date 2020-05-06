
from lxml import etree

tree = etree.parse('xml_a.xml')
tree.xinclude()
print(etree.tostring(tree))