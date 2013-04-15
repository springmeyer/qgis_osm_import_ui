# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
#from qgis.core import *
#from qgis.gui import *

from dialog_settings_ui import Ui_Dialog
import osm_tools

class SettingsDialog( QDialog, Ui_Dialog ):
  def __init__( self, iface ):
    QDialog.__init__( self, iface.mainWindow() )
    self.iface = iface
    self.setupUi( self )

    self.osm2pgsql_path.setText( osm_tools.get_osm2pgsql_path() )
    self.osmosis_path.setText( osm_tools.get_osmosis_path() )

    QObject.connect( self.set_osm2pgsql_path, SIGNAL( "clicked()" ), self.set_osm2pgsql )
    QObject.connect( self.set_osmosis_path, SIGNAL( "clicked()" ), self.set_osmosis )

  def set_osm2pgsql(self):
    val = QFileDialog.getExistingDirectory(None, "Select directory with osm2pgsql binary")
    if val.isEmpty():
      return

    self.osm2pgsql_path.setText(val)

  def set_osmosis(self):
    val = QFileDialog.getExistingDirectory(None, "Select directory with osmosis binary")
    if val.isEmpty():
      return

    self.osmosis_path.setText(val)

  def accept( self ):
    osm_tools.set_osm2pgsql_path( self.osm2pgsql_path.text() )
    osm_tools.set_osmosis_path( self.osmosis_path.text() )
    QDialog.accept( self )
