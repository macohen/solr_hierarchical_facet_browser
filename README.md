solr_hierarchical_facet_browser
===============================

Browse hierarchical facets using Flask, Solr, &amp; Twitter Bootstrap

This project is a result of a data cleanup effort. The intent is to take strings that are formatted in a sort of hierarchy:

Content Type: VH1: Full Episodes

and use the "Flattened Breadcrumb" methodology described [here](http://wiki.apache.org/solr/HierarchicalFaceting#Flattened_Data_.2BIBw-breadcrumbs.2BIB0-) to browse the hierarchy.  When the leaf of the hierarchy is reached a search is performed to pull all results containing that "breadcrumb trail."

Also, I wanted to learn [Flask](http://flask.pococo.org) and try out [Twitter Bootstrap](http://getbootstrap.com).


