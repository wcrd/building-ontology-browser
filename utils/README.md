### About
As of the current version of Brick (v1.3.0) there are a number of main 'categories' of items that we are interested in; namely:
* Classes
* Relationships
* EntityProperties

The Brick ontology also contains a number of other definitions within it:
* Units (qudt)
* Shapes
* Tags (BrickTag)
* Blank Nodes (properties on definitions)

---

For our reference purposes, we are only interested in the items listed in the first section above. Given the Brick ontology, we need to filter out that which we do not care to put into our reference website. 

The methods of filtering are described below.

#### Filtering the Graph
First we extract all unique subjects from the Brick/Switch graph into a list of `subjects`. We then filter out subjects we do not need.

We will first cover **excluding items**.
1. **BNodes**
   Blank Nodes are not useful to our ontology reference website. To filter these out we can just remove subjects based on their type.
   Proper subjects will be of type `rdflib.term.URIref`, where BNodes will be of type `rdflib.term.BNode`. We can use this property to filter.
   ```python
   filter(lambda x: not isinstance(x, rdflib.term.BNode), subjects)
   ```
2. **Units**
   Units are part of the `http://qudt.org/vocab/unit/` namespace. We can filter these out using this sudo code expression:
   ```python
   filter(lambda x: <<x.namespace>> != <<namespace_manager>>['qudt'], subjects)
   ```

3. **Tags**
   Tags are all part of the BrickTag (prefix: `tag`) namespace. Just like Units we can use this to filter them out. 
   ```python
   filter(lambda x: <<x.namespace>> != <<namespace_manager>>['tag'], subjects)
   ```

4. **Shapes**
   Subjects can be both a Class and a Shape. In this case they are principally valid classes which have an associated validation/definition shape, and we need to include them in our reference website (I think). There is some ambiguity around these in the Brick Ontology. My current strategy is:
   * If type is both `Owl.Class` and `SH.NodeShape`
     * If subject term contains `Shape`, put into shapes grouping. [Actually going to just exclude for now]
     * If subject term does not contain `Shape`, treat as a normal class.
   * Still deciding whether to keep all shapes in here; currently they are not really useful to us.

   We really just want to exclude (or group) Shapes which are pure shapes, that is are only of type `sh:NodeShape`
   Luckily for us, Brick puts these into a separate namespace `BrickShape` (prefix: `bsh`) which we can filter out using the same methods as above.
   ```python
   filter(lambda x: <<x.namespace>> != <<namespace_manager>>['bsh'], subjects)
   ```

Now we will cover **including items**.

Now that our subject list is reduced, we can work on generating the reference file.
In the interests of covering all bases, we also only select items that meet our criteria to include. This probably isn't necessary after our filtering work above, but it is done just to make sure we don't include anything we have overlooked.

1. **Classes**
   Classes are easy, in that their type will be `rdflib.OWL.Class`. We can use this to get all remaining valid class based subjects.
2. **Relationships**
   These are a little more tricky. Generally relationships are defined as the following combination of types: `rdflib.OWL.ObjectProperty`, `rdflib.OWL.AsymmetricProperty`, `rdflib.OWL.IrreflexiveProperty`. Now it is possible for some relationships to vary on the last two types, but currently all relationships are defined as a `rdflib.OWL.ObjectProperty`. We can use this to get all valid relationship based subjects.

We can achieve the above using an expression similar to:
```python
filter(lambda x: x in [rdflib.OWL.Class, rdflib.OWL.ObjectProperty], s_class)
```


#### Clean-up
Some brick definitions are subclasses of both brick classes (what we want) AND other classes from other ontologies (which we don't want). These other ontologies typically represent physics or graph type classification information that is not relevant to our uses on this website. The multiple parentage results in split pathways that clutter our hierarchy. The external class pathways we want to remove are:
* sosa:ObservableProperty
* sosa:FeatureOfInterest
* skos:Concept
  
These classes are where pathways will terminate (as we can't ever traverse further than them is we only use the Brick and Switch ontologies because the definitions for them are not included, hence we cannot traverse past them). This makes it quite simple for us to filter them out of the final dataset:

```python
# Some split pathways end at sosa:ObservableProperty, sosa:FeatureOfInterest, skos:Concept. We are not interested in these and are going to remove objects that terminate there.
final_data = [item for item in data if item['path']['full'][0] not in [rdflib.SSN.ObservableProperty, rdflib.SSN.FeatureOfInterest, rdflib.SKOS.Concept]]
```

In addition, all Brick Relationship definitions are a subclass of owl:ObjectProperty (as stated in section above). As per prior cleanup section, we do not include the ontology files for these other ontologies and thus we will not resolve the 'term', 'namespace', 'description' etc fields that we provide for the other class records in the final data object. In order to make this look good on the workspace we are just going to manually inject the appropriate objects for the following external classes:
1. owl:ObjectProperty
