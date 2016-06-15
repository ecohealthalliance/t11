#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import Tater data into a SPARQL DB
"""
import pymongo
import argparse
from templater import make_template
import requests
import config
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mongo_url", default='localhost'
    )
    parser.add_argument(
        "--db_name", default='t11'
    )
    args = parser.parse_args()
    db = pymongo.MongoClient(args.mongo_url)[args.db_name]
    for document in db.documents.find({}):
        uri = "http://t11.tater.io/documents/" + document['_id']
        update_query = make_template("""
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        prefix tater: <http://www.eha.io/types/tater/>
        prefix con: <http://www.eha.io/types/content/>
        INSERT DATA {
            <{{uri}}> con:text "{{doc.body | escape}}"
            {% for key in ['title', 'createdAt'] %}
                ; tater:{{key}} {{doc[key] | sparqlCast}}
            {% endfor %}
            .
        }
        """).render(
            uri=uri,
            doc=document
        )
        resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
        resp.raise_for_status()
        print("Imported " + uri)
    for code in db.keywords.find({}):
        uri = "http://t11.tater.io/codingKeywords/" + code['_id']
        update_query = make_template("""
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix tater: <http://www.eha.io/types/tater/>
        INSERT DATA {
            <{{uri}}> rdfs:label "{{code['label'] | escape}}"
                ; tater:header <{{header_uri}}>
        }
        """).render(
            uri=uri,
            code=code,
            header_uri="http://t11.tater.io/headers/" + code['headerId']
        )
        resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
        resp.raise_for_status()
        print("Imported " + uri)
    for annotation in db.annotations.find({}):
        uri = "http://t11.tater.io/annotations/" + annotation['_id']
        update_query = make_template("""
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        prefix tater: <http://www.eha.io/types/tater/>
        prefix eha: <http://www.eha.io/types/>
        prefix anno: <http://www.eha.io/types/annotation_prop/>
        INSERT DATA {
            <{{uri}}> anno:start {{annotation['startOffset']}}
                ; anno:end {{annotation['endOffset']}}
                ; anno:source_doc <{{doc_uri}}>
                ; anno:annotator eha:tater
                ; tater:code <{{code_uri}}>
                .
        }
        """).render(
            uri=uri,
            annotation=annotation,
            code_uri="http://t11.tater.io/codingKeywords/" + annotation['codeId'],
            doc_uri="http://t11.tater.io/documents/" + annotation['documentId']
        )
        resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
        resp.raise_for_status()
        print("Imported " + uri)
