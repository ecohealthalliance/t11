# coding=utf8
"""
Unit tests for import_mongo_articles
"""
import datetime
import textwrap
import unittest

from import_mongo_articles import create_sparql_post_update
from import_mongo_articles import create_sparql_article_update

class TestArticleImport(unittest.TestCase):
    def test_create_sparql_post(self):
        """Test for creating the SPARQL webservice query for a post"""
        expected_update = textwrap.dedent(
            """
            prefix pro: <http://www.eha.io/types/promed/>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#>
            INSERT DATA {
                <http://www.promedmail.org/post/112358> pro:date "2016-06-01T16:29:43-00:00"^^xsd:dateTime

                    ; pro:feed_id "65537"

            }
            """)
        post = {
            'promedDate': datetime.datetime(2016, 6, 1, 16, 29, 43),
            'sparqlDate': datetime.datetime(2016, 6, 4, 3, 13, 00),
            'feedId': 65537,
        }
        post_uri = "http://www.promedmail.org/post/112358"
        update = create_sparql_post_update(post, post_uri)
        update = textwrap.dedent(update)
        self.assertEquals(update, expected_update)
    def test_create_sparql_article(self):
        """Test for creating the SPARQL webservice query for an article"""
        expected_update = textwrap.dedent(
            """
            prefix pro: <http://www.eha.io/types/promed/>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#>
            INSERT DATA {
                <http://www.promedmail.org/post/112358#112358> pro:text "Test" ;
                                  pro:post <http://www.promedmail.org/post/112358>

                    ; pro:date "2016-06-01T16:29:43-00:00"^^xsd:dateTime

            }
            """)
        post = {
            'date': datetime.datetime(2016, 6, 1, 16, 29, 43),
            'sparqlDate': datetime.datetime(2016, 6, 4, 3, 13, 00),
            'content': 'Test',
        }
        post_uri = "http://www.promedmail.org/post/112358"
        article_uri = post_uri + "#112358"
        update = create_sparql_article_update(post, post_uri, article_uri)
        update = textwrap.dedent(update)
        self.assertEquals(update, expected_update)
