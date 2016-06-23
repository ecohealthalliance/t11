Scripts for loading NLP annotations into a SPARQL Database

# Requirements

Apache Fuseki requires Oracle JDK 8.x and above.
The latest release can be found [here](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html).

# To run [Fuseki](https://jena.apache.org/documentation/fuseki2/index.html)

```
wget http://ftp.mirror.tw/pub/apache/jena/binaries/apache-jena-fuseki-2.4.0.tar.gz
tar -xvzf apache-jena-fuseki-2.4.0.tar.gz
cd apache-jena-fuseki-2.4.0
mkdir DB
# Increase the JVM heap size if GC overhead errors occur
JVM_ARGS=-Xmx3210m ./fuseki-server --update --loc=DB /dataset
```

## To load type data used by this project:

```
./s-post http://localhost:3030/dataset default types.ttl
```

## To import a Fuseki database

```
sudo apt-get install awscli
# Configure your aws access key. It must be in the grits-dev group.
aws s3 cp s3://promed-database/sparql-annotation-database/dump.ttl
# This could take a long time. Try increasing the Fuseki JVM heap size if it takes a really really long time.
./s-post http://localhost:3030/dataset default dump.ttl
```

## To create a new backup

```
./s-get http://localhost:3030/dataset default > dump.ttl 2>&1
aws s3 cp dump.ttl s3://promed-database/sparql-annotation-database/dump.ttl
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

# To install stanbol and the disease ontology (In Development)

Install Java 8, ansible 2.0+ and supervisor.

*If you are not using the ubunty apt version of Supervisor, you probably need
to set the variable supervisor_config_dir in site.yml*

Run the ansible playbook:

```
sudo ansible-playbook --connection=local site.yml --become-user=[your user] --extra "stanbol_dir=[path where you want to install stanbol]"
```

# To create annotations with annie

Follow the directions here to install the grits-api using the same virtual environment as this project:
https://github.com/ecohealthalliance/grits-api#installation-and-set-up

Import the disease ontology into Fuseki

```
cd [fuseki directory]
wget http://purl.obolibrary.org/obo/doid.owl
./bin/s-post http://localhost:3030/dataset default doid.owl
```

```
python annie_to_rdf.py
```

# To add computed predicates (like anno:contains)

Computed predicates are relationships added after data is imported.
They are used to make queries simpler and more efficient.

```
python add_computed_predicates.py
```
