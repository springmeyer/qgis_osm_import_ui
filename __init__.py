# -*- coding: utf-8 -*-

def name():
    return "OSM-Import-UI"

def description():
    return "GUI for OSM tools (osmosis/osm2pgsql)"

def version():
    return "Version 0.1.11"

def qgisMinimumVersion():
    return "1.8"

def author():
    return "Dane Springmeyer"

def email():
    return "dane@dbsgeo.com"

def homepage():
    return "https://github.com/springmeyer/qgis_osm_import_ui"

def classFactory(iface):
    from osm_tools import Commands
    return Commands(iface)
