"""
This adds some relationships to the dataset for making queries simpler and/or more efficient.
"""
import requests
from templater import make_template
import config
import datetime

prefixes = """
prefix pro: <http://www.eha.io/types/promed/>
prefix anno: <http://www.eha.io/types/annotation_prop/>
prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
prefix dc: <http://purl.org/dc/terms/>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix eha: <http://www.eha.io/types/>
"""
if __name__ == '__main__':
    start = datetime.datetime.now()
    print "Computing containment relationships between keyword annotations and depency parse annotations..."
    update_query = prefixes+"""
    INSERT { ?p1 anno:contains ?p2 }
    WHERE {
        ?p1 anno:start ?p1start
            ; anno:end ?p1end
            ; anno:source_doc ?same_source
            .
        ?dep_rel a anno:dependency_relation .
        ?parent ?dep_rel ?p1 .
        ?p2 anno:start ?p2start
            ; anno:end ?p2end
            ; anno:source_doc ?same_source
            ; anno:category "diseases"
            .
        FILTER ( ?p1start <= ?p2start && ?p1end >= ?p2end )
        FILTER (?p1 != ?p2)
    }
    """
    resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
    resp.raise_for_status()
    print "Finished in", datetime.datetime.now() - start
    start = datetime.datetime.now()
    print "Computing minimal containment relationships..."
    # I.e. the containing element contains no elements that contain object.
    update_query = prefixes+"""
    INSERT { ?p1 anno:min_contains ?target }
    WHERE {
        ?p1 anno:contains ?target
            ; anno:start ?p1start
            ; anno:end ?p1end
            .
        FILTER NOT EXISTS {
            ?p2 anno:contains ?target
                ; anno:start ?p2start
                ; anno:end ?p2end
                .
            FILTER (?p1 != ?p2)
            FILTER (?p2end - ?p2start < ?p1end - ?p1start)
        }
    }
    """
    resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
    resp.raise_for_status()
    print "Finished in", datetime.datetime.now() - start
    start = datetime.datetime.now()
    print "Testing query speed without containment predicate..."
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query":prefixes+"""
    SELECT ?p1 ?p2
    WHERE {
        ?p1 anno:start ?p1start
            ; anno:end ?p1end
            ; anno:source_doc ?same_source
            .
        ?dep_rel a anno:dependency_relation .
        ?parent ?dep_rel ?p1 .
        ?p2 anno:start ?p2start
            ; anno:end ?p2end
            ; anno:source_doc ?same_source
            ; anno:category "diseases"
            .
        FILTER ( ?p1start <= ?p2start && ?p1end >= ?p2end )
        FILTER (?p1 != ?p2)
    }
    """}, headers={"Accept":"application/sparql-results+json" })
    print "Finished in", datetime.datetime.now() - start
    start = datetime.datetime.now()
    print "Testing query speed with containment predicate..."
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query":prefixes+"""
    SELECT ?p1 ?p2
    WHERE {
        ?p1 anno:contains ?p2
    }
    """}, headers={"Accept":"application/sparql-results+json" })
    print "Finished in", datetime.datetime.now() - start
