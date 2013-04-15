# -*- coding: utf-8 -*-

import os
import sys
import time
import shlex
import tempfile
import platform
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from command_dock_ui import Ui_DockWidget

import osm_tools


currentPath = os.path.dirname( __file__ )
working_dir = os.path.abspath( os.path.join(os.path.dirname( __file__) ) )

class CommandDock(QDockWidget, Ui_DockWidget):
    def __init__(self, parent):
        QDockWidget.__init__(self, parent.iface.mainWindow())
        self.parent = parent
        self.setupUi(self)
        self.add_dropable_path('input',dropable=True)
        self.add_dropable_path('output',dropable=False)

        self.process = QProcess()
        #self.process_in = None
        self.connect(self.go, SIGNAL("clicked()"), self.startCommand)
        self.connect(self.load_from_file, SIGNAL("toggled(bool)"), self.load_method_toggled)
        self.connect(self.load_from_api, SIGNAL("toggled(bool)"), self.load_method_toggled)
        self.connect(self.load_from_xapi, SIGNAL("toggled(bool)"), self.load_method_toggled)
        self.connect(self.parent.canvas, SIGNAL("extentsChanged()"),self.bbox_hook)
        self.connect(self.process, SIGNAL("readyReadStandardOutput()"), self.readOutput)
        self.connect(self.process, SIGNAL("readyReadStandardError()"), self.readErrors)
        self.connect(self.process, SIGNAL("error(QProcess::ProcessError)"), self.catchError)
        self.connect(self.process, SIGNAL("finished(int, QProcess::ExitStatus)"), self.finished)

        #self.connect(self.comboBox, SIGNAL("highlighted(QString)"),self.update_active_db)        
        #self.connect(self.refresh_db_list, SIGNAL("clicked()"), self.listDatabases)
        self.bounds = '0.0,0.0,0.0,0.0'
        # make sure to initialize bounds
        self.bbox_hook()
        #self.input_file()
        #self.output_file()

    def load_method_toggled(self,on):
        if self.load_from_file.isChecked():
           self.input.setEnabled(True)
           self.input_button.setEnabled(True)
        elif self.load_from_api.isChecked() or self.load_from_xapi.isChecked():
           self.input.setEnabled(False)
           self.input_button.setEnabled(False)
           self.use_bbox_filter.setChecked(True)
            
    def err_msg(self,msg):
        err = self.process.errorString()
        if not err:
            err = "Error"
        self.command_output.setHtml('<span style="color:red;"><b>%s: %s</b></span>' % (err,msg))

    def catchError(self,error=None):
        #QMessageBox.information(self.parent.iface.mainWindow(),"error","error")
        self.command_output.setHtml('<span style="color:red;"><b>Error: %s</b></span>' % self.process.errorString())

    def finished(self,code,status):
        #QMessageBox.information(self.parent.iface.mainWindow(),"code","code")
        if 'SEVERE' in self.command_output.toPlainText():
            self.command_output.append(QString('FAILED!'))
        else:
            self.command_output.append(QString('FINISHED!'))
        #self.command_output.append(QString('e: %s %s' % (code,status)))

    def readOutput(self):
        #osm2pgsql sends to stderr
        self.command_output.append(QString(self.process.readAllStandardOutput()))

    def readErrors(self):
        self.command_output.append(QString(self.process.readAllStandardError()))
        
    def path_drag_input(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def path_drag_output(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def path_drop(self,event):
        urls = event.mimeData().urls()
        return str(urls[0].path())

    def path_drop_input(self, event):
        self.input.setText(self.path_drop(event))
        event.acceptProposedAction()

    def path_drop_output(self, event):
        self.output.setText(self.path_drop(event))
        event.acceptProposedAction()

    def add_dropable_path(self,name,dropable=True):
        QObject.connect(getattr(self,'%s_button' % name), SIGNAL("clicked()"), getattr(self,'%s_file' % name))

        if dropable:
            getattr(self,name).__class__.dragEnterEvent = getattr(self,'path_drag_%s' % name)
            getattr(self,name).__class__.dropEvent = getattr(self,'path_drop_%s' % name)
    
    def input_file(self):
        #self.input.setText('/Users/dane/Downloads/latest.osm')
        #return
        val = QFileDialog.getOpenFileNames(None, "Select one or more .osm files to open",osm_tools.get_last_load_dir('osmosis'), "OSM (*.osm *.osm.bz2)")

        if isinstance(val, QStringList):
            text = ';'.join([str(i) for i in val])
            if text:
                self.input.setText(text)
                osm_tools.set_last_load_dir('osmosis',val[0])
        elif str(val):
            self.input.setText(str(val))
            osm_tools.set_last_load_dir('osmosis',str(val))
      
    def output_file(self):
        #self.output.setText('/Users/dane/test.osm')
        #return
        # TODO - should we support outputting to .osm.bz2 ?
        val = QFileDialog.getSaveFileName(None, "Output OSM file",osm_tools.get_last_save_dir('osmosis'), "OSM (*.osm *.bz2)")
        if str(val):
            self.output.setText(str(val))
            osm_tools.set_last_save_dir('osmosis',str(val))
    
    def closeEvent(self, event):
        self.parent.dock_window = None

    def bbox_hook(self):
        e = self.parent.iface.mapCanvas().extent()
        #minx, miny, maxx, maxy = e.xMinimum(),e.yMinimum(),e.xMaximum(),e.yMaximum()
        left,bottom,right,top = e.xMinimum(),e.yMinimum(),e.xMaximum(),e.yMaximum()
        self.bounds = '%s,%s,%s,%s' % (left,bottom,right,top)
        if not self.bounds == '0.0,0.0,0.0,0.0':
            self.clipping_area.setText(self.bounds)

    def startCommand(self):
        self.command_output.clear()

        #proj4 = str(self.parent.canvas.mapRenderer().destinationSrs().toProj4()).strip()
        #proj_str = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
        epsg = self.parent.canvas.mapRenderer().destinationSrs().epsg()
        if not epsg == 4326:
            self.command_output.clear()
            self.command_output.setHtml('<span style="color:red;"><b>Projection must be in WGS 84/ESPG 4326 to run this command</b></span>')
            return
        # TODO - uninitialized bounds not predicatable across platforms
        if self.use_bbox_filter.isChecked() and self.bounds == '0.0,0.0,0.0,0.0':
            self.command_output.clear()
            self.clipping_area.setHtml('<span style="color:red;"><b>Please zoom into a relevant area using existing data</b></span>')
            return
        
        output = str(self.output.text())
        if not output:
            self.command.setHtml('<span style="color:red;"><b>Please provide an output .osm file</b></span>')
            return
        
        osm_tools.set_last_saved_osm_file(output)
        
        # windows
        cmd = 'java -Xmx%sm -cp' % str(self.memory_choice.currentText()).replace(' MB','')
        if os.name == 'nt':
          # pass the full path to the jar files to the classpath arg
          # on windows we must escape quotes
          cmd += ' \"%s\\*\"' % os.path.join(working_dir,'osmosis')
        else:
          cmd += ' "./osmosis/*"'
          # on mac and linux we can just carefree change into the current directory
          self.process.setWorkingDirectory(working_dir)

        cmd += ' org.openstreetmap.osmosis.core.Osmosis '

        e = self.parent.iface.mapCanvas().extent()
        left,bottom,right,top = e.xMinimum(),e.yMinimum(),e.xMaximum(),e.yMaximum()
        
        if self.load_from_file.isChecked():
            input = str(self.input.text())
            if not input:
                self.command.setHtml('<span style="color:red;"><b>Please provide an input .osm file</b></span>')
                return
            #if input.endswith('.bz2'):
            #    cmd += ' --read-xml file=/dev/stdin '
            #    self.process_in = QProcess()
            #    self.process_in.setStandardOutputProcess(self.process)
            #    self.connect(self.process_in, SIGNAL("readyReadStandardOutput()"), self.readOutput)
            #    self.connect(self.process_in, SIGNAL("readyReadStandardError()"), self.readErrors)
            #    self.connect(self.process_in, SIGNAL("error(QProcess::ProcessError)"), self.catchError)
            #    self.connect(self.process_in, SIGNAL("finished(int, QProcess::ExitStatus)"), self.finished)
            #else:
            #    cmd += ' --read-xml file="%(input)s" ' % locals()
            if ';' in input:
                for f in input.split(';'):
                    cmd += ' --read-xml file="%s" ' % f
                for i in range(len(input.split(';'))-1):
                    cmd += ' --merge '
            else:
                cmd += ' --read-xml file="%(input)s" ' % locals()
        
        elif self.load_from_api.isChecked():
            # todo - load from xapi
            cmd += ' --read-api top=%(top)s left=%(left)s bottom=%(bottom)s right=%(right)s ' % locals()

        elif self.load_from_xapi.isChecked():
            # todo - load from xapi
            cmd += ' --read-api url=http://xapi.openstreetmap.org/api/0.6 top=%(top)s left=%(left)s bottom=%(bottom)s right=%(right)s ' % locals()
        
        if self.use_bbox_filter.isChecked():
            cmd += ' --bounding-box top=%(top)s left=%(left)s bottom=%(bottom)s right=%(right)s ' % locals()

        if self.use_polygon_filter.isChecked():
            #lyr = self.parent.iface.activeLayer()
            #feature = lyr.selectedFeatures()[0]
            #wkt = feature.geometry().exportToWkt()
            layersmap = QgsMapLayerRegistry.instance().mapLayers()
            layerslist=[]
            current_layer = self.parent.iface.mapCanvas().currentLayer()
            if not current_layer:
                self.err_msg("No layers selected")
                return
            if not current_layer.type() == current_layer.VectorLayer:
                self.err_msg("Not a vector layer")
                return
            if not current_layer.geometryType() == QGis.Polygon:
                self.err_msg("Not a polygon layer")
                return
            featids = current_layer.selectedFeaturesIds()
            if len(featids) == 0:
                msg = QString("No features selected, using all %s features" % current_layer.featureCount())
                QMessageBox.information(self.parent.iface.mainWindow(),"Warning",msg)
                featids = range(current_layer.featureCount())
            (handle, poly_file) = tempfile.mkstemp(suffix='.poly', prefix='poly-tmp-')
            os.close(handle)

            j=1
            for fid in featids:
               features={}
               result={}
               features[fid] = QgsFeature()
               current_layer.featureAtId(fid,features[fid])
               result[fid] = features[fid].geometry()
               handle = open(poly_file, 'wb')
               handle.write("POLY%s\n" % j)
               handle.write("%s\n" % j)
               i=0
               vertex = result[fid].vertexAt(i)
               while (vertex != QgsPoint(0,0)):
                 handle.write("    %s     %s\n" % (vertex.x(),vertex.y()))
                 i += 1
                 vertex = result[fid].vertexAt(i) 
               handle.write("END" +"\n")
               handle.write("END" +"\n")
               handle.close()
            cmd += ''' --bounding-polygon file="%(poly_file)s" ''' % locals()
        
        cmd += ' --write-xml file="%(output)s" ' % locals()
        #if self.process_in:
        #    cmd_in = 'bzcat %(input)s' % locals()
        #    self.command.append(cmd_in + ' | ')
        #    self.process_in.start(cmd_in)
        # check for vista/windows 7
        if 'vista' in platform.platform().lower():
            # xp gives: Windows-XP-5.1.2600 
            # backup to QProcess (buggy on windows)
            os.system(cmd)
            # todo - actually hit bat script that keeps terminal open
            # so we can see what happened...
            if os.path.exists("%(output)s" % locals()):
                self.command_output.append(QString('FINISHED!, file written to %(output)s' % locals()))
            else:
                self.err_msg('Sorry, the program failed to run.<br><br>Try copying the above command into a separate command prompt and running yourself<br><br>(Start Menu > All Programs > Accessories > Command Prompt)')
                
            #import shlex
            #from subprocess import call, Popen, PIPE
            #resp = Popen(shlex.split(cmd),stdin=PIPE,stderr=PIPE,shell=True)
            #result = resp.communicate(password)
        else:
            self.process.start(cmd)
            if not self.process.waitForStarted():
                self.err_msg('It appears that Java is not installed<br><br>. You likely need to install it from http://www.java.com/en/download/. <br><br>Alternatively, if you have already installed Java, then you need to properly put it on your system PATH. <br><br>See OSM Tools > Tool Settings where you can set a custom location for java.')
                return
    
        self.command.clear()
        self.command.append(cmd)
