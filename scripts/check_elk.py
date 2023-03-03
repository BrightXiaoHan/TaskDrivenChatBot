from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:19200", http_auth=("elastic", "changeme"))

es.info()
