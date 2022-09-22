def is_type(item, type_or_tuple):
	item_type = type(item)
	if isinstance(type_or_tuple, (tuple, list)):
		for sub_type in type_or_tuple:
			if item_type is sub_type:
				return True
	else:
		if item_type is type_or_tuple:
			return True

	return False


def is_subclass(item, type_or_tuple):
	return isinstance(item, type) and issubclass(item, type_or_tuple)
