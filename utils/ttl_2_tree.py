# %%
'''
@wcrd
This script processes a ttl file and builds a ag-grid formatted tree view data source
'''

import rdflib
from typing import Tuple, List
import json

# %%

## INPUT FILES
SWITCH_PATH = "./data/ontology/switch.ttl"
BRICK_PATH = "./data/ontology/brick.ttl"

# %% [markdown]
# ### LOAD INTO GRAPH

# %%

## LOAD FILES INTO GRAPH
ds = rdflib.Dataset(default_union=True)
# Generic namespace I am going to use to name the graphs
ds_ns = rdflib.Namespace("https://_graph_.com#")
# lets load it with data from brick and switch.
# this will add graph if it doesn't exist, or return the existing one.
# could also do this independently using add_graph() method.
ds.graph(ds_ns['brick']).parse(BRICK_PATH, format='turtle');
ds.graph(ds_ns['switch']).parse(SWITCH_PATH, format="turtle");


# %%
# generate namespaces
ds_g_ns = dict(ds.namespaces())
# check that graphs created.
contexts = ds.graphs()
print(f"Total DS entries: {len(ds)}")
print("Graphs created:")
for c in contexts:
    print(f"{c} ---- Entries: {len(ds.graph(c))}")

# %% [markdown]
# ### GENERATE TREE

# %%
# URI PROCESSOR
def uri_spliter(uri: rdflib.term.URIRef, ns: dict = {}) -> Tuple[str, str, str]:
    '''
    Given a URI, split into namespace and term.
    If a ns dict is given, return the prefix for that namespace as well
    (ns, term, prefix)
    '''
    try:
        chunks = uri.toPython().split("#")
        if len(chunks) == 1:
            # no # found, lets try spliting on last / (i.e. QUDT uses this system)
            chunks = uri.toPython().rsplit("/", 1)
        namespace = chunks[0]
        term = chunks[1]
    except IndexError:
        print(f"URI did not resolve into parts: {uri}")
        return (None,None,None)
    except:
        raise ValueError(f"Error parsing URI: {uri}")
    
    if ns:
        try:
            prefix = next(key for key, value in ns.items() if value.toPython() in [f"{namespace}#", f"{namespace}/"])
            return (namespace, term, prefix)
        except StopIteration:
            pass
    
    return (namespace, term, None)


# %%
# PARSE GRAPHS TO BUILD OUTPUT DATA
# get list of subjects to include in our reference file
subjects = ds.subjects()
# filter out BNodes
subjects = set(filter(lambda x: not isinstance(x, rdflib.term.BNode), subjects))
# filter out all 'Brick Tags'
subjects = list(filter(lambda x: f"{uri_spliter(x)[0]}#" != ds_g_ns['tag'].toPython(), subjects))
# filter out all true Shapes
subjects = list(filter(lambda x: f"{uri_spliter(x)[0]}#" != ds_g_ns['bsh'].toPython(), subjects))
# filter out Unit definitions
subjects = list(filter(lambda x: f"{uri_spliter(x)[0]}/" != ds_g_ns['unit'].toPython(), subjects))

print(len(subjects))

# %%
#### Path Generating Functions

def get_class_heirarchy(class_uri, graph, base_level = 1, depth_limit=15, initial_path=[]):
    '''
    :base_level: how far down the class heirarchy to return as 'base'. base_level=0 is the root (for brick, this is simply 'Class')
    '''
    depth = 0
    # # get type of entity
    # entity_class = list(graph.objects(entity, rdflib.RDF.type))
    # if len(entity_class)==0:
    #     raise ValueError(f"No class found in graph for entity {entity}.")

    # Check Class exists
    if (class_uri, None, None) not in graph:
        raise ValueError(f"No class found in graph for class {class_uri}.")

    path = _climb_class_heirarchy(class_uri, graph, depth_limit, depth, initial_path)

    try:
        # return path[base_level]
        return path
    except IndexError:
        print(f"Requested base level {base_level} does not exist. Returning level 0 instead")
        return path[0]


def _climb_class_heirarchy(entity_class, graph, depth_limit, depth, path=[]) -> list:
    '''
    Path is used for storing the journey to the root class. Users can request base class at level {n}. Base of all classes is 'Class' which is level 0.
    '''
    # guard
    if depth >= depth_limit:
        raise RecursionError(f"Max depth of {depth_limit} reached. Increase depth_limit parameter if required.")

    # add current class to path
    path = [entity_class] + path

    # get parent
    parents = list(graph.objects(entity_class, rdflib.RDFS.subClassOf))
    # filter out BNodes - they are not useful to us here. We want explicit class definitions only.
    parents = list(filter(lambda x: not isinstance(x, rdflib.term.BNode), parents))
    
    # take each path and climb
    if len(parents)==0:
        # print("I'm done with this path. Returning: ")
        # print([path])
        return [path]
    else:
        paths = []
        for p in parents:
            new_paths = _climb_class_heirarchy(p, graph, depth_limit, depth+1, path)
            for new_path in new_paths:
                paths.append(new_path)
    return paths

# %%
# PATH FORMATTER (SIMPLIFIER)
def path_2_termString(path: List[rdflib.term.URIRef]) -> List[str]:
    '''
    Given a list of URIRefs, resolve to a list of term strings (no namespace)
    '''
    output = []
    for uri in path:
        _, term, _ = uri_spliter(uri)
        output.append(term)
    
    return output


# %%
# generate path data and data row
data = []
for idx, s in enumerate(subjects):
    namespace, term, prefix = uri_spliter(s, ds_g_ns)


    ### GOING TO SKIP THIS FOR NOW AND JUST PROCESS ENTITIES IF THEY ARE A CLASS DEFINTION OR OBJECT PROPERTY (relationships).
    ### TODO: Come back and update this to handle shapes, entityProperties, etc.

    # # Check type -> If Class, then get class path. If instance, get class, then get class path
    # # need to filter self out
    # s_class = list(filter(lambda x: x != s, ds.objects(s, rdflib.RDF.type)))
    # if len(s_class)==0:
    #     raise ValueError(f"No class found in graph for entity {s}.")
    # elif len(s_class) > 1:
    #     # raise ValueError(f"Too many types exist for the class. Please review: {s}.")
    #     print(f"Too many types exist for the class. SKIPPING. Please review: {s}.")
    #     continue
    # else:
    #     if s_class[0] != rdflib.OWL.Class:
    #         # Set this as first path item
    #         initial_path = s_class
    #     else: 
    #         initial_path = []

    ### BASIC VERSION
    # Get subject type(s) [filter self out]
    s_class = list(filter(lambda x: x != s, ds.objects(s, rdflib.RDF.type)))
    # filter down to only owl.class and owl.objectproperty, and sh:NodeShape so we can remove it -> these are what we will process
    s_class = list(filter(lambda x: x in [rdflib.OWL.Class, rdflib.OWL.ObjectProperty, rdflib.SH.NodeShape], s_class))
    
    if len(s_class)==0:
        print(f"No class found in graph for entity {s}. \nSKIPPING")
        continue

    if rdflib.SH.NodeShape in s_class:
        # OLD. We are excluding this now
        # # fixed path
        # paths = [[rdflib.SH.NodeShape, s]]

        # NEW
        # if the name term contains shape, skip it. Else treat it as a class.
        if "Shape" in term:
            print(f"Not progressing: {s}")
            continue
        else:
            s_class.remove(rdflib.SH.NodeShape)


    if s_class[0] != rdflib.OWL.Class:
        # If not a class then 
        paths = [[*s_class, s]]
    else:
        paths = get_class_heirarchy(s, ds)

    # Get description
    desc = list(ds.objects(s, rdflib.SKOS.definition))
    if len(desc) == 0: desc=""
    else: desc = desc[0]

    #if multiple paths, make multiple rows.
    for p_idx, path in enumerate(paths):
        data.append({
            "uri": s,
            "namespace": namespace,
            "prefix": prefix,
            "term": term,
            "desc": desc,
            "path": {
                "full": path,
                "agGridPath": path_2_termString(path)
            },
            "idx": f"{idx}.{p_idx}"
        })


# %% [markdown]
# ### CLEAN UP

# %%
### FINAL FILTERING
# Some split pathways end at sosa:ObservableProperty, sosa:FeatureOfInterest, skos:Concept. We are not interested in these and are going to remove objects that terminate there.
final_data = [item for item in data if item['path']['full'][0] not in [rdflib.SSN.ObservableProperty, rdflib.SSN.FeatureOfInterest, rdflib.SOSA.ObservableProperty, rdflib.SOSA.FeatureOfInterest, rdflib.SKOS.Concept]]

# %% [markdown]
# ### MANUAL DATA INJECTION
# Any objects that are needed for the website but that are not defined in provided ontology files. Generally just some high level rdf definition classes.

# %%
# Get last idx
# We can just manually write these for now as the idx range '0.x' is free.
# idx = int(float(final_data[-1]["idx"]))

# Add owl:ObjectProperty
# idx += 1
final_data.append({
    "uri": "http://www.w3.org/2002/07/owl#ObjectProperty",
    "namespace": "http://www.w3.org/2002/07/owl",
    "prefix": "owl",
    "term": "ObjectProperty",
    "desc": "A property axiom defines characteristics of a property. In its simplest form, a property axiom just defines the existence of a property. Object properties link individuals to individuals.",
    "path": {
      "full": [
        "http://www.w3.org/2002/07/owl#ObjectProperty"
      ],
      "agGridPath": [
        "ObjectProperty"
      ]
    },
    "idx": "0.1"
})

# %% [markdown]
# ### EXPORT

# %%
with open("data.json", "w") as f:
    json.dump(final_data, f, indent=2)
