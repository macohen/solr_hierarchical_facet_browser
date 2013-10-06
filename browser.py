from flask import Flask,render_template, request
from solr_query_runner import SolrQuery
import urllib
from markupsafe import Markup

app = Flask(__name__)
app.debug = True


@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return Markup(s)

def group_facets(depth):
    q = SolrQuery()
    return q.query("*:*", facet='on', facet_field=['groups_s_mv'], facet_prefix=depth, rows=10, facet_mincount=1)


def docs_with_facet(field):
    q = SolrQuery()
    return q.query("groups_s_mv:\"" + field + "\"", facet='on', facet_field=['file_name_s'], facet_mincount=1, rows=10)

def get_depth(matchobj):
    depth = int(matchobj.group(1))
    return depth
def increment_depth(matchobj):
    depth = get_depth(matchobj)
    return str(depth + 1)

def decrement_depth(matchobj):
    depth = get_depth(matchobj)
    return str(depth - 1)

def replace_depth(drill, depth_changer):
    import re
    pattern = re.compile("^(\d+)")
    drill_down = re.sub(pattern, depth_changer, drill)
    app.logger.debug(drill_down)
    return drill_down

@app.template_filter('drilldown')
def drilldown(drill):
    drill_down = replace_depth(drill, increment_depth)
    return drill_down

@app.template_filter('drillup')
def drillup(drill):
    drill_up = replace_depth(drill, decrement_depth)
    return drill_up

@app.template_filter('convert_to_hierarchy')
def make_hier(group):
    """ copied from BVIToSolrConverter.py """
    group_parts = group.split(":")
    group = "/".join(group_parts)
    group = str(len(group_parts)) + "/" + group  
    
    return group

#def convert(group):
    
@app.route('/')
def query():
    drill_down = "0/"
    if request.args.get('drill') != None:
        drill_down = request.args.get('drill')
#        app.logger.debug("drill=" + drill_down)
    
    results = group_facets(drill_down)
#    num_facets = len(results.facets['facet_fields'])
#    if num_facets == 0:
#        app.logger.debug("no more to drill down")
#    else:
#        app.logger.debug(str(num_facets) + " more to drill down")
        
    facet_fields = {}
    for field, facets in results.facets['facet_fields'].iteritems():
        i=0
        name = ""
        value = 0
        pair=()
        pair_list = []
        app.logger.debug("facets: {0}".format(facets))
        num_facets = len(facets)
        if num_facets > 0:
            for i in range(0, num_facets):
                #            app.logger.debug(facets[i])
                if i % 2 == 0:                
                    name = facets[i]
                    app.logger.debug("name= " + str(name))
                else:
                    value = facets[i]
                    pair = (name, value)
                    pair_list.append(pair)
                    #               app.logger.debug("value= " + str(value))
                    name = ""
                    value = 0
                    #              app.logger.debug(pair)
                    pair = ()
        else:
            #back up one level
            drill_up = drillup(drill_down)
            results = docs_with_facet(drill_up)
#            for result in results:
#                app.logger.debug(result)

            return render_template('results.html', results=results)
            

 #       for item in pair_list:
 #           app.logger.debug(item)
        facet_fields[field] = pair_list
 #       app.logger.debug(facet_fields)
#        app.logger.debug(facet)
#        app.logger.debug(type(facet))
    return render_template('browser.html', facets=facet_fields)

if __name__ == '__main__':
    app.run()
