from rdflib import Graph, OWL, RDF, RDFS

g = Graph()
g.parse('examples/imports_demo/core_ontology.ttl')
print(f'Total triples: {len(g)}')

print('Classes (owl:Class):')
for s in g.subjects(RDF.type, OWL.Class):
    print(f'  {s}')

print('Properties (owl:DatatypeProperty):')
for s in g.subjects(RDF.type, OWL.DatatypeProperty):
    print(f'  {s}')

print('Properties (owl:ObjectProperty):')
for s in g.subjects(RDF.type, OWL.ObjectProperty):
    print(f'  {s}')
