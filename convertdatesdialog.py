# -*- coding: utf-8 -*-
"""
/***************************************************************************
 convertDateDialog
 converts dates to days or decimal years & derives decimal year fields from text date fields & vice versa
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

import time
from datetime import  date, timedelta
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from qgis.core import QGis, QgsMapLayerRegistry, QgsMapLayer, QgsVectorDataProvider
from PyQt4.QtGui import *
from ui_checkDates import Ui_CheckDates
from dateFunctions import dateFunctions
from conversions import conversions
import os
# create the dialog for zoom to point


class convertDatesDialog(QtGui.QDialog, Ui_CheckDates):
    def __init__(self, iface):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.selectedLayer = self.iface.legendInterface().currentLayer()
        self.dateFunctions = dateFunctions()
        self.conversions = conversions()

        self.connect(self.spbDays,SIGNAL("valueChanged(int)"), self.dateChanged)
        self.connect(self.spbMonths,SIGNAL("valueChanged(int)"), self.monthChanged)
        self.connect(self.spbYears,SIGNAL("valueChanged(int)"), self.dateChanged)
        
        self.connect(self.spbDayNumber,SIGNAL("valueChanged(int)"), self.dayNumberChanged)
        self.connect(self.spbDecimalYear,SIGNAL("valueChanged(double)"), self.decimalYearChanged)
        
        self.layerList = []
        self.textDateFieldList = []
        self.textDateField = None
        self.textDateFieldIdx = None
        self.decDateField = None
        self.decDateFieldIdx = None
        self.cbxLayer.clear()
            
        self.AddLayersToComboBox(self.cbxLayer, ("vector",), self.layerList)
        layerIndex = 0
        try:
            self.loadFieldsToCBXs(0)
        except:
            pass
        self.connect(self.cbxLayer, SIGNAL("currentIndexChanged(int)"), self.loadFieldsToCBXs)
        self.connect(self.btnUpdateDecDates,SIGNAL("clicked()"), self.updateDecDates)
        self.connect(self.btnUpdateTextDates,SIGNAL("clicked()"), self.updateTextDates)
        self.connect(self.btnIncrementDates,SIGNAL("clicked()"), self.incrementDates)
        self.connect(self.btnHelp,SIGNAL("clicked()"), self.help)
        if not self.selectedLayer is None:
            if self.selectedLayer.type() == QgsMapLayer.VectorLayer:
                self.cbxLayer.setCurrentIndex(self.cbxLayer.findText("%s" % self.selectedLayer.name()))

    def AddFieldsToComboBox(self, layer, cbx, typeList = None, fieldList = None):
        cbx.clear()
        for idx, field in enumerate(layer.pendingFields()):
#            QMessageBox.warning(None, "Field type", "%s; %s" % (field.name(), field.typeName())) 
            if typeList == None or ("%s" % field.typeName()).lower() in typeList:
                fieldName = field.name()
                cbx.addItem(fieldName)
                if not fieldList is None:
                    fieldList.append((idx, field))

    def AddLayersToComboBox(self, cbx, typeList = None, layerList = None):
        currentLayerName = ""
        for layer in self.iface.legendInterface().layers():
            if layer.type() == QgsMapLayer.VectorLayer:
                if typeList == None or "vector" in typeList:
                    if not layerList is None:
                        layerList.append(layer)
                    layerName = "%s" % layer.name()
                    cbx.addItem(layerName)

    def dateChanged(self):
        years = self.spbYears.value()
        months = self.spbMonths.value()
        days = self.spbDays.value()
        dayNumber = self.dateFunctions.getDayNumber(years, months, days)
        self.spbDayNumber.setValue(dayNumber)

    def dayNumberChanged(self):
        dayNumber = self.spbDayNumber.value()
        dateFromDayNumber = self.dateFunctions.getDateFromDayNumber(dayNumber)
        self.txtDateFromDayNumber.setText("%s:%s:%s" % (dateFromDayNumber[2], dateFromDayNumber[1], dateFromDayNumber[0]))
        years = self.spbYears.value()
        months = self.spbMonths.value()
        days = self.spbDays.value()
        decimalYear = self.dateFunctions.getDecimalYear(years, months, days)
        self.spbDecimalYear.setValue(decimalYear)

    def decimalYearChanged(self):
        decimalYear = self.spbDecimalYear.value()
        dayNumberFromDecimalYear = self.dateFunctions.getDayNumberFromDecimalYear(decimalYear)
        dateFromDecimalYear = self.dateFunctions.getDateTupleFromDecimalYear(decimalYear)
        self.txtDayNoFromDecimalYear.setText("%s" % dayNumberFromDecimalYear)
        self.txtDateFromDecimalYear.setText("%s:%s:%s" % (dateFromDecimalYear[2], dateFromDecimalYear[1], dateFromDecimalYear[0]))

    def help(self):
        path = os.path.dirname(os.path.realpath(__file__))
        path = path + "\help\HTML\Convertdates.html"
        self.iface.openURL("file://" + path,False)
        
    def incrementDates(self):
        self.textDateFieldIdx = self.textDateFieldList[self.cbxTextDateField.currentIndex()][0]
        self.textDateField = self.textDateFieldList[self.cbxTextDateField.currentIndex()][1]
        self.decDateFieldIdx = self.decDateFieldList[self.cbxDecDateField.currentIndex()][0]
        self.decDateField = self.decDateFieldList[self.cbxDecDateField.currentIndex()][1]
        caps = self.layer.dataProvider().capabilities()
        if not caps & QgsVectorDataProvider.ChangeAttributeValues:
            QMessageBox.warning(None, "Data provider warning ", "Cannot update data") 

        self.layer.beginEditCommand("Change dec date")
        if self.chkSelectedOnly.isChecked():
            features = self.layer.selectedFeatures()
        else:
            features = self.layer.getFeatures()
        updatedCt = 0
        errorCt = 0
        for feature in features:
            try:
                try:
                    textDate = feature.attributes()[self.textDateFieldIdx].strip()
                except:
                    textDate = None
                if not textDate is None:
                    if len(textDate) == 10:
                        textYear = textDate[0:4]
                        textMonth = textDate[5:7]
                        textDay = textDate[8:10]
                        intYear = int(textYear)
                    else:
                        textYear = textDate[1:5]
                        textMonth = textDate[6:8]
                        textDay = textDate[9:11]
                        intYear = -int(textYear)
                    decDate = self.dateFunctions.getDecimalYear(intYear, int(textMonth), int(textDay))
                    days = self.dateFunctions.getDayNumberFromDecimalYear(decDate) + self.spbDaysIncrement.value()
                    decDate = self.dateFunctions.getDecimalYearFromDayNumber(days)
                    dateTuple = self.dateFunctions.getDateTupleFromDecimalYear(decDate)
                    if decDate < 0:
                        textYear = "-" + ("0000" + "%s" % -dateTuple[0])[-4:]
                    else:
                        textYear = ("0000" + "%s" % dateTuple[0])[-4:]
                    textMonth = ("00" + "%s" % dateTuple[1])[-2:]
                    textDay = ("00" + "%s" % dateTuple[2])[-2:]
                    textDate = textYear + "/" + textMonth + "/" + textDay
#            QMessageBox.warning(None, "Decimal date", "%s" % decDate) 
                    attr = {self.decDateFieldIdx : decDate}
                    self.layer.dataProvider().changeAttributeValues({feature.id() : attr})
                    attr = {self.textDateFieldIdx : textDate}
                    self.layer.dataProvider().changeAttributeValues({feature.id() : attr})
                    updatedCt += 1
            except:
                errorCt += 1
#        self.layer.commitChanges() 
        self.layer.endEditCommand()
        QMessageBox.warning(None, "Updated count", "%s rows updated; %s errors" % (updatedCt, errorCt)) 
        

    def loadFieldsToCBXs(self, index):
#        QMessageBox.warning(None, "LoadFields", "%s" % index) 
        self.textDateFieldList = []
        self.decDateFieldList = []
        self.layer = self.layerList[index]
        self.AddFieldsToComboBox(self.layer, self.cbxTextDateField, self.conversions.dateStringTuple, self.textDateFieldList)
        self.AddFieldsToComboBox(self.layer, self.cbxDecDateField, self.conversions.dateRealTuple, self.decDateFieldList)
        self.txtSelectedCt.setText("%s" % self.layer.selectedFeatureCount())
        self.chkSelectedOnly.setEnabled(self.layer.selectedFeatureCount() > 0)
        self.chkSelectedOnly.setChecked(self.layer.selectedFeatureCount() > 0)

    def monthChanged(self):
        years = self.spbYears.value()
        months = self.spbMonths.value()
        if months == 1 or months == 3 or months == 5 or months == 7 or months == 8 or months == 10 or months == 12:
            self.spbDays.setMaximum(31)
        elif months == 2:
            if self.dateFunctions.isLeapYear(years):
                self.spbDays.setMaximum(29)
            else:
                self.spbDays.setMaximum(28)
        else:
            self.spbDays.setMaximum(30)
        self.dateChanged()        

    def updateDecDates(self):
        self.textDateFieldIdx = self.textDateFieldList[self.cbxTextDateField.currentIndex()][0]
        self.textDateField = self.textDateFieldList[self.cbxTextDateField.currentIndex()][1]
        self.decDateFieldIdx = self.decDateFieldList[self.cbxDecDateField.currentIndex()][0]
        self.decDateField = self.decDateFieldList[self.cbxDecDateField.currentIndex()][1]
        caps = self.layer.dataProvider().capabilities()
        if not caps & QgsVectorDataProvider.ChangeAttributeValues:
            QMessageBox.warning(None, "Data provider warning ", "Cannot update data") 

        self.layer.beginEditCommand("Change dec date")
        if self.chkSelectedOnly.isChecked():
            features = self.layer.selectedFeatures()
        else:
            features = self.layer.getFeatures()
        updatedCt = 0
        errorCt = 0
        for feature in features:
            try:
                try:
                    textDate = feature.attributes()[self.textDateFieldIdx].strip()
                except:
                    textDate = None
                if not textDate is None:
                    if len(textDate) == 10:
                        textYear = textDate[0:4]
                        textMonth = textDate[5:7]
                        textDay = textDate[8:10]
                        intYear = int(textYear)
                    else:
                        textYear = textDate[1:5]
                        textMonth = textDate[6:8]
                        textDay = textDate[9:11]
                        intYear = -int(textYear)
                    decDate = self.dateFunctions.getDecimalYear(intYear, int(textMonth), int(textDay))
#            QMessageBox.warning(None, "Decimal date", "%s" % decDate) 
                    attr = {self.decDateFieldIdx : decDate}
                    self.layer.dataProvider().changeAttributeValues({feature.id() : attr})
                    updatedCt += 1
            except:
                errorCt += 1
#        self.layer.commitChanges() 
        self.layer.endEditCommand()
        QMessageBox.warning(None, "Updated count", "%s rows updated; %s errors" % (updatedCt, errorCt)) 

    def updateTextDates(self):
        self.textDateFieldIdx = self.textDateFieldList[self.cbxTextDateField.currentIndex()][0]
        self.textDateField = self.textDateFieldList[self.cbxTextDateField.currentIndex()][1]
        self.decDateFieldIdx = self.decDateFieldList[self.cbxDecDateField.currentIndex()][0]
        self.decDateField = self.decDateFieldList[self.cbxDecDateField.currentIndex()][1]
        caps = self.layer.dataProvider().capabilities()
        if not caps & QgsVectorDataProvider.ChangeAttributeValues:
            QMessageBox.warning(None, "Data provider warning ", "Cannot update data") 

        self.layer.beginEditCommand("Change text date")
        if self.chkSelectedOnly.isChecked():
            features = self.layer.selectedFeatures()
        else:
            features = self.layer.getFeatures()
        updatedCt = 0
        errorCt = 0
        for feature in features:
            try:
                try:
                    decDate = feature.attributes()[self.decDateFieldIdx]
                except:
                    decDate = None
                dateTuple = self.dateFunctions.getDateTupleFromDecimalYear(decDate)
                if not decDate is None:
                    if decDate < 0:
                        textYear = "-" + ("0000" + "%s" % -dateTuple[0])[-4:]
                    else:
                        textYear = ("0000" + "%s" % dateTuple[0])[-4:]
                    textMonth = ("00" + "%s" % dateTuple[1])[-2:]
                    textDay = ("00" + "%s" % dateTuple[2])[-2:]
                    textDate = textYear + "/" + textMonth + "/" + textDay
#            QMessageBox.warning(None, "Decimal date", "%s" % decDate) 
                    attr = {self.textDateFieldIdx : textDate}
                    self.layer.dataProvider().changeAttributeValues({feature.id() : attr})
                    updatedCt += 1
            except:
                errorCt += 1
#        self.layer.commitChanges() 
        self.layer.endEditCommand()
        QMessageBox.warning(None, "Updated count", "%s rows updated; %s errors" % (updatedCt, errorCt)) 
        
        


