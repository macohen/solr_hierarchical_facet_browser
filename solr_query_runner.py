import pysolr

SOLR_SERVER = "http://localhost:8983/solr/bvi_newfeeds"

class SolrQuery():
    def __init__(self):
        self.solr_conn = pysolr.Solr(SOLR_SERVER)

    def query(self, query, facet=None, facet_field=None, facet_prefix=None, facet_mincount=0, rows=10):
        params = {}
        if facet != None:
            params['facet'] = 'true'
        if facet_field != None:
            params['facet.field'] = facet_field
        if facet_prefix != None:
            params['facet.prefix'] = facet_prefix
        params['rows'] = rows
        response = self.solr_conn.search(query,** params)
        return response

        
    
    

