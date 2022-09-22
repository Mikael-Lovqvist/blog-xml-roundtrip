#From base directory
#   PYTHONPATH=. python examples/t1.py

import xml_inspection as XI
import xml_helpers as XH
import xml_formatting as XF
import xml_inspection as XI
import xml_highlevel as XHL

TPL =  XHL.load_templates_from_path('data/template2.xml')


data = TPL.graph(

	XH.fragment(
		XH.element('stuff:thing', some_attribute='123'),
		XH.element('more', some_attribute='456'),
	)

)

XI.dump(TPL)

print(XF.terminal_highlight(data))