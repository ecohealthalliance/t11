#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This iterates over stored articles loading their annie annotations
into a SPARQL DB. 
"""
import argparse
from templater import make_template
import requests
import hashlib
import config
from annotator.annotator import AnnoDoc
from annotator.keyword_annotator import KeywordAnnotator
from annotator.geoname_annotator import GeonameAnnotator
import re

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
    resp = requests.post(config.SPARQLDB_URL + "/query", data={
        "query": query
    }, headers={"Accept":"application/sparql-results+json" })
    resp.raise_for_status()
    bindings = resp.json()['results']['bindings']
    if len(bindings) == 0:
        print "no match for", keyword
    elif len(bindings) > 1:
        print "multiple matches for", keyword
        print bindings
    return [binding['entity']['value'] for binding in bindings]

def create_annotations(article_uri, annotated_doc):
    def get_span_uri(span):
        h = hashlib.md5()
        h.update(article_uri)
        h.update(str(span.start) + ':' + str(span.end))
        return "http://www.eha.io/types/annotation/annie/span/" + str(h.hexdigest())
    for tier_name, tier in annotated_doc.tiers.items():
        if tier_name.endswith("grams") or tier_name in ["tokens", "pos", "nes"]:
            continue
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
                ; anno:annotator eha:annie
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
            <{{source_doc}}> anno:annotated_by eha:annie
        }
        """).render(
            get_span_uri=get_span_uri,
            resolve_keyword=resolve_keyword,
            source_doc=article_uri,
            tier_name=tier_name,
            spans=tier.spans)
        resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
        resp.raise_for_status()

if __name__ == '__main__':
    annotators = [
        KeywordAnnotator(),
        GeonameAnnotator(),
    ]
    article_query_template = make_template("""
    prefix pro: <http://www.eha.io/types/promed/>
    prefix anno: <http://www.eha.io/types/annotation_prop/>
    prefix eha: <http://www.eha.io/types/>
    SELECT ?article_uri ?content
    WHERE {
        ?article_uri pro:text ?content
            ; pro:date ?date
        FILTER NOT EXISTS {
            ?article_uri anno:annotated_by eha:annie
        }
    }
    ORDER BY ?date
    LIMIT 100
    OFFSET {{ offset }}
    """)
    offset = 0
    while True:
        result = requests.post(config.SPARQLDB_URL + "/query", data={
            "query": article_query_template.render(offset=offset)
        }, headers={"Accept":"application/sparql-results+json" })
        result.raise_for_status()
        bindings = result.json()['results']['bindings']
        if len(bindings) == 0:
            print "No more results"
            break
        else:
            offset += len(bindings)
            for binding in bindings:
                article_uri = binding['article_uri']['value']
                content = binding['content']['value']
                print("Parsing " + article_uri)
                text = 'I thought I had a spot of periodontitis but it turned out to be Endometrial Endometrioid Adenocarcinoma with squamous differentiation.'
                doc = AnnoDoc(content)
                for annotator in annotators:
                    doc.add_tier(annotator)
                create_annotations(article_uri, doc)
