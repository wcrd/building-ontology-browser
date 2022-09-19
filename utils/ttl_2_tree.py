'''
@wcrd
This script processes a ttl file and builds a ag-grid formatted tree view data source
'''

#### NOT IN USE / NOT COMPLETE

import rdflib

## INPUT FILES
SWITCH_PATH = "./data/ontology/switch.ttl"
BRICK_PATH = "./data/ontology/brick.ttl"


## LOAD FILES INTO GRAPH
print("\nLoading TTLs\n\n")
ds = rdflib.Dataset(default_union=True)
# Generic namespace I am going to use to name the graphs
ds_ns = rdflib.Namespace("https://_graph_.com#")
# lets load it with data from brick and switch.
# this will add graph if it doesn't exist, or return the existing one.
# could also do this independently using add_graph() method.
ds.graph(ds_ns['brick']).parse(BRICK_PATH, format='turtle');
ds.graph(ds_ns['switch']).parse(SWITCH_PATH, format="turtle");

# check that graphs created.
contexts = ds.graphs()
print(f"Total DS entries: {len(ds)}")
print("Graphs created:")
for c in contexts:
    print(f"{c} ---- Entries: {len(ds.graph(c))}")


# PARSE GRAPHS TO BUILD OUTPUT DATA
triples = list(ds.triples((None,None,None)))
print(len(triples))