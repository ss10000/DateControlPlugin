# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DateControl
                                 A QGIS plugin
 Runs time backwards or forwards allowing vector layers to be displayed according to start & end dates 
                              -------------------
        begin                : 2014-03-05
        copyright            : (C) 2014 by S Sinclair
        email                : ss10000@cam.ac.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This file is part of the DateControl addin.
 *
 *   DateControl is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,
 *      but WITHOUT ANY WARRANTY; without even the implied warranty of
 *      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *      GNU General Public License for more details.
 *   
 *      You should have received a copy of the GNU General Public License
*     along with this program.  If not, see <http://www.gnu.org/licenses/>.

 ***************************************************************************/
/***************************************************************************
 * 
 * The internal (current) date is decimal year.
 * The dates may be displayed as DD/MM/YYYY, MM/DD/YYYY, YYYY/MM/DD, or YYYY
 * DD/MM/YYYY is the default unless all the dates in the layers are integers in which case YYYY is used
 *
 ***************************************************************************/

/***************************************************************************
 * 
 * Date field in the layers may be in the following formats :
 *     date format for dates on or after 0/0/0
 *     integer for years only; no restriction (negative for BCE)
 *     decimal years, implying years, months, days; no restriction (negative for BCE)
 *     text (string) format for dates on or after 0/0/0 formatted as YYYY/MM/DD or YYYYMMDD
 *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from datecontroldock import DateControlDock
from settingsdialog import SettingsDialog
from getsavesettings import GetSaveSettings
from convertdatesdialog import convertDatesDialog
from os import startfile
import os.path


class DateControl:
 
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'datecontrol_{}.qm'.format(locale))
        
        self.proj = QgsProject.instance()
        UriFile = str(self.proj.fileName())
        self.Path = str(os.path.dirname(UriFile))
#        QMessageBox.warning(None, "Path",self.Path)
        self.projName = UriFile[len(self.Path)+1:]

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.setGetSaveSettings()            
        self.dock = DateControlDock(self.iface, self.pluginSettingsDic)
 
    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/datecontrol/DateControlControl.png"), u"Date control", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)
        self.settingsAction = QAction(QIcon(":/plugins/datecontrol/DateControlSettings.png"), u"Settings", self.iface.mainWindow())
        self.settingsAction.triggered.connect(self.showSettings)
        self.convertDatesAction = QAction(QIcon(":/plugins/datecontrol/DateControlCheckDates.png"), u"Convert dates", self.iface.mainWindow())
        self.convertDatesAction.triggered.connect(self.showConvertDates)
#        self.iface.mapCanvas().layersChanged.connect(self.layersChanged)
        self.iface.projectRead.connect(self.changeProject)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addToolBarIcon(self.settingsAction)
        self.iface.addToolBarIcon(self.convertDatesAction)
        self.iface.addPluginToMenu(u"&DateControl", self.action)
        self.iface.addPluginToMenu(u"&DateControl", self.settingsAction)     
        self.iface.addPluginToMenu(u"&DateControl", self.convertDatesAction)     

    def changeProject(self):
        if not QgsProject is None:
            self.proj = QgsProject.instance()
            UriFile = str(self.proj.fileName())
            self.Path = str(os.path.dirname(UriFile))
            self.projName = UriFile[len(self.Path)+1:]
        else:
            self.projName = ""

        self.setGetSaveSettings()
        settingsKeys = self.pluginSettingsDic.keys()
        self.dock = DateControlDock(self.iface, self.pluginSettingsDic)
        self.convertDatesDialog = convertDatesDialog(self.iface)

    def setGetSaveSettings(self):
        self.pluginSettingsDic = {}
        try:
            self.getSaveSettings = GetSaveSettings(self.pluginSettingsDic, self.iface, self.projName, self.Path)
            self.pluginSettingsDic = self.getSaveSettings.getSettings(self.pluginSettingsDic)
        except:
            pass
        self.settingsDialog = SettingsDialog(self.iface, self.pluginSettingsDic, self.projName, self.Path)

# run method that performs all the real work
    def run(self):
        # show the dialog
        self.openDateControlDock()
#        try:
#            self.openDateControlDock()
#        except:
#            pass
 
    def showConvertDates(self):
        self.convertDatesDialog = convertDatesDialog(self.iface)
        self.convertDatesDialog.show()
        # Run the dialog event loop
        self.convertDatesDialog.exec_()
 
    def showSettings(self):
        self.settingsDialog.show()
        # Run the dialog event loop
        if self.settingsDialog.exec_():
            self.pluginSettingsDic = self.settingsDialog.pluginSettingsDic
            self.dock = DateControlDock(self.iface, self.pluginSettingsDic)
 
    def openDateControlDock(self):
        self.dock.getLayersData()
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

    def unload(self):
       # Remove the plugin menu item and icon
        self.dock.resetLayerQueries()
        self.iface.removePluginMenu(u"&DateControl", self.action)
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu(u"&DateControl", self.settingsAction)
        self.iface.removeToolBarIcon(self.settingsAction)
        self.iface.removePluginMenu(u"&DateControl", self.convertDatesAction)
        self.iface.removeToolBarIcon(self.convertDatesAction)
#        QMessageBox.warning(None, "", "Unload end") 

