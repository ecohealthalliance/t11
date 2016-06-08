#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import ProMED articles from mongo into SPARQL DB
"""
import sys

import argparse
import pymongo
import requests

import config
from templater import make_template

def do_parse(args):
    """Handles the command line I/O for import_mongo_articles"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mongo_url", default='localhost'
    )
    parser.add_argument(
        "--db_name", default='promed'
    )
    args = parser.parse_args(args)
    database = pymongo.MongoClient(args.mongo_url)[args.db_name]

    query = {}
    posts = database.posts.find(query)
    post_count = posts.count()
    print "Number of posts to process:", post_count
    article_count = 0
    for post in posts:
        post_uri = "http://www.promedmail.org/post/" + post['promedId']
        update_query = create_sparql_post_update(post, post_uri)
        resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
        resp.raise_for_status()
        for idx, article in enumerate(post["articles"]):
            if not 'content' in article:
                continue
            article_count += 1
            # Create triples for article within the post
            article_uri = post_uri + "#" + str(idx)
            update_query = create_sparql_article_update(article, post_uri, article_uri)
            resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
            resp.raise_for_status()            
            print "Imported " + article_uri
    print "Imported", article_count, "total articles in", post_count, "posts."

def create_sparql_post_update(post, post_uri):
    """Create triples for post"""
    return make_template("""
        prefix pro: <http://www.eha.io/types/promed/>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {
            <{{post_uri}}> pro:date "{{promedDate | sparqlDate}}"^^xsd:dateTime
             {% if feedId %}
                ; pro:feed_id "{{feedId}}"
             {% endif %}
        }
    """).render(
        post_uri=post_uri,
        **post)

def create_sparql_article_update(article, post_uri, article_uri):
    """Create triples for article"""
    return make_template("""
        prefix pro: <http://www.eha.io/types/promed/>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {
            <{{article_uri}}> pro:text "{{content | escape}}" ;
                              pro:post <{{post_uri}}>
             {% if date %}
                ; pro:date "{{date | sparqlDate}}"^^xsd:dateTime
             {% endif %}
        }
    """).render(
        post_uri=post_uri,
        article_uri=article_uri,
        **article)

if __name__ == '__main__':
    do_parse(sys.argv[1:])
