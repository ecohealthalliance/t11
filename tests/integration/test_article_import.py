# coding=utf8
"""
Unit tests for import_mongo_articles
"""
import unittest

import json
import requests
from schema import Schema, And, Use, Optional

class TestArticleImportCount(unittest.TestCase):
    def test_integration(self):
        """Integration test with Mongo and Fuseki"""
        request = {"query": """
            prefix anno: <http://www.eha.io/types/annotation_prop/>
            prefix dep: <http://www.eha.io/types/annotation_prop/dep/>
            prefix rdf: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?word (count(?s) as ?count)
            WHERE {
              ?s anno:root ?r .
              ?r anno:pos 'NOUN' ;
              rdf:label ?word .
            }
            GROUP BY ?word
            ORDER BY DESC(?count)
            LIMIT 10
        """}
        headers = {"Accept": "application/sparql-results+json"}
        raw_response = requests.post("http://localhost:3030/dataset/query", data=request, headers=headers)
        response = json.loads(raw_response.content)
        print json.dumps(response, indent=4, sort_keys=True)
        schema = Schema({
            'head': {'vars': ['word', 'count']},
            'results': {
                'bindings': [
                    {
                        'count': {
                            'datatype': 'http://www.w3.org/2001/XMLSchema#integer',
                            'type': 'literal',
                            'value': And(unicode, lambda x: x > 0)
                        },
                        'word': {
                            'type': 'literal',
                            'value': And(unicode, len)
                        }
                    }
                ]
            }
        })
        schema.validate(response)
