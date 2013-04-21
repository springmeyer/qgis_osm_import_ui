# -*- coding: utf-8 -*-

import os
import sys
import platform
from qgis.gui import *
from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import resources_rc

# Use pdb for debugging
#import pdb
# These lines allow you to set a breakpoint in the app
#pyqtRemoveInputHook()
#pdb.set_trace()

NAME = "OSM Import UI"
SLUG = "osm-import-ui"

def get_last_saved_osm_file():
    settings = QSettings()
    return settings.value( "/%s/last_osm_file" % SLUG, QVariant('') ).toString()

def set_last_saved_osm_file(filepath):
    settings = QSettings()
    settings.setValue( "/%s/last_osm_file" % SLUG, QVariant(filepath) )

def set_last_load_dir(name,path):
    settings = QSettings()
    fileInfo = QFileInfo(path)
    if fileInfo.isDir():
        dirPath = fileInfo.filePath()
    else:
        dirPath = fileInfo.path()
    settings.setValue( "/%s/last_dir/load/%s" % (SLUG,name), QVariant(dirPath) )

def get_last_load_dir(name):
    settings = QSettings()
    last_dir = settings.value( "/UI/lastProjectDir", QVariant("") ).toString()
    return settings.value( "/%s/last_dir/load/%s" % (SLUG,name), QVariant(last_dir) ).toString()

def set_last_load_dir(name,path):
    settings = QSettings()
    fileInfo = QFileInfo(path)
    if fileInfo.isDir():
        dirPath = fileInfo.filePath()
    else:
        dirPath = fileInfo.path()
    settings.setValue( "/%s/last_dir/load/%s" % (SLUG,name), QVariant(dirPath) )

def get_last_save_dir(name):
    settings = QSettings()
    last_dir = settings.value( "/UI/lastProjectDir", QVariant("") ).toString()
    return settings.value( "/%s/last_dir/save/%s" % (SLUG,name), QVariant(last_dir) ).toString()

def set_last_save_dir(name,path):
    settings = QSettings()
    fileInfo = QFileInfo(path)
    if fileInfo.isDir():
        dirPath = fileInfo.filePath()
    else:
        dirPath = fileInfo.path()
    settings.setValue( "/%s/last_dir/save/%s" % (SLUG,name), QVariant(dirPath) )

def get_osm2pgsql_path():
    settings = QSettings()
    return settings.value( "/%s/osm2pgsql_path" % SLUG, QVariant( "" ) ).toString()

def set_osm2pgsql_path( path ):
    settings = QSettings()
    settings.setValue( "/%s/osm2pgsql_path" % SLUG, QVariant( path ) )

def get_osmosis_path():
    settings = QSettings()
    return settings.value( "/%s/osmosis_path" % SLUG, QVariant( "" ) ).toString()

def set_osmosis_path( path ):
    settings = QSettings()
    settings.setValue( "/%s/osmosis_path" % SLUG, QVariant( path ) )


class Commands(QObject):
    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface
        self.dock_window = None
        self.dock_window2 = None
        self.bbox_area = None
        self.canvas = self.iface.mapCanvas()
        self.actions = []

    def create_action(self,meta):
        action = QAction(QCoreApplication.translate( NAME, "&%s" % meta['title'] ), self.iface.mainWindow())
        tooltip = meta.get('tooltip')
        if tooltip:
            action.setWhatsThis(tooltip)
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
        icon = meta.get('icon')
        if icon:
            action.setIcon(QIcon(icon))
        action_name = '%s_action' % meta['action']
        setattr(self,action_name,action)
        setattr(action,'action_name',action_name)
        QObject.connect(getattr(self,action_name), SIGNAL("triggered()"), getattr(self,meta['action']))
        return getattr(self,action_name)

    def create_menu(self,actions):
        for action in actions:
            action_obj = self.create_action(action)
            self.actions.append(action_obj)
            # Add toolbar button and menu item
            self.iface.addToolBarIcon(action_obj)
            self.iface.addPluginToMenu("&%s" % NAME, action_obj)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu("&%s" % NAME,action)
            self.iface.removeToolBarIcon(action)
            
    def initGui(self):
        actions = []
        actions.append({
                    'title':'Process OSM data (osmosis)',
                    'action':'osmosis',
                    'tooltip':'Download and clip .osm files using the osmosis java application',
                    'icon':':/icons/osmosis.png',
                  })
        actions.append({
                    'title':'Import into PostGIS (osm2pgsql)',
                    'action':'osm2pgsql',
                    'tooltip':'Import an osm or osm.bz2 file into a PostGIS enabled PostgreSQL database using osm2pgsql',
                    'icon':':/icons/osm2pgsql.png',
                  })
        actions.append({
                    'title':'%s settings' % NAME,
                    'action':'plugin_settings',
                    'tooltip':'',
                    'icon':'',
                  })
        self.create_menu(actions)

    def plugin_settings(self):
        import settings
        d = settings.SettingsDialog( self.iface )
        d.exec_()
    
    def osm2pgsql(self):
        if not self.dock_window2:
            from command_dock2 import CommandDock as CommandDock2
            self.dock_window2 = CommandDock2(self)
            self.iface.mainWindow().addDockWidget( Qt.RightDockWidgetArea,
                                                   self.dock_window2 )
        if self.dock_window:
            self.dock_window.hide()
        self.dock_window2.show()
            
    def osmosis(self):
        if not self.dock_window:
            from command_dock import CommandDock
            self.dock_window = CommandDock(self)
            self.iface.mainWindow().addDockWidget( Qt.RightDockWidgetArea,
                                                   self.dock_window )
        if self.dock_window2:
            self.dock_window2.hide()
        self.dock_window.show()