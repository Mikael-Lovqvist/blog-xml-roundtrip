from dataclasses import dataclass
import typing as T
from lxml import etree
import enum

class filter_context(enum.Enum):
	tag				= enum.auto()
	attribute		= enum.auto()
#	value			= enum.auto()
	data			= enum.auto()
	comment			= enum.auto()

class filter_operation(enum.Enum):
	ignore			= enum.auto()
	remove			= enum.auto()

#We define these operations outside because enum.Enum will try to turn it into an enum member otherwise.
@dataclass
class replace:
	replacement:	object

@dataclass
class amend:
	amendments:		object

filter_operation.replace = replace
filter_operation.amend = amend

#Remove them from this context
del replace, amend


@dataclass
class filter_configuration:
	tag: 		T.Callable = None
	attribute: 	T.Callable = None
#	value: 		T.Callable = None
	data: 		T.Callable = None
	comment: 	T.Callable = None



