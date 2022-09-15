from pygraphml import GraphMLParser

parser = GraphMLParser()
g = parser.parse('data/test1.graphml')

parser.write(g, 'out/pygraphml1.graphml')

