"""
Compare accuracty of computer annotations to human annotations
"""
import requests
from templater import make_template
import config

prefixes = """
prefix anno: <http://www.eha.io/types/annotation_prop/>
prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
prefix dc: <http://purl.org/dc/terms/>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
prefix eha: <http://www.eha.io/types/>
prefix tater: <http://www.eha.io/types/tater/>
"""
if __name__ == '__main__':
    result = requests.post(config.SPARQLDB_URL + "/query", data={"query": prefixes + """
    SELECT
        ?overlap
        (count(DISTINCT ?annotation1) AS ?correctAnnotations)
        (count(DISTINCT ?annotation2) AS ?selectedAnnotations)
    WHERE {
        ?annotation1 anno:annotator eha:tater
            ; anno:start ?start1
            ; anno:end ?end1
            ; anno:source_doc ?source
            #; tater:code/rdfs:label "Disease/Condition/Symptom Set/Illness"
            #; tater:code/tater:header/rdfs:label "Roles"
            .
        ?annotation2 anno:annotator eha:annie
            ; anno:category "diseases"
            ; anno:start ?start2
            ; anno:end ?end2
            ; anno:source_doc ?source
            .
        # The annotations overlap
        BIND((?start1 >= ?start2 && ?start1 <= ?end2) || (?start2 >= ?start1 && ?start2 <= ?end1) AS ?overlap)
    } GROUP BY ?overlap
    """}, headers={"Accept":"application/sparql-results+json" })
    result.raise_for_status()
    stats = {}
    for binding in result.json()['results']['bindings']:
        if binding['overlap']['value'] == 'false':
            stats['tpfp'] = int(binding['selectedAnnotations']['value'])
            stats['tpfn'] = int(binding['correctAnnotations']['value'])
        else:
            stats['tp'] = int(binding['correctAnnotations']['value'])
    stats['precision'] = float(stats['tp']) / stats['tpfp']
    stats['recall'] = float(stats['tp']) / stats['tpfn']
    stats['f1'] = 2 * stats['precision'] * stats['recall'] / (stats['precision'] + stats['recall'])
    for key, value in stats.items():
        print key + ": " + str(value) 
