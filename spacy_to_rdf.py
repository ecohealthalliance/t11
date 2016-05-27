#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This iterates over stored articles loading their spacy parse trees into
annotations in a SPARQL DB. 

Useful resources related to spacy parse trees:
https://nicschrading.com/project/Intro-to-NLP-with-spaCy/
https://spacy.io/demos/displacy
"""
import argparse
from spacy.en import English
from templater import make_template
import requests
import hashlib
import config

def create_annotations(article_uri, tokens):
    token_to_range = {}
    def update_range(r1, r2):
        if r1 is None:
            return r2
        if r2 is None:
            return r1
        return [min(r1[0], r2[0]), max(r1[1], r2[1])]
    for token in tokens:
        child_token = token
        # import pdb; pdb.set_trace()
        while True:
            token_to_range[token] = update_range(
                token_to_range.get(token),
                update_range(
                    token_to_range.get(child_token),
                    [token.idx, token.idx + len(token.text)]))
            if token.dep_ != 'ROOT':
                child_token = token
                token = token.head
            else:
                break
    def get_token_uri(token):
        h = hashlib.md5()
        h.update(article_uri)
        h.update(str(token.idx))
        return "http://www.eha.io/types/annotation/spacy/" + str(h.hexdigest())
    def get_pharse_uri(token):
        h = hashlib.md5()
        h.update(article_uri)
        start, end = token_to_range[token]
        assert isinstance(start, int)
        assert isinstance(end, int)
        h.update(str(start) + ':' + str(end))
        return "http://www.eha.io/types/annotation/spacy/phrase/" + str(h.hexdigest())
    for token in tokens:
        update_query = make_template("""
        prefix anno: <http://www.eha.io/types/annotation_prop/>
        prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
        prefix eha: <http://www.eha.io/types/>
        prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
        
        INSERT DATA {
            <{{pharse_ref}}> rdf:type eha:dependent_pharse
                ; anno:annotator eha:spacy
                ; anno:source_doc <{{source_doc}}>
                ; anno:start {{phrase_start}}
                ; anno:end {{phrase_end}}
                ; anno:root <{{token_ref}}>
        } ;
        INSERT DATA {
            <{{token_ref}}> rdf:label "{{root_word | escape}}"
                ; anno:pos "{{pos}}"
                {% if entity_type %}
                    ; anno:entity_type "{{entity_type}}"
                {% endif %}
        } ;
        INSERT DATA {
            <{{parent_phrase_ref}}> dep:{{dep}} <{{pharse_ref}}>
        }
        """).render(
            source_doc=article_uri,
            phrase_start=token_to_range[token][0],
            phrase_end=token_to_range[token][1],
            root_word=token.text,
            pos=token.pos_,
            entity_type=token.ent_type_,
            token_ref=get_token_uri(token),
            pharse_ref=get_pharse_uri(token),
            parent_phrase_ref=get_pharse_uri(token.head),
            dep=token.dep_)
        resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
        resp.raise_for_status()

if __name__ == '__main__':
    spacy_parser = English()
    print("Spacy Ready!")
    
    article_query_template = make_template("""
    prefix pro: <http://www.eha.io/types/promed/>
    SELECT ?article_uri ?content
    WHERE {
        ?article_uri pro:text ?content
            ; pro:date ?date
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
                tokens = spacy_parser(content)
                create_annotations(article_uri, tokens)
