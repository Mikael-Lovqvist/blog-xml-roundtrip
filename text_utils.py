
from xml_types import symbol

UNMATCHED = symbol('UNMATCHED')

def re_tokenizer(text, matchers, start=0, include_unmatched=True, unmatched=UNMATCHED):
	pos = start

	while True:

		pending_best_match = None
		for pattern, token in matchers.items():
			if match := pattern.search(text, pos):
				if pending_best_match is None or match.start() < pending_best_match.start():
					pending_best_match = match
					pending_best_token = token

					if match.start() == pos:	#early bail
						break
		if pending_best_match:

			head = text[pos:pending_best_match.start()]
			if head and include_unmatched:
				yield unmatched, head

			yield pending_best_token, pending_best_match

			if pos == pending_best_match.end():	#Advance one position for null sized matches
				pos += 1
			else:
				pos = pending_best_match.end()
		else:
			tail = text[pos:]
			if tail and include_unmatched:
				yield unmatched, tail

			break

