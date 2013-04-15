# -*- coding: utf-8 -*-

import os
import sys
import time
import shlex
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from command_dock_ui2 import Ui_DockWidget

import osm_tools

debug = False

currentPath = os.path.dirname( __file__ )
default_style = os.path.abspath( os.path.join(os.path.dirname( __file__), 'default.style' ) )

class CommandDock(QDockWidget, Ui_DockWidget):
    def __init__(self, parent):
        QDockWidget.__init__(self, parent.iface.mainWindow())
        self.parent = parent
        self.setupUi(self)
        self.add_dropable_path('input',dropable=True)
        self.add_dropable_path('style',dropable=False)

        self.process = QProcess()
        self.connect(self.go, SIGNAL("clicked()"), self.startCommand)
        self.connect(self.parent.canvas, SIGNAL("extentsChanged()"),self.bbox_hook)
        self.connect(self.process, SIGNAL("readyReadStandardOutput()"), self.readOutput)
        self.connect(self.process, SIGNAL("readyReadStandardError()"), self.readErrors)
        self.connect(self.process, SIGNAL("error(QProcess::ProcessError)"), self.catchError)
        self.connect(self.process, SIGNAL("finished(int, QProcess::ExitStatus)"), self.finished)
        self.connect(self.comboBox, SIGNAL("highlighted(QString)"),self.update_active_db)        
        self.connect(self.refresh_db_list, SIGNAL("clicked()"), self.listDatabases)
        self.bounds = '0.0,0.0,0.0,0.0'
        if debug:
            self.input_file()
        #self.output_file()
        self.listDatabases()
        if not str(self.input.text()):
            self.input.setText(osm_tools.get_last_saved_osm_file())
        self.first = True

    def err_msg(self,msg):
        err = self.process.errorString()
        if not err:
            err = "Error"
        self.command_output.setHtml('<span style="color:red;"><b>%s: %s</b></span>' % (err,msg))
    
    def catchError(self,error=None):
        self.err_msg(self.process.errorString())

    def finished(self,code,status):
        #QMessageBox.information(self.parent.iface.mainWindow(),"code","code")
        self.command_output.append(QString('<span style="color:green;"><b>Finished!</b></span>'))
        #self.command_output.append(QString('e: %s %s' % (code,status)))

    def readOutput(self):
        #osm2pgsql sends to stderr
        self.command_output.append(QString(self.process.readAllStandardOutput()))

    def readErrors(self):
        line = QString(self.process.readAllStandardError())
        if line.contains('notice',Qt.CaseInsensitive):
            pass # notices freak new users out
        elif line.contains('processing',Qt.CaseInsensitive) or line.contains('writing',Qt.CaseInsensitive):
            if self.first:
                self.first = False
            else:
                self.command_output.document().undo()            
            blue = QString('<span style="color:blue;"><b>%s</b></span>' % line)
            self.command_output.append(blue)
        else:
            self.command_output.append(line)
    
    def update_active_db(self, selected):
        settings = QSettings()
        settings.setValue("/PostgreSQL/connections/selected", QVariant(selected))
        
    def listDatabases(self):
        settings = QSettings()
        settings.beginGroup("/PostgreSQL/connections")
        keys = settings.childGroups()
        self.comboBox.clear()
        for key in keys:
          self.comboBox.addItem(key)
        settings.endGroup()
        settings = QSettings()
        selected = unicode(settings.value("/PostgreSQL/connections/selected").toString())
        self.comboBox.setCurrentIndex(self.comboBox.findText(selected))
 
    def path_drop(self,event):
        urls = event.mimeData().urls()
        return str(urls[0].path())

    def path_drag_input(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def path_drop_input(self, event):
        self.input.setText(self.path_drop(event))
        event.acceptProposedAction()

    def add_dropable_path(self,name,dropable=True):
        QObject.connect(getattr(self,'%s_button' % name), SIGNAL("clicked()"), getattr(self,'%s_file' % name))

        if dropable:
            getattr(self,name).__class__.dragEnterEvent = getattr(self,'path_drag_%s' % name)
            getattr(self,name).__class__.dropEvent = getattr(self,'path_drop_%s' % name)
   
    def input_file(self):
        if debug:
            self.input.setText('/Users/dane/Downloads/latest.osm')
            return
        val = QFileDialog.getOpenFileNames(None, "One or more OSM files to import",osm_tools.get_last_load_dir('osm2pgsql'), "OSM (*.osm *.osm.bz2)")
        if isinstance(val, QStringList):
            text = ';'.join([str(i) for i in val])
            if text:
                self.input.setText(text)
                osm_tools.set_last_load_dir('osm2pgsql',val[0])                
        elif str(val):
            self.input.setText(str(val))
            osm_tools.set_last_load_dir('osm2pgsql',str(val))
        
    def style_file(self):
        #self.output.setText('/Users/dane/test.osm')
        #return
        val = str(QFileDialog.getOpenFileName(None, "Style file", osm_tools.get_last_load_dir('osm2pgsql'), "Style (*.style)"))
        if val:
            self.style.setText(val)
    
    def closeEvent(self, event):
        self.parent.dock_window2 = None

    def bbox_hook(self):
        e = self.parent.iface.mapCanvas().extent()
        minx, miny, maxx, maxy = e.xMinimum(),e.yMinimum(),e.xMaximum(),e.yMaximum()
        self.bounds = '%s,%s,%s,%s' % (minx, miny, maxx, maxy)
        if not self.bounds == '0.0,0.0,0.0,0.0':
            self.clipping_area.setText(self.bounds)
        
    def startCommand(self):
        self.first = True
        self.command_output.clear()
        #proj4 = str(self.parent.canvas.mapRenderer().destinationSrs().toProj4()).strip()
        #proj_str = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
        epsg = self.parent.canvas.mapRenderer().destinationSrs().epsg()
        if not epsg == 4326:
            self.err_msg('Projection must be in WGS 84/ESPG 4326 to run this command')
        input = str(self.input.text())
        if not input:
            self.err_msg('Please provide and input .osm (or compressed .osm.bz2) file')
            return False
        if ';' in input:
            input = ' '.join(["%s" % i for i in input.split(';')])
        else:
            input = '"%s"' % input

        style = str(self.style.text())
        if not style:
            style = default_style

        settings = QSettings()
        selected = self.comboBox.currentText()
        settings.beginGroup( u"/PostgreSQL/connections/%s" % selected )
        if not settings.contains("database"): # non-existent entry?
          QMessageBox.critical(self, "Error", "Unable to connect: there is no defined database connection \"%s\"." % selected)
          return
        
        get_value_str = lambda x: unicode(settings.value(x).toString())
        host, db, username, password = map(get_value_str, ["host", "database", "username", "password"])
        port = settings.value("port").toInt()[0]
        if not password and not settings.value("save").toBool():
          (password, ok) = QInputDialog.getText(self, "Enter password", "Enter password for connection (or leave blank) \"%s\":" % selected, QLineEdit.Password)
          if not ok: return

        if not username:
          (username, ok) = QInputDialog.getText(self, "Enter username", "Enter username for connection (or leave blank) \"%s\":" % selected)
          if not ok: return

        settings.endGroup()
        
        # set env
        path = os.environ['PATH']
        if not '/usr/local/bin' in path:
            path += ':/usr/local/bin'
        custom_path = str(osm_tools.get_osm2pgsql_path())
        if custom_path and custom_path not in path:
            path = '%s:%s' % (custom_path,path)
        os.environ['PATH'] = path

        #self.command_output.append('sysenv: %s ' % ','.join([str(i) for i in self.process.systemEnvironment()]))
        cmd = '''osm2pgsql %(input)s -d %(db)s -S "%(style)s"''' % locals()
        if password:
            cmd += ' -W'
        if username:
            cmd += ' -U %s' % username
        if self.use_slim.isChecked():
            cmd += ' --slim'
        if self.srs_choice.currentIndex() == 0:
            cmd += ' -l'
        if self.use_bbox_filter.isChecked():
            # TODO - uninitialized bounds not predicatable across platforms
            if self.bounds == '0.0,0.0,0.0,0.0':
                self.command_output.clear()
                self.err_msg('<span style="color:red;"><b>Please zoom into a relevant area using existing data</b></span>')
                return
            else:
                cmd += ' --bbox %s' % self.bounds
        # requires extending the style file
        # should not be used with hstore support
        if self.use_extra_attributes.isChecked():
            cmd += ' --extra-attributes'

        # not seeing a reason to expose these yet...
        #if self.use_multigeometry.isChecked():
        #    cmd += ' --multi-geometry'
        # Advanced features users will not likely need...
        # We can enable if need be
        #if self.use_hstore.isChecked():
        #    cmd += ' --hstore'
        #if self.radio_append.isChecked():
        #    cmd += ' --append'

        self.command.clear()
        self.command.append(cmd)
        self.process.start(cmd)
        if not self.process.waitForStarted():
            self.err_msg('The command line tool osm2pgsql was not found.<br><br> Either it is not installed correctly or it is not available on your system PATH. <br><br>See OSM Tools > Tool Settings where you can set a custom location for the tool. <br><br>For information on installing osm2pgsql see:<br><br> http://wiki.openstreetmap.org/wiki/Osm2pgsql')
            return

        # TODO, if password is written, stdout stalls
        if password:
            byte_pass = QByteArray()
            byte_pass.append(password)
            self.process.write(byte_pass)
            self.process.closeWriteChannel()