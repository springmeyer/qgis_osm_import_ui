INST_DIR = ~/.qgis/python/plugins/qgis-osm-import-ui

PYRCC = pyrcc4
PYUIC = pyuic4

RC_PY_FILE = resources_rc.py

all: command_dock_ui.py command_dock_ui2.py dialog_settings_ui.py $(RC_PY_FILE)

install: all
	mkdir -p $(INST_DIR)
	cp *.py $(INST_DIR)/
	cp *.style $(INST_DIR)/
	cp -R osmosis $(INST_DIR)/
	cp -R icons $(INST_DIR)/
	chmod -R 777 $(INST_DIR)/

clean:
	rm -f $(RC_PY_FILE)
	rm -f *.pyc
	rm -f command_dock_ui.py
	rm -f dialog_settings_ui.py
	rm -f command_dock_ui2.py

$(RC_PY_FILE): resources.qrc
	$(PYRCC) -o $(RC_PY_FILE) resources.qrc

command_dock_ui.py: command_dock.ui
	$(PYUIC) -o command_dock_ui.py command_dock.ui

dialog_settings_ui.py: dialog_settings.ui
	$(PYUIC) -o dialog_settings_ui.py dialog_settings.ui
	
command_dock_ui2.py: command_dock2.ui
	$(PYUIC) -o command_dock_ui2.py command_dock2.ui
