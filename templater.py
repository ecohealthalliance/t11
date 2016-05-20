from jinja2 import Environment
import json
env = Environment()
env.filters['sparqlDate'] = lambda x: x.strftime('%Y-%m-%dT%H:%M:%S-00:00')
env.filters['escape'] = lambda x: json.dumps(x)[1:-1]

def make_template(s):
    return env.from_string(s)
