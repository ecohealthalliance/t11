"""
Example annotation database queries
"""
import requests
from templater import make_template
import config

def print_result(result):
    result.raise_for_status()
    for binding in result.json()['results']['bindings']:
        for key, value in binding.items():
            raw_val = value['value']
            print "[" + key + "]"
            # Check for the delimiter used to combine results in a "group by" query group.
            if ";;" in raw_val:
                print raw_val.split(";;")
                continue
            # If the value references an annotation, query it and display
            # the full text.
            if raw_val.startswith('http://www.eha.io/types/annotation/'):
                query = make_template("""
                prefix anno: <http://www.eha.io/types/annotation_prop/>
                prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
                prefix pro: <http://www.eha.io/types/promed/>
                SELECT ?phraseStart ?phraseEnd ?prepStart ?sourceText
                WHERE {
                    <{{annotation_uri}}> anno:start ?phraseStart
                        ; anno:end ?phraseEnd
                        ; anno:source_doc/pro:text ?sourceText
                }
                """).render(annotation_uri=raw_val)
                result = requests.post(config.SPARQLDB_URL + "/query", data={"query":query})
                bindings = result.json()['results']['bindings']
                if len(bindings) == 0:
                    print "Could not resolve source text for:"
                    print key, raw_val
                for binding in bindings:
                    text = binding['sourceText']['value']
                    start = int(binding['phraseStart']['value'])
                    end = int(binding['phraseEnd']['value'])
                    print text[start:end]
            else:
                print raw_val
            print ""
        print "~~--~~--~~"

if __name__ == '__main__':
    print "Prepositions containing a location name"
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query":"""
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
    SELECT ?phrase ?prep
    WHERE {
        ?phrase dep:prep ?prep .
        ?prep anno:start ?start1 ;
            anno:end ?end1 .
        ?s2 anno:root/anno:entity_type "GPE" ;
            anno:start ?start2 ;
            anno:end ?end2 .
        ?phrase anno:source_doc ?same_source .
        ?s2     anno:source_doc ?same_source
        FILTER ( ?start2 >= ?start1 && ?end2 <= ?end1 )
    }
    """}, headers={"Accept":"application/sparql-results+json" })
    print_result(result)
    
    print "Most frequent nouns"
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query":"""
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
    prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?word
        # (group_concat(DISTINCT ?s;separator=";;") as ?subjects)
        (count(?s) as ?count)
    WHERE {
        ?s anno:root ?r .
        ?r anno:pos "NOUN" ;
           rdf:label ?word .
    }
    GROUP BY ?word
    ORDER BY DESC(?count)
    LIMIT 10
    """}, headers={"Accept":"application/sparql-results+json" })
    print_result(result)
    
    print "Most common dependency relations around the given word:"
    # This could be useful for finding patterns in how certain types of words
    # are used.
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query":"""
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
    prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?p ?p2
        (sample(?o) as ?example)
        (count(?s) as ?count)
    WHERE {
        ?s anno:root/rdf:label "fever" .
        ?o ?p ?s .
        OPTIONAL {
            ?o ?p2 ?s2 .
            ?p2 rdf:type anno:dependency_relation .
            FILTER(?s != ?s2)
        } .
        ?p rdf:type anno:dependency_relation
    }
    GROUP BY ?p ?p2
    ORDER BY DESC(?count)
    LIMIT 10
    """}, headers={"Accept":"application/sparql-results+json" })
    print_result(result)
    
    print "Outbreak types"
    # This could be useful for identifying infectious agents which
    # often appear in the "compound" dependencies on the word "outbreak"
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query":"""
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
    prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?outbreakP ?outbreakType
    WHERE {
        ?outbreakP anno:root/rdf:label "outbreak"
            ; dep:compound ?outbreakType
    }
    """}, headers={"Accept":"application/sparql-results+json" })
    print_result(result)
    
    print "Attributes of subjects"
    # Possibly useful for fact extraction.
    # However, coreference resolution is needed in most cases.
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query":"""
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
    SELECT ?nsubj ?phrase ?attr
    WHERE {
        ?phrase dep:attr ?attr
            ; dep:nsubj ?nsubj
    }
    """}, headers={"Accept":"application/sparql-results+json" })
    print_result(result)
    
    print "Compound subjects"
    print_result(requests.post(config.SPARQLDB_URL + "/query", data={"query":"""
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
    prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?subject
    WHERE {
        ?subject dep:compound/dep:compound ?c
    }
    """}, headers={"Accept":"application/sparql-results+json" }))
