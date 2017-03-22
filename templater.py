from jinja2 import Environment
import json
import datetime
import re

def escape(x):
    return json.dumps(x)[1:-1]
def replace_invalid_uri_chars(x):
    return re.sub("[^a-zA-Z0-9_\-]", "_", x)
def sparqlDate(x):
    return x.strftime('%Y-%m-%dT%H:%M:%S-00:00')
def sparqlCast(x):
    """
    Cast the given value to an equivalent type formatted as a SPARQL string.
    """
    if isinstance(x, datetime.datetime):
        return '"' + sparqlDate(x) + '"^^xsd:dateTime'
    else:
        return json.dumps(x)
env = Environment()
env.filters['sparqlDate'] = sparqlDate
env.filters['escape'] = escape
env.filters['replace_invalid_uri_chars'] = replace_invalid_uri_chars
env.filters['sparqlCast'] = sparqlCast
def make_template(s):
    return env.from_string(s)
