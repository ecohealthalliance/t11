from jinja2 import Environment
import json
import datetime

def escape(x):
    return json.dumps(x)[1:-1]
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
env.filters['sparqlCast'] = sparqlCast
def make_template(s):
    return env.from_string(s)
