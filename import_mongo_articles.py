#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import ProMED articles from mongo into SPARQL DB
"""
import pymongo
import argparse
from templater import make_template
import requests
import config

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mongo_url", default='localhost'
    )
    parser.add_argument(
        "--db_name", default='promed'
    )
    args = parser.parse_args()
    db = pymongo.MongoClient(args.mongo_url)[args.db_name]

    def resolve_report(archive_num):
        post = db.posts.find_one({'archiveNumber': archive_num})
        if post:
            return "http://www.promedmail.org/post/" + post.get('promedId')

    query = {}
    print("Number of articles to process:")
    print(db.posts.find(query).count())
    for post in db.posts.find(query):
        # Create triples for post
        post_uri = "http://www.promedmail.org/post/" + post['promedId']
        update_query = make_template("""
        prefix pro: <http://www.eha.io/types/promed/>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {
            <{{post_uri}}> pro:date "{{promedDate | sparqlDate}}"^^xsd:dateTime
                ; pro:subject_raw "{{subject.raw | escape}}"
                ; pro:archiveNumber "{{archiveNumber}}"
            {% for linkedReport in resolvedLinkedReports %}
                ; pro:linkedReport <{{linkedReport}}>
            {% endfor %}
            {% if feedId %}
                ; pro:feed_id "{{feedId}}"
            {% endif %}
        }
        """).render(
            post_uri=post_uri,
            resolvedLinkedReports=filter(lambda x:x, map(resolve_report, post['linkedReports'])),
            **post)
        resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
        resp.raise_for_status()
        for idx, art in enumerate(post["articles"]):
            if not 'content' in art: continue
            # Create triples for article within the post
            article_uri = post_uri + "#" + str(idx)
            update_query = make_template("""
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
                **art)
            resp = requests.post(config.SPARQLDB_URL + "/update", data={"update": update_query})
            resp.raise_for_status()
            print("Imported " + article_uri)
