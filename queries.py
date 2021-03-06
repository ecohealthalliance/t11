"""
Example annotation database queries
"""
from templater import make_template
import sparql_utils

prefixes = """
prefix pro: <http://www.eha.io/types/promed/>
prefix anno: <http://www.eha.io/types/annotation_prop/>
prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
prefix dc: <http://purl.org/dc/terms/>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
prefix eha: <http://www.eha.io/types/>
"""
def print_result(result):
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
                prefix con: <http://www.eha.io/types/content/>
                SELECT ?phraseStart ?phraseEnd ?prepStart ?sourceText
                WHERE {
                    <{{annotation_uri}}> anno:start ?phraseStart
                        ; anno:end ?phraseEnd
                        ; anno:source_doc/con:text ?sourceText
                }
                """).render(annotation_uri=raw_val)
                result = sparql_utils.query(query)
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
    print "Descriptors of resolved disease names"
    query = prefixes+"""
    SELECT ?parent ?target ?descriptor ?dep_rel ?rel ?pos
    WHERE {
        ?dep_rel rdf:type anno:dependency_relation .
        VALUES ?dep_rel { dep:amod dep:nmod }
        ?parent anno:min_contains ?target
            ; ?dep_rel ?descriptor
            .
        ?descriptor anno:start ?d_start
            ; anno:end ?d_end
            ; anno:root/anno:pos ?pos
            .
        FILTER (?pos NOT IN ("X", "PUNCT"))
        ?target anno:category "diseases"
            ; anno:start ?t_start
            ; anno:end ?t_end
            ; ^dc:relation ?rel
            .
        ?rel rdf:label "malaria" .
        # The descriptor is outside of the target
        FILTER ( ?d_end <= ?t_start || ?t_end <= ?d_start )
    } LIMIT 100
    """
    result = sparql_utils.query(query)
    print_result(result)
    print "Pathogens and the sentences they appear in"
    query = prefixes+"""
    SELECT ?phrase ?target
    WHERE {
        ?phrase anno:start ?p_start
            ; anno:end ?p_end
            ; dep:ROOT ?noop
            .
        ?target anno:category "pathogens"
            ; anno:start ?t_start
            ; anno:end ?t_end
            .
        ?phrase anno:source_doc ?same_source .
        ?target anno:source_doc ?same_source .
        FILTER ( ?t_start >= ?p_start && ?t_end <= ?p_end )
    } LIMIT 100
    """
    result = sparql_utils.query(query)
    print_result(result)
    print "Prepositions containing a location name"
    query = prefixes+"""
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
    """
    result = sparql_utils.query(query)
    print_result(result)
    print "Most frequent nouns"
    query = """
    SELECT ?word
        # (group_concat(DISTINCT ?s;separator=";;") as ?subjects)
        (count(?s) as ?count)
    WHERE {
        ?s anno:root ?r .
        ?r anno:pos "NOUN" ;
           rdfs:label ?word .
    }
    GROUP BY ?word
    ORDER BY DESC(?count)
    LIMIT 10
    """
    result = sparql_utils.query(query)
    print_result(result)
    print "Most common dependency relations around the given word:"
    # This could be useful for finding patterns in how certain types of words
    # are used.
    query = prefixes+"""
    SELECT ?p ?p2
        (sample(?o) as ?example)
        (count(?s) as ?count)
    WHERE {
        ?s anno:root/rdfs:label "fever" .
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
    """
    result = sparql_utils.query(query)
    print_result(result)
    print "Outbreak types"
    # This could be useful for identifying infectious agents which
    # often appear in the "compound" dependencies on the word "outbreak"
    query = prefixes+"""
    SELECT ?outbreakP ?outbreakType
    WHERE {
        ?outbreakP anno:root/rdfs:label "outbreak"
            ; dep:compound ?outbreakType
    }
    """
    result = sparql_utils.query(query)
    print_result(result)
    print "Attributes of subjects"
    # Possibly useful for fact extraction.
    # However, coreference resolution is needed in most cases.
    query = """
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
    SELECT ?nsubj ?phrase ?attr
    WHERE {
        ?phrase dep:attr ?attr
            ; dep:nsubj ?nsubj
    }
    """
    result = sparql_utils.query(query)
    print_result(result)
    print "Compound subjects"
    query = prefixes+"""
    SELECT ?subject
    WHERE {
        ?subject dep:compound/dep:compound ?c
    }
    """
    result = sparql_utils.query(query)
    print_result(result)