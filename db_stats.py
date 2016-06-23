import requests
from templater import make_template
import config

result = requests.post(config.SPARQLDB_URL + "/query", data={"query": """
prefix pro: <http://www.eha.io/types/promed/>
prefix eha: <http://www.eha.io/types/>
prefix anno: <http://www.eha.io/types/annotation_prop/>
SELECT
    ?annotator
    (count(?article) AS ?articles)
WHERE {
    ?article pro:post ?post .
    OPTIONAL {
        ?article anno:annotated_by ?annotator
    }
}
GROUP BY ?annotator
"""}, headers={"Accept":"application/sparql-results+json" })
print result.content
