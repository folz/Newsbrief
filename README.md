# News....

Get today's important news and summarize it into bite-sized chunks.

Running it:

`virtualenv venv --distribute`

`pip install -r requirements.txt`

In one terminal:

`javac -classpath ./Classifier4J-0.6.jar:./venv/share/py4j/py4j0.7.jar:./boilerpipe-1.2.0/boilerpipe-1.2.0.jar:.:./boilerpipe-1.2.0/lib/nekohtml-1.9.13.jar:./boilerpipe-1.2.0/lib/xerces-2.9.1.jar BoilerpipeGateway.java`

`java -classpath ./Classifier4J-0.6.jar:./venv/share/py4j/py4j0.7.jar:./boilerpipe-1.2.0/boilerpipe-1.2.0.jar:.:./boilerpipe-1.2.0/lib/nekohtml-1.9.13.jar:./boilerpipe-1.2.0/lib/xerces-2.9.1.jar BoilerpipeGateway`

In another terminal:

`source venv/bin/activate`

`python features.py`

Inspect "national_news.txt" and "summaries.txt" when features.py is finished running.
