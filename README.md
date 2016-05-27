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

## To import a Fuseki database

Stop Fuseki.

```
sudo apt-get install awscli
# Configure your aws access key. It must be in the grits-dev group.
aws s3 cp s3://promed-database/sparql-annotation-database/DB.tar.gz
tar -xvzf DB.tar.gz [Your DB directory location]
```

## To create a new backup

```
tar -cvzf DB.tar.gz [Your DB directory location]
aws s3 cp DB.tar.gz s3://promed-database/sparql-annotation-database/DB.tar.gz
```

# To run the Python scripts

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.pip
```

## To import ProMED articles from mongo into Fuseki

```
python import_mongo_articles.py
```

## To load spacy parse trees into Fuseki

```
python -m spacy.en.download
python spacy_to_rdf.py
```
