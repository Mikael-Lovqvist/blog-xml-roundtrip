import xml_types as XML
import xml_templating as XT
from utils import is_subclass


#NOTE - if we add support for template_processor and similar, we also need to start keeping track of what items we have detailed and use short versions to refer to those.
#	we could also use a more capable dumper that could have various settings depending on what you are interested in viewing

def dump(item, indent=''):
	if isinstance(item, (XML.document, XML.fragment)):
		print(f'{indent}{item.__class__.__qualname__}')
		for child in item.children:
			dump(child, f'{indent}  ')
	elif isinstance(item, (XML.comment, XML.data)):
		print(f'{indent}{item.__class__.__qualname__}: {item.value!r}')
	elif isinstance(item, XML.element):
		tag =f'{item.prefix}:{item.tag}' if item.prefix is not None else item.tag
		print(f'{indent}{item.__class__.__qualname__} {tag}')
		for attribute in item.attributes:
			dump(attribute, f'{indent}  ')
		for child in item.children:
			dump(child, f'{indent}  ')
	elif isinstance(item, XML.attribute):
		print(f'{indent}{item.__class__.__qualname__} {item.name}: {item.value!r}')
	elif isinstance(item, XML.meta_element):
		tag = item.tag
		print(f'{indent}{item.__class__.__qualname__} {tag}')
		for attribute in item.attributes:
			dump(attribute, f'{indent}  ')

	elif isinstance(item, XT.bound_positional_template):
		ph = ', '.join(item.placeholder_ids)
		print(f'{indent}{item.__class__.__qualname__} {item.name}({ph})')
		dump(item.template, f'{indent}  ')

	elif is_subclass(item, XT.base_template_collection):
		print(f'{indent}{item.__qualname__} (template collection)')

		for k in item.__dict__:
			if k.startswith('_'):
				continue
			dump(item.__dict__[k], f'{indent}  ')


	elif isinstance(item, XT.template):
		print(f'{indent}{item.__class__.__qualname__} {item.id}')
		dump(item.context, f'{indent}  ')
		dump(item.element, f'{indent}  ')


	else:
		print(f'{indent}{item!r}')
