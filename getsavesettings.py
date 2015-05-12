"""
/***************************************************************************
 getsavesettings
                                 A QGIS plugin
 saves settings for a particluar project (start & end dates, & date format to use in DateControl) 
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
"""

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from qgis.core import QGis, QgsMapLayer
from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui

class GetSaveSettings():
    
# self.savedSettings are the setting stored in the computer for this project for DateControl

    def __init__(self, pluginSettingsDic, iface, projName, path):
        self.pluginSettingsDic = pluginSettingsDic 
        self.iface = iface
        self.projName = projName
        self.path = path
        self.settingsFileName = self.path + "/" + self.projName + ".settings"
        self.savedSettings = self.readSettings()
 
    def deleteSettings(self):
        try:
            fw = open(self.settingsFileName, 'w')
        except:
            QMessageBox.warning(None, "Cannot open file for write", self.settingsFileName)
            return self.savedSettings
        fw.close()

    def getSettings(self, pluginSettingsDic):
        self.pluginSettingsDic = {}
        if (self.projName + "/" + "dateDisplayFormat") in self.savedSettings:
            self.dateDisplayFormat = self.savedSettings[self.projName + "/" + "dateDisplayFormat"]
        else:
            self.dateDisplayFormat = "DayMonthYear"
        self.pluginSettingsDic[("dateDisplayFormat", "dateDisplayFormat")] = self.dateDisplayFormat 
        
        for layer in self.iface.legendInterface().layers():
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue
#            if layer.hasGeometryType():
#                if not self.iface.legendInterface().isLayerVisible(layer):
#                    continue
            layerName = "%s" % layer.name()
            layerKeyBase = self.projName + "/layer/" + layerName + "/"
            if (layerKeyBase + "StartDate") in  self.savedSettings:
                startDateField = self.savedSettings[layerKeyBase + "StartDate"]
                if (layerKeyBase + "EndDate") in self.savedSettings:
                    endDateField = self.savedSettings[layerKeyBase + "EndDate"]
                    self.pluginSettingsDic[("layer", "%s" % layerName)] = (startDateField, endDateField)
                else:
                    QMessageBox.warning(None, "Error in retrieving settings", "Sorry, settings are inconsistent - please reset")
            else:
                pass           
        if "CommentaryLayerName" in self.savedSettings:
            self.pluginSettingsDic[("Commentary", "CommentaryLayerName")] = self.savedSettings["CommentaryLayerName"] 
        if "CommentaryFieldNames" in self.savedSettings:
            self.pluginSettingsDic[("Commentary", "CommentaryFieldNames")] = self.savedSettings["CommentaryFieldNames"] 
        return self.pluginSettingsDic

    def readSettings(self):
        settingsDic = {}
        try:
            fr = open(self.settingsFileName, 'r')
        except:
            return settingsDic 
        line = 'kk'
        while line != '':
            line = fr.readline().strip(" \n\r")
            if "dateDisplayFormat" in line:
                pos = line.find("dateDisplayFormat")
                dateDisplayFormat = line[pos + 17:]
                settingsDic[self.projName + "/" + "dateDisplayFormat"] = dateDisplayFormat
            elif "StartDate" in line:
                pos = line.find("StartDate")
                startDateFieldName = line[pos+9:]
                settingsDic[line[0:pos+9]] = startDateFieldName
            elif "EndDate" in line:
                pos = line.find("EndDate")
                endDateFieldName = line[pos+7:]
                settingsDic[line[0:pos+7]] = endDateFieldName
            elif "CommentaryLayerName" in line:
                pos = line.find("CommentaryLayerName")
                commentaryLayerName = line[pos+len("CommentaryLayerName"):]
                settingsDic["CommentaryLayerName"] = commentaryLayerName
            elif "CommentaryFieldNames" in line:
                pos = line.find("CommentaryFieldNames")
                commentaryFieldNames = line[pos+len("CommentaryFieldNames"):]
                settingsDic["CommentaryFieldNames"] = commentaryFieldNames
        fr.close()
        return settingsDic 

    def saveSettings(self, pluginSettingsDic):
        self.pluginSettingsDic = pluginSettingsDic 
        self.savedSettings.clear()
        pluginSettingsKeys = self.pluginSettingsDic.keys()
        try:
            fw = open(self.settingsFileName, 'w')
        except:
            QMessageBox.warning(None, "Cannot open file for write", settingFile)
            return self.savedSettings
        for pluginSettingsKey in pluginSettingsKeys:
            settingsType = pluginSettingsKey[0]
            if settingsType == "dateDisplayFormat":
                self.dateDisplayFormat = pluginSettingsDic[pluginSettingsKey]
                fw.write(self.projName + "/" + "dateDisplayFormat" + self.dateDisplayFormat + "\n")
            elif settingsType == "Commentary":
                if pluginSettingsKey[1] == "CommentaryLayerName":
                    layerName = pluginSettingsDic[pluginSettingsKey]
                    fw.write(self.projName + "/" + "CommentaryLayerName" + layerName + "\n")
                if pluginSettingsKey[1] == "CommentaryFieldNames":
                    fieldNames = pluginSettingsDic[pluginSettingsKey]
                    fw.write(self.projName + "/" + "CommentaryFieldNames" + fieldNames + "\n")
            elif settingsType == "layer":
                layerName = pluginSettingsKey[1]
                layerKeyBase = self.projName + "/layer/" + layerName + "/"
                dateTuple = self.pluginSettingsDic[pluginSettingsKey]
                fw.write(layerKeyBase + "StartDate" + dateTuple[0] + "\n")
                fw.write(layerKeyBase + "EndDate" + dateTuple[1] + "\n")
        fw.close()
                
