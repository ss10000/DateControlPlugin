"""
/***************************************************************************
 settingsdialog
                                 A QGIS plugin
 allows the start & end dates to be selected for vector layers for use in DateControl 
                              -------------------
        begin                : 2014-03-05
        copyright            : (C) 201@cam.ac.uk
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

import time
from datetime import  date, timedelta
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from qgis.core import QGis, QgsMapLayerRegistry, QgsMapLayer
from PyQt4.QtGui import *
from ui_settingsdlg2 import Ui_settingDialog2
from getsavesettings import GetSaveSettings
from dateFunctions import dateFunctions
from conversions import conversions
import os


class SettingsDialog(QtGui.QDialog, Ui_settingDialog2):

    def __init__(self, iface, pluginSettingsDic, projName, path):
# The project settings, if any, for the plugin will have been read & put into pluginSettingsDic
# to initialise this dialog
        QtGui.QDialog.__init__(self)
        self.iface = iface
        self.pluginSettingsDic = pluginSettingsDic
        self.projName = projName
        self.path = path
        self.renderer = self.iface.mapCanvas().mapRenderer()
        self.setupUi(self)
        self.dateFunctions = dateFunctions()
        self.conversions = conversions()

        tableCt = 0
        self.layerList = []
        self.textDateDetailsDic = {}
        self.commentaryLayerName = ""
        self.commentaryFieldNames = ""
        self.rdbDayMonthYearFormat.setChecked(True)
        self.rdbMonthDayYearFormat.setChecked(False)
        self.rdbYearMonthDayFormat.setChecked(False)
        self.rdbYearFormat.setChecked(False)

        if not self.pluginSettingsDic is None:
#          default to dates if not in settings
            settingsKey = ("dateDisplayFormat", "dateDisplayFormat")
            self.dateFormat = "DayMonthYear"
#          default to dates if not in settings
            self.rdbDayMonthYearFormat.setChecked(True)
            if settingsKey in self.pluginSettingsDic:
                self.dateFormat = self.pluginSettingsDic[settingsKey]
                self.rdbDayMonthYearFormat.setChecked(self.dateFormat == "DayMonthYear")
                self.rdbMonthDayYearFormat.setChecked(self.dateFormat == "MonthDayYear")
                self.rdbYearMonthDayFormat.setChecked(self.dateFormat == "YearMonthDay")
                self.rdbYearFormat.setChecked(self.dateFormat == "Year")
#          get the commentary table details
            settingsKey = ("Commentary", "CommentaryLayerName")
            if settingsKey in self.pluginSettingsDic:
                self.commentaryLayerName = self.pluginSettingsDic[settingsKey]
            settingsKey = ("Commentary", "CommentaryFieldNames")
            if settingsKey in self.pluginSettingsDic:
                self.commentaryFieldNames = self.pluginSettingsDic[settingsKey]


#      add the project layers to the table & any date fields in the settings
        for layer in self.iface.legendInterface().layers():
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue
            if not layer.isValid():
                continue
            self.layerList.append(layer)
            self.tblLayerDateData.setRowCount(tableCt + 1)
            layerName = "%s" % layer.name()
            self.tblLayerDateData.setItem(tableCt, 0, QtGui.QTableWidgetItem(layerName, 0))
            if not self.pluginSettingsDic is None:
                settingsKey = ("layer", layerName)
                if settingsKey in self.pluginSettingsDic:
                    dateTuple = self.pluginSettingsDic[settingsKey]
                    if self.checkField(layer, dateTuple[0]):
                        self.tblLayerDateData.setItem(tableCt, 1, QtGui.QTableWidgetItem(dateTuple[0], 0))
                    if self.checkField(layer, dateTuple[1]):
                        self.tblLayerDateData.setItem(tableCt, 2, QtGui.QTableWidgetItem(dateTuple[1], 0))
            if layerName == self.commentaryLayerName:
                self.loadCommentaryFields(layer, self.commentaryFieldNames)
                self.btnSetResetCommentaryLayer.setText("Reset")
            tableCt += 1
        self.tblLayerDateData.resizeRowsToContents()
        self.tblLayerDateData.resizeColumnsToContents()
            
        self.getSaveSettings = GetSaveSettings(self.pluginSettingsDic, self.iface, self.projName, self.path)
        self.connect(self.btnClearDates,SIGNAL("clicked()"), self.clearDates)
        self.connect(self.btnSetStartDate,SIGNAL("clicked()"), self.setStartDate)
        self.connect(self.btnSetEndDate,SIGNAL("clicked()"), self.setEndDate)
        self.connect(self.btnSaveSettings,SIGNAL("clicked()"), self.saveSettings)
        self.connect(self.btnDeleteSettings,SIGNAL("clicked()"), self.deleteSettings)
        self.connect(self.btnSetResetCommentaryLayer,SIGNAL("clicked()"), self.setResetCommentaryLayer)
        self.connect(self.buttonBox, SIGNAL("accepted()"), self, SLOT("accept()"))
        self.connect(self.btnHelp,SIGNAL("clicked()"), self.help)
        
        self.itemRow = None
        self.tblLayerDateData.cellClicked.connect(self.slotItemClicked)
        self.tblLayerDateData.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.fieldType = None
        
        self.datelength = 10
        self.startDatelength = 10
        self.endDatelength = 10
        self.separator = "/"
        self.startSeparator = "/"
        self.endSeparator = "/"

    def AddFieldsToComboBox(self, layer, cbx, typeList = None):
        cbx.clear()
        for idx, field in enumerate(layer.pendingFields()):
            if typeList == None or field.type() in typeList:
                fieldName = field.name()
                cbx.addItem(fieldName)

    def accept(self):
        if not self.createPluginSettingsDic():
            return
        QDialog.accept(self)
        
    def checkCommentaryDetails(self):
        selRangeList = self.tblCommentaryFields.selectedRanges()
        if len(selRangeList) > 0:
            commentaryFieldList = []
            for selRange in selRangeList:
                topRow = selRange.topRow()
                while topRow <= selRange.bottomRow():
                    item = self.tblCommentaryFields.item(topRow, 0)
                    commentaryFieldList.append(item.text())
                    topRow += 1
            self.tblCommentaryFields.clear()
            self.tblCommentaryFields.clearContents()
            self.tblCommentaryFields.setRowCount(len(commentaryFieldList))
            tableCt = 0
            for fieldName in commentaryFieldList:
                item = QtGui.QTableWidgetItem(fieldName, 0)
                item.setBackground(QBrush(QColor(0, 0, 255,255)))
                item.setForeground(QBrush(QColor(255, 255, 0,255)))
                self.tblCommentaryFields.setItem(tableCt, 0, item)
                tableCt += 1
            selRange = QTableWidgetSelectionRange(0, 0, len(commentaryFieldList) - 1, 0)
            self.tblCommentaryFields.setRangeSelected(selRange, True)
            return True
        else:
            return False
        
    def checkField(self, layer, fieldName):
        idx = layer.fieldNameIndex(fieldName)
        if idx == -1:
            QMessageBox.warning(None, "Invalid field name", fieldName + " not in layer " + "%s" % layer.name()) 
            return False
        field = layer.pendingFields()[idx]
        if field.typeName().lower() in self.conversions.dateStringTuple:
            iter = layer.getFeatures()
            initialise = True
            dateLength = 10
            separator = '/'
            for feature in iter:
                dateValue = feature.attributes()[idx]
                try:
                    dateValue = dateValue.strip()
                except:
                    continue 
                if len(dateValue) == 0:
                    continue 
                if initialise:
                    dateLength = len(dateValue)
                    initialise = False
                    if not (dateLength ==10 or dateLength ==8):
                        QMessageBox.warning(None, "Invalid date length", "Must be 10 or 8: %s" % dateValue) 
                        return False
                    if dateLength == 10:
                        separator = dateValue[4]
                    else:
                        separator = ''
                    self.separator = separator
                    self.dateLength = dateLength
                try:
                    if dateLength != len(dateValue):
                        QMessageBox.warning(None, "Inconsistent date lengths", "%s" % dateValue) 
                        return False
                    if dateLength == 10 and separator != dateValue[4]:
                        QMessageBox.warning(None, "Inconsistent separator", "%s, %s, %s" % (separator,  dateValue[4], dateValue)) 
                        return False
                    if dateLength == 10 and separator != dateValue[7]:
                        QMessageBox.warning(None, "Inconsistent separator", "%s, %s, %s" % (separator,  dateValue[7], dateValue)) 
                        return False
                    if not self.dateFunctions.stringDateValid(dateValue):
                        QMessageBox.warning(None, "Invalid date form", "%s" % dateValue) 
                        return False
                except:    
                    QMessageBox.warning(None, "Except: invalid date form", "%s" % dateValue) 
                    return False
        return True
    
    def clearDates(self):
        if len(self.tblLayerDateData.selectedItems())== 0:
            QMessageBox.warning(None, "Selection error", "A layer must be selected")
            return
        self.tblLayerDateData.setItem(self.itemRow, 1, None)
        self.tblLayerDateData.setItem(self.itemRow, 2, None)
           
    def createPluginSettingsDic(self):
        self.pluginSettingsDic = {}
        if self.rdbDayMonthYearFormat.isChecked():
            self.pluginSettingsDic[("dateDisplayFormat", "dateDisplayFormat")] = "DayMonthYear"
        elif self.rdbMonthDayYearFormat.isChecked():
            self.pluginSettingsDic[("dateDisplayFormat", "dateDisplayFormat")] = "MonthDayYear"
        elif self.rdbYearMonthDayFormat.isChecked():
            self.pluginSettingsDic[("dateDisplayFormat", "dateDisplayFormat")] = "YearMonthDay"
        elif self.rdbYearFormat.isChecked():
            self.pluginSettingsDic[("dateDisplayFormat", "dateDisplayFormat")] = "Year"
        if not self.crossCheckFieldTypes():
            QMessageBox.warning(None, "Field error", "Errors must be corrected before settings can be used")
            return False
        rowNo = 0
        while rowNo < self.tblLayerDateData.rowCount():
            if not self.tblLayerDateData.item(rowNo, 0) is None:
                layerName = self.tblLayerDateData.item(rowNo, 0).text()
                if self.tblLayerDateData.item(rowNo, 1) is None and self.tblLayerDateData.item(rowNo, 2) is None:
                    pass
                elif self.tblLayerDateData.item(rowNo, 1) is None or self.tblLayerDateData.item(rowNo, 2) is None:
                    QMessageBox.warning(None, "Date selection error", ("You must enter start & end date (they may be the same), " +
                                   "(layer: %s" % layerName) + ")")
                    self.pluginSettingsDic = {}
                    return self.pluginSettingsDic
                else:
                    startDateField = self.tblLayerDateData.item(rowNo, 1).text()
                    endDateField = self.tblLayerDateData.item(rowNo, 2).text()
                    self.pluginSettingsDic[("layer", "%s" % layerName)] = (startDateField, endDateField)
            rowNo += 1
        if self.btnSetResetCommentaryLayer.text() == "Reset":
            self.pluginSettingsDic[("Commentary", "CommentaryLayerName")] = self.txtCommentaryLayer.text()
            self.pluginSettingsDic[("Commentary", "CommentaryFieldNames")] = self.getCommentaryDetails()
        return True

    def crossCheckFieldTypes(self):
        rowNo = 0
        while rowNo < self.tblLayerDateData.rowCount():
            if not self.tblLayerDateData.item(rowNo, 0) is None:
                layerName = self.tblLayerDateData.item(rowNo, 0).text()
                if self.tblLayerDateData.item(rowNo, 1) is None and self.tblLayerDateData.item(rowNo, 2) is None:
                    pass
                elif self.tblLayerDateData.item(rowNo, 1) is None or self.tblLayerDateData.item(rowNo, 2) is None:
                    QMessageBox.warning(None, "Date selection error", ("You must enter start & end date (they may be the same), " +
                                   "(layer: %s" % layerName) + ")")
                    return False
                else:
                    layer = self.layerList[rowNo]
                    startDateField = self.tblLayerDateData.item(rowNo, 1).text()
                    endDateField = self.tblLayerDateData.item(rowNo, 2).text()
                    idx = layer.fieldNameIndex(startDateField)
                    startField = layer.pendingFields()[idx]
                    idx = layer.fieldNameIndex(endDateField)
                    endField = layer.pendingFields()[idx]
                    if endField.typeName() != startField.typeName():
                        QMessageBox.warning(None, "Date type error", ("Start & end date must be the same type: " +
                                                                      "(layer: %s" % layerName) + ")")
                        return False
                    if endField.typeName()  == 'String':
                        if (layer, "Start") in self.textDateDetailsDic and (layer, "End") in self.textDateDetailsDic:
                            if self.textDateDetailsDic[(layer, "Start")][0] !=  self.textDateDetailsDic[(layer, "End")][0]:
                                QMessageBox.warning(None, "Date type error", ("Start & end date must have the same length: " +
                                                                            "(layer: %s" % layerName) + ")")
                                return False
                            if self.textDateDetailsDic[(layer, "Start")][1] !=  self.textDateDetailsDic[(layer, "End")][1]:
                                QMessageBox.warning(None, "Date type error", ("Start & end date must have the same separator: " +
                                                                            "(layer: %s" % layerName) + ")")
                                return False
                        else:
                            if not self.checkField(layer, startDateField):
                                return False
                            separator = self.separator
                            dateLength = self.dateLength
                            if not self.checkField(layer, endDateField):
                                return False
                            if separator != self.separator:
                                QMessageBox.warning(None, "Date type error", ("Start & end date must have the same separator: " +
                                                                        "(layer: %s" % layerName) + ")")
                                return False
                            if dateLength != self.dateLength:
                                QMessageBox.warning(None, "Date type error", ("Start & end date must have the same length: " +
                                                                            "(layer: %s" % layerName) + ")")
                                return False
                         
            rowNo += 1
        return True

    def deleteSettings(self):
        self.getSaveSettings.deleteSettings()
        
    def getCommentaryDetails(self):
        commentaryFieldNames = ""
        selRangeList = self.tblCommentaryFields.selectedRanges()
        if len(selRangeList) > 0:
            for selRange in selRangeList:
                topRow = selRange.topRow()
                while topRow <= selRange.bottomRow():
                    commentaryFieldNames += self.tblCommentaryFields.item(topRow, 0).text() + "; "
                    topRow += 1
        return commentaryFieldNames
       
    def help(self):
        path = os.path.dirname(os.path.realpath(__file__))
        path = path + "\help\HTML\settings.html"
        self.iface.openURL("file://" + path,False)
    
    def loadCommentaryFields(self, layer, fieldNames = ""):
        self.txtCommentaryLayer.setText(layer.name())
        self.tblCommentaryFields.clear()
        self.tblCommentaryFields.clearContents()
        fieldCt = 0
        for idx, field in enumerate(layer.pendingFields()):
            if field.typeName().lower() in self.conversions.dateStringTuple and field.length() > 15:
                fieldName = field.name()
                if fieldName.lower() + ";" in fieldNames.lower() or fieldNames == "":
                    self.tblCommentaryFields.setRowCount(fieldCt+1)
                    item = QtGui.QTableWidgetItem(fieldName, 0)
                    if fieldNames != "":
                        item.setBackground(QBrush(QColor(0, 0, 255,255)))
                        item.setForeground(QBrush(QColor(255, 255, 0,255)))
                    self.tblCommentaryFields.setItem(fieldCt, 0, item)
                    selRange = QTableWidgetSelectionRange(fieldCt, 0, fieldCt, 0)
                    self.tblCommentaryFields.setRangeSelected(selRange, True)
                    fieldCt += 1
        self.tblCommentaryFields.resizeRowsToContents()
        return

    
    def saveSettings(self):
        if not self.createPluginSettingsDic():
            QMessageBox.warning(None, "Field error", "Errors must be corrected before settings can be used")
            return
        self.getSaveSettings.saveSettings(self.pluginSettingsDic)

    def setEndDate(self):
        if len(self.tblLayerDateData.selectedItems())== 0:
            QMessageBox.warning(None, "Selection error", "A layer must be selected")
            return
        fieldName = self.cbxEndDate.currentText()
        self.checkField(self.layer, fieldName)
        item = QtGui.QTableWidgetItem("%s" % fieldName, 0)
        self.tblLayerDateData.setItem(self.itemRow, 2, item)
        self.textDateDetailsDic[(self.layer, "End")] = (self.datelength, self.separator)
           
    def setResetCommentaryLayer(self):
        if self.btnSetResetCommentaryLayer.text() == "Set":
            if self.checkCommentaryDetails():
                self.btnSetResetCommentaryLayer.setText("Reset")
        else:
            self.txtCommentaryLayer.setText("")
            self.tblCommentaryFields.clear()
            self.tblCommentaryFields.clearContents()
            self.commentaryLayerName = ""
            self.commentaryFieldNames = ""
            self.btnSetResetCommentaryLayer.setText("Set")
        
    def setStartDate(self):
        if len(self.tblLayerDateData.selectedItems())== 0:
            QMessageBox.warning(None, "Selection error", "A layer must be selected")
            return
        fieldName = self.cbxStartDate.currentText()
        self.checkField(self.layer, fieldName)
        item = QtGui.QTableWidgetItem("%s" % fieldName, 0)
        self.tblLayerDateData.setItem(self.itemRow, 1, item)
        self.textDateDetailsDic[(self.layer, "Start")] = (self.datelength, self.separator)
           
    @pyqtSlot(int,int)
    def slotItemClicked(self,itemRow,itemRow2):
        self.processSelectedItem(itemRow)
                
    @pyqtSlot()
    def itemSelectionChanged(self):
        selRangeList = self.tblLayerDateData.selectedRanges()
        if len(selRangeList) == 0:
            pass
        elif len(selRangeList) >1:
            pass
        else:
            for selRange in selRangeList:
                if selRange.topRow() != selRange.bottomRow():
                    pass
                else:
                    self.processSelectedItem(selRange.topRow())

    def processSelectedItem(self, itemRow):
        self.itemRow = itemRow
        item = self.tblLayerDateData.item(itemRow, 0)
        selectedLayerName = item.text()
        self.layer = self.layerList[itemRow]
        self.AddFieldsToComboBox(self.layer, self.cbxStartDate)
        if not self.tblLayerDateData.item(itemRow, 1) is None:
            self.cbxStartDate.setCurrentIndex(self.cbxStartDate.findText(self.tblLayerDateData.item(itemRow, 1).text()))
        self.AddFieldsToComboBox(self.layer, self.cbxEndDate)
        try:
            self.cbxEndDate.setCurrentIndex(self.cbxEndDate.findText(self.tblLayerDateData.item(itemRow, 2).text()))
        except:
            pass
        self.fieldType = None
        if not self.layer.hasGeometryType():
            if self.btnSetResetCommentaryLayer.text() == "Set":
                self.txtCommentaryLayer.setText(selectedLayerName)
                self.loadCommentaryFields(self.layer)


#        QMessageBox.information(self, "Selected layer", "%s" % item.text())

