"""
This adds some relationships to the dataset for making queries simpler and/or more efficient.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from templater import make_template
import sparql_utils
import datetime

prefixes = """
prefix anno: <http://www.eha.io/types/annotation_prop/>
prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
prefix dc: <http://purl.org/dc/terms/>
prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix eha: <http://www.eha.io/types/>
prefix pro: <http://www.eha.io/types/promed/>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
"""

containment_query_template = make_template(prefixes+"""
INSERT { ?p1 anno:contains ?p2 }
WHERE {
    ?p1 anno:start ?p1start
    ; anno:end ?p1end
    ; anno:source_doc ?same_source
    .
    ?dep_rel rdf:type anno:dependency_relation .
    ?parent ?dep_rel ?p1 .
    ?p2 anno:start ?p2start
    ; anno:end ?p2end
    ; anno:source_doc ?same_source
    ; anno:category "diseases"
    .
    ?same_source pro:post/pro:date ?source_date .
    FILTER ( ?p1start <= ?p2start && ?p1end >= ?p2end )
    FILTER (?p1 != ?p2)
    {% if min_date %}
        FILTER (?source_date >= "{{min_date | sparqlDate}}"^^xsd:dateTime)
    {% endif %}
    {% if max_date %}
        FILTER (?source_date < "{{max_date | sparqlDate}}"^^xsd:dateTime)
    {% endif %}
}
""")

if __name__ == '__main__':
    import argparse
    import dateutil.parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-debug', action='store_true')
    parser.add_argument(
        "--last_n_days", default=None
    )
    parser.add_argument(
        "--from_date", default=None
    )
    args = parser.parse_args()
    min_date = datetime.datetime(year=1994, month=1, day=1)
    if args.last_n_days:
        min_date = datetime.datetime.now() - datetime.timedelta(int(args.last_n_days))
    elif args.from_date:
        min_date = dateutil.parser.parse(args.from_date)
    interval = datetime.timedelta(3)
    start = datetime.datetime.now()
    print("Computing containment relationships between keyword annotations and depency parse annotations...")
    while min_date <= datetime.datetime.now():
        print("Current date", min_date)
        resp = sparql_utils.update(containment_query_template.render(
            min_date=min_date,
            max_date=min_date+interval))
        min_date += interval
    print("Finished in", datetime.datetime.now() - start)
    start = datetime.datetime.now()
    print("Computing minimal containment relationships...")
    # I.e. the containing element contains no elements that contain object.
    query = prefixes+"""
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
    resp = sparql_utils.update(query)
    print("Finished in", datetime.datetime.now() - start)
    if args.debug:
        start = datetime.datetime.now()
        print("Testing query speed without containment predicate...")
        query = prefixes+"""
        SELECT ?p1 ?p2
        WHERE {
            ?p1 anno:start ?p1start
                ; anno:end ?p1end
                ; anno:source_doc ?same_source
                .
            ?dep_rel rdf:type anno:dependency_relation .
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
        resp = sparql_utils.query(query)
        print("Finished in", datetime.datetime.now() - start)
        start = datetime.datetime.now()
        print("Testing query speed with containment predicate...")
        query = prefixes+"""
        SELECT ?p1 ?p2
        WHERE {
            ?p1 anno:contains ?p2
        }
        """
        resp = sparql_utils.query(query)
        print("Finished in", datetime.datetime.now() - start)
