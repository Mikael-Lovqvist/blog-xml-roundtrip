from xml_tokenizer import tokenizer
import xml_rules as rules
import xml_types as XML


#TODO - convert to symbol
MISS = type('MISS', (), {})

class base_template_collection:
	pass

class template_processor:
	def __init__(self, parent=None, placeholder_prefix=None, template_prefix=None, locals=None, placeholder_fallback=None, template_factory=None):
		self.parent = parent
		self.locals = locals
		self.placeholder_fallback = placeholder_fallback
		self.template_factory = template_factory

		#TODO - redo this a bit, we should have some separation of concerns here regarding stacking/parenting and features

		#Note - set placeholder_prefix to False if you want to explicitly not use it
		pending_placeholder_prefix = placeholder_prefix
		if placeholder_prefix is None:
			if parent:
				pending_placeholder_prefix = parent.placeholder_prefix

		self.placeholder_prefix = pending_placeholder_prefix

		#Note - set template_prefix to False if you want to explicitly not use it
		pending_template_prefix = template_prefix
		if template_prefix is None:
			if parent:
				pending_template_prefix = parent.template_prefix

		self.template_prefix = pending_template_prefix

	def get_placeholder_value(self, id):
		value = self.get_placeholder(id)
		assert isinstance(value, str), f'Placeholder {id!r} expected to be str, got: {value!r}'
		return value

	def get_placeholder(self, id):
		if self.locals:
			if (l := self.locals.get(id, MISS)) is not MISS:
				if callable(l):
					return l(self, id)
				else:
					return l

		if self.parent:
			return self.parent.get_placeholder(id)

		if self.placeholder_fallback:
			return self.placeholder_fallback(self, id)

		raise Exception(f'Could not resolve place holder {id!r}')

	def iter_placeholders(self, item):
		#TODO - support more placeholders
		if isinstance(item, XML.element):
			if self.placeholder_prefix and self.placeholder_prefix == item.prefix:
				yield item.tag
			else:
				for attr in item.attributes:
					if isinstance(attr.value, XML.reference):
						yield attr.value.id

				for child in item.children:
					yield from self.iter_placeholders(child)
		elif isinstance(item, XML.document):
			for child in item.children:
				yield from self.iter_placeholders(child)
		elif isinstance(item, (XML.data, XML.comment, XML.meta_element)):
			pass
		else:
			raise Exception(item)


	def __call__(self, item):
		if isinstance(item, XML.element):

			if self.placeholder_prefix and self.placeholder_prefix == item.prefix:
				return self.get_placeholder(item.tag)
			else:
				return XML.element(
					item.prefix,
					item.tag,
					tuple(item.process_attributes(self)),
					tuple(item.process_children(self))
				)
		if isinstance(item, XML.meta_element):
			return item	#No change for now

		elif isinstance(item, XML.data):
			return item	#No change
		elif isinstance(item, XML.attribute):
			if isinstance(item.value, XML.reference):
				return XML.attribute(
					item.prefix,
					item.name,
					self.get_placeholder_value(item.value.id),
				)
			else:
				return item

		elif isinstance(item, XML.document):	# We will check for templates in a document if we have template_prefix
			if self.template_prefix:
				return type('templates', (base_template_collection,), {t.tag: self.template_factory(self, t.tag, t) for t in item.iter_children(instance_check=XML.element) if t.prefix == self.template_prefix})
			else:
				return item
		else:
			raise TypeError(item)

	def stack(self, locals):
		return template_processor(parent=self, locals=locals)


class template:
	def __init__(self, context, id, element):
		self.context = context
		self.id = id
		self.element = element

	def __call__(self, **context_updates):
		return XML.fragment(tuple(self.element.process_children(self.context.stack(context_updates))))

	def iter_placeholders(self):
		yield from self.context.iter_placeholders(self.element)


class bound_positional_template:
	def __init__(self, template, placeholder_ids):
		self.template = template
		self.placeholder_ids = placeholder_ids
		self.name = template.id

	def __call__(self, *pos):
		assert len(pos) == len(self.placeholder_ids)
		d = dict(zip(self.placeholder_ids, pos))
		return self.template(**d)

	def __set_name__(self, target, name):
		self.name = name

	def __repr__(self):
		args = ', '.join(self.placeholder_ids)
		return f'<template {self.name}({args})>'

def positional_template(processor, id, data):
	if isinstance(data, str):
		tok = tokenizer(rules.main)
		tok.process(data)
		[doc] = tok.element.pop_all() #make sure w get exactly one thing
	elif isinstance(data, XML.element):
		doc = data
	else:
		raise TypeError(data)
	temp = template(processor, id, doc)

	placeholder_ids = list(temp.iter_placeholders())

	return bound_positional_template(temp, placeholder_ids)
