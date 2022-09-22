#These are high level functions that draw upon many of the lower level ones.
#it would be nice to have everything semantically grouped but that creates circular dependencies so we also have to have the concept of "levels".

from xml_tokenizer import tokenizer
import xml_rules as XR
from xml_templating import template_processor, positional_template

from pathlib import Path

def load_templates_from_string(data, template_factory = positional_template, placeholder_prefix = 'PLACEHOLDER', template_prefix = 'TEMPLATE'):
	t = tokenizer(XR.main)
	t.process(data)

	[doc] = t.element.pop_all()

	tp = template_processor(
		template_factory = template_factory,
		placeholder_prefix = placeholder_prefix,
		template_prefix = template_prefix,
	)

	return tp(doc)

def load_templates_from_path(path, template_factory = positional_template, placeholder_prefix = 'PLACEHOLDER', template_prefix = 'TEMPLATE'):
	return load_templates_from_string(
		Path(path).read_text(),
		template_factory = template_factory,
		placeholder_prefix = placeholder_prefix,
		template_prefix = template_prefix
	)
