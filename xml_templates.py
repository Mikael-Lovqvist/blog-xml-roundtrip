import xml_types as T
from xml_utils import lxml_etree_to_local_xml, local_xml_from_filename
from dataclasses import dataclass
from text_utils import re_tokenizer
import re, enum



# rules = {
# 	re.compile(r'\s+'): 'Spaaaace',
# }
# for token, match in re_tokenizer('hello world, this is a test', rules):
# 	print(token, match)



class TOKEN(enum.Enum):
	text = enum.auto()
	template = enum.auto()
	variable = enum.auto()

@dataclass
class template_configuration(T.filter_configuration):
	template_pattern: object = None
	variable_pattern: object = None
	process_nodes: bool = False
	process_attributes: bool = False
	process_data: bool = False
	process_comments: bool = False

	def node(self, node):
		#NOTE - we only allow one token right now - this may change in the future
		tag = f'{node.prefix}.{node.tag}' if node.prefix else node.tag

		tokenization_result = tuple(re_tokenizer(tag, self.tokenization_rules, unmatched=TOKEN.text))
		if len(tokenization_result) == 1:
			[(token, match)] = tokenization_result


			if token is TOKEN.text:
				return node
			elif token is TOKEN.template:
				#We should define a template here
				#Currently we don't expect any attributes but this may change

				assert not node.attributes

				template_name = match.group(1)

				#Make sure that child nodes are processed
				result = T.template(template_name, node)
				self.process_child_node = T.access_attribute(result, 'root')
				return result

			elif token is TOKEN.variable:
				#We should refer to a template here
				#Currently we don't expect any attributes but this may change

				assert not node.attributes, f'There were attributes! {node.attributes}'
				return T.placeholder(match.group(1))

			else:
				raise NotImplementedError(token)


		else:
			return node


	def attribute(self, attribute):
		pending_key = self.process_text(attribute.key)
		pending_value = self.process_text(attribute.value)

		key_seq = isinstance(pending_key, T.text_sequence)
		value_seq = isinstance(pending_value, T.text_sequence)

		#TBD - ruleset for the combinations

		if key_seq and value_seq:
			#Should both be allowed?
			raise NotImplementedError('Both key and value of attribute is text_sequence')
		elif key_seq and not value_seq:
			#If only key is a sequence we might want to do one of two things
			#Either we want to define a placeholder for a specific attribute and don't care about the value
			#Or perhaps we just want to do a literal processing of the key
			#Until we have decided on this, this will not be supported
			raise NotImplementedError('Decision has not been made for dealing with attributes where the key is the text_sequence')
		elif value_seq and not key_seq:
			#Here we are simply replacing a value
			return T.attribute(attribute.key, pending_value)
		else:
			#No change
			return attribute

	def data(self, data):
		return T.data(self.process_text(data.value))

	def comment(self, comment):
		return T.comment(self.process_text(comment.value))

	def process_text(self, text):

		pending = T.text_sequence()

		for token, match in re_tokenizer(text, self.tokenization_rules, unmatched=TOKEN.text):

			if token is TOKEN.text:
				pending.sequence.append(match)
			elif token is TOKEN.variable:
				pending.sequence.append(T.placeholder(match.group(1)))
			else:
				raise TypeError(match)

		#Check if we had any changes or not
		if len(pending.sequence) == 1 and isinstance(pending.sequence[0], str):
			return text

		return pending


	def __post_init__(self):
		self.tokenization_rules = dict()

		if self.template_pattern:
			self.tokenization_rules[re.compile(self.template_pattern)] = TOKEN.template

		if self.variable_pattern:
			self.tokenization_rules[re.compile(self.variable_pattern)] = TOKEN.variable


def templates_from_xml_filename(filename):
	xml = local_xml_from_filename(filename).filter(template_configuration(
		template_pattern = r'_T_(.*)',
		variable_pattern = r'_V_(.*)',
		process_nodes = True,
		process_attributes = True,
		process_data = True,
		process_comments = True,
	))

	return T.template_collection(xml)