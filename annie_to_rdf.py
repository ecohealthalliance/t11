#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This iterates over stored articles loading their annie annotations
into a SPARQL DB.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
from templater import make_template
import sparql_utils
import hashlib
from epitator.annotator import AnnoDoc
from epitator.keyword_annotator import KeywordAnnotator
from epitator.geoname_annotator import GeonameAnnotator
import re
from pylru import lrudecorator

annotators = [
    KeywordAnnotator(),
    GeonameAnnotator(),
]

# Test that the keyword annotator is set up correctly
test_doc = AnnoDoc("ebola influenza glanders dermatitis")
for annotator in annotators:
    test_doc.add_tier(annotator)
assert(
    set(disease.label for disease in test_doc.tiers["diseases"].spans) -
    set("ebola influenza glanders dermatitis".split(" ")) == set())

@lrudecorator(500)
def resolve_keyword(keyword):
    query = make_template("""
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
    prefix obo: <http://purl.obolibrary.org/obo/>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?entity
    WHERE {
        BIND (obo:DOID_4 AS ?disease)
        ?entity rdfs:subClassOf* ?disease .
        ?entity oboInOwl:hasNarrowSynonym|oboInOwl:hasRelatedSynonym|oboInOwl:hasExactSynonym|rdfs:label ?label
        FILTER regex(?label, "^({{keyword | escape}})$", "i")
    }
    """).render(
        keyword=re.escape(keyword)
    )
    resp = sparql_utils.query(query)
    bindings = resp.json()['results']['bindings']
    if len(bindings) == 0:
        print("no match for", keyword.encode('ascii', 'xmlcharrefreplace'))
    elif len(bindings) > 1:
        print("multiple matches for", keyword.encode('ascii', 'xmlcharrefreplace'))
        print(bindings)
    return [binding['entity']['value'] for binding in bindings]

def create_annotations(article_uri, content):
    annotated_doc = AnnoDoc(content)
    for annotator in annotators:
        annotated_doc.add_tier(annotator)
    def get_span_uri(span):
        h = hashlib.md5()
        h.update(article_uri)
        h.update(str(span.start) + ':' + str(span.end))
        return "http://www.eha.io/types/annotation/annie/span/" + str(h.hexdigest())
    for tier_name in ['geonames', 'diseases', 'hosts', 'modes', 'pathogens', 'symptoms']:
        tier = annotated_doc.tiers[tier_name]
        update_query = make_template("""
        prefix anno: <http://www.eha.io/types/annotation_prop/>
        prefix eha: <http://www.eha.io/types/>
        prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
        prefix dc: <http://purl.org/dc/terms/>
        {% for span in spans %}
        INSERT DATA {
            <{{get_span_uri(span)}}> anno:annotator eha:annie
                {% if span.geoname %}
                    ; rdf:type eha:geoname_annotation
                    ; anno:geoname <http://sws.geonames.org/{{span.geoname.geonameid}}>
                {% else %}
                    ; rdf:type eha:keyword_annotation
                    ; anno:category "{{tier_name}}"
                {% endif %}
                ; anno:label "{{span.label | escape}}"
                ; anno:source_doc <{{source_doc}}>
                ; anno:start {{span.start}}
                ; anno:end {{span.end}}
                ; anno:selected-text "{{span.text | escape}}"
        } ;
        {% if tier_name == "diseases" %}
            INSERT DATA {
                {% for entity_uri in resolve_keyword(span.label) %}
                     <{{entity_uri}}> dc:relation <{{get_span_uri(span)}}> .
                {% endfor %}
            } ;
        {% endif %}
        {% endfor %}
        INSERT DATA {
            <{{source_doc}}> anno:annotated_by eha:annie_1
        }
        """).render(
            get_span_uri=get_span_uri,
            resolve_keyword=resolve_keyword,
            source_doc=article_uri,
            tier_name=tier_name,
            spans=tier.spans)
        sparql_utils.update(update_query)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max_items", default="-1"
    )
    args = parser.parse_args()
    max_items = int(args.max_items)
    query_template = make_template("""
    prefix con: <http://www.eha.io/types/content/>
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix eha: <http://www.eha.io/types/>
    SELECT ?item_uri ?content
    WHERE {
        ?item_uri con:text ?content
        # FILTER(strstarts(str(?item_uri), "http://t11.tater.io/documents/"))
        FILTER NOT EXISTS {
            ?item_uri anno:annotated_by eha:annie_1
        }
    }
    ORDER BY rand()
    LIMIT 100
    """)
    items_processed = 0
    while max_items < 0 or items_processed < max_items:
        print("Items processed: ", str(items_processed))
        result = sparql_utils.query(query_template.render())
        bindings = result.json()['results']['bindings']
        if len(bindings) == 0:
            print("No more results")
            break
        else:
            items_processed += len(bindings)
            for binding in bindings:
                item_uri = binding['item_uri']['value']
                content = binding['content']['value']
                print("Annotating ", item_uri)
                create_annotations(item_uri, content)
