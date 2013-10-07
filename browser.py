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

@app.template_filter('partial_hierarchy')
def add_slash(group):
    return group + "/"

@app.route('/')
def query():
    drill_down = "0/"
    if request.args.get('drill') != None:
        drill_down = request.args.get('drill')
    
    results = group_facets(drill_down)
    facet_fields = {}
    browse = False
    # for each facet field
    for field, facets in results.facets['facet_fields'].iteritems():
        facet_pair = build_facet_pairs(facets)
        if len(facet_pair) > 0:
            browse = True
        facet_fields[field] = facet_pair

    if browse == False:
        app.logger.debug("browse off")
        drill_up = drillup(drill_down)
        drill_up = drill_up[0:len(drill_up)-1]
        results = docs_with_facet(drill_up)
    
    if browse == True:
        return render_template('browser.html', facets=facet_fields)
    else:
        return render_template('results.html', results=results)

def build_facet_pairs(facets):
    name = ""
    value = 0
    pair = ()
    pair_list = []
    num_facets = len(facets)
    app.logger.debug(num_facets)
    for i in range(0, num_facets):
        app.logger.debug(facets[i])
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
    return pair_list

if __name__ == '__main__':
    app.run()
