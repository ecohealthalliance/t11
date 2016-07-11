import requests
from requests.auth import HTTPDigestAuth
import config

def query(query_text):
    resp = requests.post(config.SPARQLDB_URL,
        auth=HTTPDigestAuth(config.SPARQLDB_USER, config.SPARQLDB_PASSWORD),
        data={"query": query_text},
        headers={"Accept":"application/sparql-results+json" })
    try:
        resp.raise_for_status()
        return resp
    except requests.exceptions.HTTPError as e:
        print resp.content[0:2000] + "..."
        raise e

def update(query_text):
    if "SPARQLDB_UPDATE_URL" in dir(config):
        resp = requests.post(config.SPARQLDB_UPDATE_URL,
            auth=HTTPDigestAuth(config.SPARQLDB_USER, config.SPARQLDB_PASSWORD),
            data={"update": query_text},
            headers={"Accept":"application/sparql-results+json" })
        try:
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            print resp.content[0:1000]
            raise e
    else:
        return query(query_text)
