Scripts for loading NLP annotations into a SPARQL Database

# To run [Fuseki](https://jena.apache.org/documentation/fuseki2/index.html)

```
wget http://ftp.mirror.tw/pub/apache/jena/binaries/apache-jena-fuseki-2.4.0.tar.gz
tar -xvzf apache-jena-fuseki-2.4.0.tar.gz
cd apache-jena-fuseki-2.4.0
mkdir DB
./fuseki-server --update --loc=DB /dataset
```
In another window load the types data:
```
./bin/s-post http://localhost:3030/dataset default ../types.ttl
```

## To laod spacy parse trees into Fuseki

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.pip
python -m spacy.en.download
python spacy_to_rdf.py
```
