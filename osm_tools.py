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

    def create_action_group(self,name,actions):
        setattr(self,name,QMenu( QCoreApplication.translate( NAME, "&%s" % name ) ))
        action_objs = []
        for action_name in actions:
            action_obj = QAction(QCoreApplication.translate( NAME, action_name.replace('_',' ')), self.iface.mainWindow())
            action_objs.append(action_obj)
            setattr(self,'%s_action' % action_name, action_obj)
            #self.action.setWhatsThis("Clip osm file")
            QObject.connect(getattr(self,'%s_action' % action_name), SIGNAL("triggered()"), getattr(self,action_name))
        menu_item = getattr(self,name)
        menu_item.addActions( action_objs )
        return menu_item

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
        QObject.connect(getattr(self,action_name), SIGNAL("triggered()"), getattr(self,meta['action']))
        return getattr(self,action_name)
                
    def create_menu(self):
        self.menu = QMenu()
        self.menu.setTitle(QCoreApplication.translate(NAME, "&%s" % NAME))
        self.menu.addMenu(self.create_action_group("Process",["osmosis_clip"]))
        self.menu.addMenu(self.create_action_group("Import",["osm2pgsql"]))
        self.menu.addSeparator()    
        menu_bar = self.iface.mainWindow().menuBar()
        actions = menu_bar.actions()
        lastAction = actions[ len( actions ) - 1 ]
        menu_bar.insertMenu( lastAction, self.menu )    
        self.unload = self.unload_menu

    def create_menu2(self,actions):
        self.menu = QMenu()
        self.menu.setTitle(QCoreApplication.translate(NAME, "&%s" % NAME))
        for action in actions:
            self.menu.addAction(self.create_action(action))
        #self.menu.addSeparator()    
        menu_bar = self.iface.mainWindow().menuBar()
        actions = menu_bar.actions()
        lastAction = actions[ len( actions ) - 1 ]
        menu_bar.insertMenu( lastAction, self.menu )    
        self.unload = self.unload_menu
         
    def unload_menu(self):
        pass
        
    def create_plugin_menu(self):
        self.action = QAction(QString("Clip osm file (osmosis)"), self.iface.mainWindow())
        self.action.setWhatsThis("Clip osm file")
        QObject.connect(self.action, SIGNAL("triggered()"), self.clip)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&%s" % NAME, self.action)
        
        # osm2pgsql
        self.action2 = QAction(QString("Import osm to postgis (osm2pgsql)"), self.iface.mainWindow())
        self.action2.setWhatsThis("Clip osm file")
        QObject.connect(self.action2, SIGNAL("triggered()"), self.import2postgis)
        self.iface.addToolBarIcon(self.action2)
        self.iface.addPluginToMenu("&%s" % NAME, self.action2)
        self.unload = self.unload_plugin_menu

    def unload_plugin_menu(self):
        self.iface.removePluginMenu("&%s" % NAME,self.action)
        self.iface.removeToolBarIcon(self.action)

        self.iface.removePluginMenu("&%s" % NAME,self.action2)
        self.iface.removeToolBarIcon(self.action2)
            
    def initGui(self):
        #self.create_menu()
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
                    'title':'Tool settings',
                    'action':'plugin_settings',
                    'tooltip':'',
                    'icon':'',
                  })
        self.create_menu2(actions)

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