#This is a separate line of testing where we try out using the xmlschema library

import urllib.request

urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPHandler(debuglevel=1)))

import xmlschema

schema = xmlschema.XMLSchema('http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd')

exit()


# print('storing')
# import pickle
# with open('schema-cache.pickled', 'wb') as outfile:
# 	pickle.dump(schema, outfile)

# print('done')

import pickle
with open('schema-cache.pickled', 'rb') as infile:
	schema = pickle.load(infile)


print(schema.to_dict('data/test2.graphml'))


#This is weird.. we are getting an error where raised is not an allowed property of y:BorderStyle