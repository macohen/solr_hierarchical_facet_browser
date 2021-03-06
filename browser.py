from flask import Flask,render_template, Response, url_for, redirect
import sys
from pprint import pprint
from solr_query_runner import SolrQuery
import urllib
from markupsafe import Markup

app = Flask(__name__)
app.debug = True


@app.template_filter("urlencode")
def urlencode_filter(s):
    if type(s) == "Markup":
        s = s.unescape()
    s = s.encode("utf8")
    s = urllib.quote_plus(s)
    return Markup(s)

def group_facets(depth, start=0, count=10):
    q = SolrQuery()
    return q.query("*:*", facet="on", facet_field=["groups_s_mv","series_s_mv"], facet_prefix=depth, rows=count, start_num=start, facet_mincount=1)

def docs_with_facet(hier_level, field, start=0):
    q = SolrQuery()
    query = field + ":\"" + hier_level + "\""
    app.logger.debug("calling docs_with_facet: " + query)
    return q.query(query, facet="on", facet_field=["file_name_s"], facet_mincount=1, start_num=start, rows=10)

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

@app.template_filter("drilldown")
def drilldown(drill):
    drill_down = replace_depth(drill, increment_depth)
    return drill_down

@app.template_filter("drillup")
def drillup(drill):
    drill_up = replace_depth(drill, decrement_depth)
    return drill_up

@app.template_filter("convert_to_hierarchy")
def make_hier(group):
    """ copied from BVIToSolrConverter.py """
    group_parts = group.split(":")
    group = "/".join(group_parts)
    group = str(len(group_parts)) + "/" + group 
    
    return group

@app.template_filter("partial_hierarchy")
def add_slash(group):
    return group + "/"

def clean_results(results):
    for result in results:
        file_name_field = result["file_name_s"]
#        app.logger.debug("file: " + file_name_field)
        file_name_scratch = file_name_field.split("/bvi")
        file_name_parts =file_name_scratch[1].split("/")
#        app.logger.debug("file_name_parts")
#        pprint(file_name_parts, stream=sys.stderr)
        date = file_name_parts[1]
        file_name = file_name_parts[2]
        if file_name != None:
            file_name = file_name.replace("/Users/cohenma/work/freewheel_logs/bvi/", "")
            file_structure = { 'file_name':file_name, 'date': date}
            result['file_structure'] = file_structure
    return results

def convert_solr_name(field_name):
    field_name = field_name.replace("_s_mv", "")
    field_name = field_name.title()
    return field_name
    

def clean_facet_keys(facets):
    field_name_map = {}
    for key in facets.keys():
        new_key = convert_solr_name(key)
        field_name_map[key] = new_key
    return field_name_map

@app.route("/bvi/<file_date>/<file_name>")
def show_bvi_file(file_date, file_name):
    def generate(file_name):
        app.logger.debug("opening " + file_name)
        with open(file_name, 'rb') as feed:
            for line in feed:
                yield line

    file_name = app.root_path + "/bvi_feeds/" + file_date + "/" + file_name
    app.logger.debug("file_name=" + file_name)
    return Response(generate(file_name), mimetype='text/xml')


@app.route("/")
def home():
    return redirect(url_for("query"))

@app.route("/browse/", defaults = {"drill_down" : "0/", "search_field" : "groups_s_mv", "start" : 0 })
@app.route("/browse/<search_field>/<drill_down>/", defaults={"start": 0})
@app.route("/browse/<search_field>/<drill_down>/<int:start>")
def query(search_field, drill_down, start):
    import urllib
    drill_down = urllib.unquote(drill_down)
    drill_down = drill_down.replace("+", " ")
    app.logger.debug("search_field={0}, drill_down={1}, start={2}".format(search_field, drill_down, start))

    results = group_facets(drill_down, start)
    
    facet_fields = {}
    browse = False
    # for each facet field
    for field, facets in results.facets["facet_fields"].iteritems():
        facet_pair = build_facet_pairs(facets)
        if len(facet_pair) > 0:
            browse = True
        facet_fields[field] = facet_pair

    if browse == False:
        app.logger.debug("browse off")
        drill_up = drillup(drill_down)
        drill_up = drill_up[0:len(drill_up)-1]
        results = docs_with_facet(drill_up, search_field, start)
    
    if browse == True:
        facet_name_map = clean_facet_keys(facet_fields)
        pprint(facets, stream=sys.stderr)
        return render_template("browser.html", facets=facet_fields, facet_names=facet_name_map)
    else:
        results = clean_results(results)
        return render_template("results.html", results=results)

def build_facet_pairs(facets):
    name = ""
    value = 0
    pair = ()
    pair_list = []
    num_facets = len(facets)
#    app.logger.debug(num_facets)
    for i in range(0, num_facets):
#        app.logger.debug(facets[i])
        if i % 2 == 0:                
            name = facets[i]
#            app.logger.debug("name= " + str(name))
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

if __name__ == "__main__":
    app.run()
