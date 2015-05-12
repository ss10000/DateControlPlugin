"""
/***************************************************************************
 datecontroldock
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
import time
from datetime import  date, timedelta
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from qgis.core import QGis, QgsMapLayerRegistry, QgsMapLayer
import qgis.utils
from PyQt4.QtGui import *
import os

#from qgis.core import QgsPoint, QgsRectangle, QgsFeatureRequest, QgsFeature
#from qgis.gui import QgsRubberBand

from ui_datecontrol2 import Ui_datecontrol
from getnumericdatedialog import GetNumericDateDialog
from dateFunctions import dateFunctions
from conversions import conversions
from getEventsdialog import GetEventsDialog
from commentarydialog import CommentaryDialog


class DateControlDock(QDockWidget, Ui_datecontrol):
    dockRemoved = pyqtSignal(str)


    def __init__(self, iface, pluginSettingsDic):
        self.iface = iface
        self.pluginSettingsDic = pluginSettingsDic
        QDockWidget.__init__(self)
        self.renderer = self.iface.mapCanvas().mapRenderer()
        self.setupUi(self)
        self.dateFunctions = dateFunctions()
        self.conversions = conversions()
        self.commentary = CommentaryDialog(self.iface)

        self.connect(self.slrDate,SIGNAL("valueChanged(int)"), self.setDateFromSlr)
        self.IgnoreSlrChange = False

        self.connect(self.btnEnd,SIGNAL("clicked()"), self.timeEnd)
        self.connect(self.btnForward,SIGNAL("clicked()"), self.timeForward)
        self.connect(self.btnPause,SIGNAL("clicked()"), self.timePause)
        self.connect(self.btnBack,SIGNAL("clicked()"), self.timeBack)
        self.connect(self.btnStart,SIGNAL("clicked()"), self.timeStart)
        self.connect(self.btnGetCurrentDate,SIGNAL("clicked()"), self.getCurrentDate)
        self.connect(self.btnStartDate,SIGNAL("clicked()"), self.getStartDate)
        self.connect(self.btnEndDate,SIGNAL("clicked()"), self.getEndDate)
        self.connect(self.btnGetEventList,SIGNAL("clicked()"), self.getEventList)
        self.connect(self.btnNextEvent,SIGNAL("clicked()"), self.nextEvent)
        self.connect(self.btnPreviousEvent,SIGNAL("clicked()"), self.previousEvent)
        self.connect(self.btnHelp,SIGNAL("clicked()"), self.help)


        self.connect(self.spbDelay,SIGNAL("valueChanged(int)"), self.setDelay)
        self.connect(self.spbIncrement,SIGNAL("valueChanged(int)"), self.setIncrement)
        self.connect(self.spbRange,SIGNAL("valueChanged(int)"), self.updateForNewDate)
        self.connect(self.cbxUnits, SIGNAL("currentIndexChanged(int)"), self.setIncrement)
        self.textDateLength = 10
        self.textDateSeparator = "/"
        self.eventNo = None
        self.eventList = []
        self.commentaryLayerName = ""

    def closeEvent(self, event):
        self.stopTimer()
        self.resetLayerQueries()
        
    def formatDate(self, myDate):
#   formats date for display as DD:MM:YYYY
        date1 = self.dateFunctions.getDateTupleFromDecimalYear(myDate)
        yearText = str(date1[0]).zfill(4) if myDate >= 0 else str(date1[0])
        if self.dateDisplayFormat == "MonthDayYear":
            return '/'.join((str(date1[1]).zfill(2), str(date1[2]).zfill(2), yearText))
        elif self.dateDisplayFormat == "YearMonthDay":
            return '/'.join((yearText, str(date1[1]).zfill(2),  str(date1[2]).zfill(2)))
        elif self.dateDisplayFormat == "DayMonthYear":
            return '/'.join((str(date1[2]).zfill(2), str(date1[1]).zfill(2),  yearText))
        elif self.dateDisplayFormat == "Year":
            return str(date1[0])
 
    def getCurrentDate(self):
#   allows manual setting of the project date
        activeTimer = self.timer.isActive()
        self.stopTimer()
        newDate = self.getDate(self.currentDate, self.startDate, self.endDate)
        if newDate != self.currentDate:
            self.currentDate = newDate
            self.updateForNewDate()
        if activeTimer:
            self.startTimer()

    def getDate(self, useDate, minDate=None, maxDate=None):
#   uses the appropriate dialog to get the project date
        dlg = GetNumericDateDialog(useDate, minDate, maxDate, self.dateDisplayFormat == "Year")
        dlg.newDate = useDate
        dlg.show()
        # Run the dialog event loop
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            return dlg.newDate
        else:
            return useDate

    def getEndDate(self):
        activeTimer = self.timer.isActive()
        self.stopTimer()
        newEndDate = self.getDate(self.endDate, self.startDate)
        if self.endDate != newEndDate:
            self.endDate = newEndDate
            self.btnEndDate.setText(self.formatDate(self.endDate))
            if self.endDate < self.currentDate:
                self.currentDate = self.endDate
                self.updateForNewDate()
            self.setIncrement()
        if activeTimer:
            self.startTimer()

    def getEndOfRangeDate(self):
        try:
            dayNumber = self.dateFunctions.getDayNumberFromDecimalYear(self.currentDate)
            if self.cbxUnits.currentText() == "Day":
                dayNumber = dayNumber + self.spbRange.value() - 1
                return self.dateFunctions.getDecimalYearFromDayNumber(dayNumber)
            elif self.cbxUnits.currentText() == "Week":
                dayNumber = dayNumber + (7 * self.spbRange.value()) - 1
                return self.dateFunctions.getDecimalYearFromDayNumber(dayNumber)
            else:
                return self.currentDate + self.spbRange.value() - 1
        except:
            self.stopTimer()
            QMessageBox.warning(None, "getEndOfRangeDate name error", "Error: %s" % e)


    def getEventsFromLayerlist(self, layerList):
        self.eventLayerList = layerList
        self.eventList = []
        self.tempEventList = []
        for layerName in self.eventLayerList:
            dataTuple = self.layerDataDic[layerName]
            if len(dataTuple) == 1:
                if dataTuple[0] == "Date fields not found":
                    QMessageBox.warning(None, "Date fields not found for that layer", "Sorry, date fields not in settings and not 'StartDt' and 'EndDt'") 
                    return
            layer = dataTuple[0]
            subsetString = layer.subsetString()
            layer.setSubsetString(dataTuple[1])
            startDateField = dataTuple[4]
            idxStart = layer.fieldNameIndex(dataTuple[2])
            idxEnd = layer.fieldNameIndex(dataTuple[3])
            iter = layer.getFeatures()
            for feature in iter:
                startDate = self.conversions.convertToDate(feature.attributes()[idxStart], startDateField)
                if not startDate is None:
                    self.tempEventList.append([startDate, "S"])
                endDate = self.conversions.convertToDate(feature.attributes()[idxEnd], startDateField, False)
                if not endDate is None:
                    self.tempEventList.append([endDate, "E"])
            layer.setSubsetString(subsetString)
            
        if len(self.tempEventList) > 1:
            self.sortEventList()
            self.eventNo = 0
            self.setDateRange(self.eventList[0][0], self.eventList[len(self.eventList) - 1][0])
            self.btnNextEvent.setEnabled(True)
            self.btnPreviousEvent.setEnabled(True)
            self.updateForNewDate()
        else:
            self.btnNextEvent.setEnabled(False)
            self.btnPreviousEvent.setEnabled(False)
            self.lblEventNo.setText('')
                    
    def getEventList(self):
#   gets the event list to use for the addin from the currently selected layer
        dlg = GetEventsDialog(self.iface, self.layerDataDic)
        dlg.show()
        # Run the dialog event loop
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            self.getEventsFromLayerlist(dlg.eventLayerList)
        else:
            return
            
 
    def getLayerData(self, layer):
#   gets the date fields to use for the layer
        subsetString = layer.subsetString()
        layerName = "%s" % layer.name()
        layerKey = ("layer", layerName)
        idxStart = 0
        if layerKey in self.pluginSettingsDic:
            dateTuple = self.pluginSettingsDic[layerKey]
            startDateFieldName = dateTuple[0]
            endDateFieldName = dateTuple[1]
            idxStart = layer.fieldNameIndex(startDateFieldName)
            idxEnd = layer.fieldNameIndex(endDateFieldName)
            if idxStart == -1:
                QMessageBox.warning(None, "Inconsistent settings", "Field %s is not in layer %s" % (startDateFieldName, layerName))
                return ("Error",)
            if idxEnd == -1:
                QMessageBox.warning(None, "Inconsistent settings", "Field %s is not in layer %s" % (endDateFieldName, layerName))
                return ("Error",)
            startDateField = layer.pendingFields()[idxStart]
            endDateField = layer.pendingFields()[idxEnd]
            if startDateField.type() != endDateField.type():
                QMessageBox.warning(None, "Inconsistent field types", 
                                        "Field types for the start & end must be the same: %s; %s" % 
                                        (startDateFieldName, endDateFieldName))
                return ("Error",)
        else:
            idxStart = layer.fieldNameIndex('startDt')
            idxEnd = layer.fieldNameIndex('endDt')
            if idxStart == -1 or idxEnd == -1:
                idxStart = layer.fieldNameIndex('startDate')
                idxEnd = layer.fieldNameIndex('endDate')
                if idxStart == -1 or idxEnd == -1:
                    idxStart = layer.fieldNameIndex('Date')
                    idxEnd = layer.fieldNameIndex('Date')
                    if idxStart == -1:
                        return  ("Date fields not found",)
            startDateField = layer.pendingFields()[idxStart]
            endDateField = layer.pendingFields()[idxEnd]
        if startDateField.typeName().lower() in self.conversions.dateStringTuple:
            if self.getTextDateFormat(layer, idxStart) is None:
                self.getTextDateFormat(layer, idxEnd)
        if not startDateField.typeName().lower() in self.conversions.dateIntegerTuple:
            self.yearsOnlyUsed = False
        return (layer, subsetString, "%s" % startDateField.name(), "%s" % endDateField.name(), startDateField, endDateField, (self.textDateLength, self.textDateSeparator))
                
    
    def getLayersData(self):
#   gets the date fields to use for the layers
        self.selectedLayer = self.iface.legendInterface().currentLayer()
        self.layerDataDic = {}
        self.eventList = []
        self.dateDisplayFormat = self.pluginSettingsDic[("dateDisplayFormat", "dateDisplayFormat")]
        self.commentaryLayerSet = False
        self.commentaryLayerFound = False
        if ("Commentary", "CommentaryLayerName") in self.pluginSettingsDic:
            self.commentaryLayerSet = True
            self.commentaryLayerName = self.pluginSettingsDic[("Commentary", "CommentaryLayerName")]
            if ("Commentary", "CommentaryFieldNames") in self.pluginSettingsDic:
                self.commentaryFieldNames = self.pluginSettingsDic[("Commentary", "CommentaryFieldNames")]
        self.yearsOnlyUsed = True
        for layer in self.iface.legendInterface().layers():
            if not layer.type() == QgsMapLayer.VectorLayer:
               continue
            dataTuple = self.getLayerData(layer)
            if len(dataTuple) > 1:
                layerName = "%s" % layer.name()
                self.layerDataDic[layerName] = dataTuple
                if self.commentaryLayerSet:
                    if layerName == self.commentaryLayerName:
                        self.commentaryLayerFound = True
                else:
                    if layerName.lower() == "commentary" and not layer.hasGeometryType():
                        if layer.fieldNameIndex("Commentary") == -1:
                            QMessageBox.warning(None, "Commentary table invalid", layerName + " does not have field 'commentary'")
                        else:
                            self.commentaryLayerFound = True
                            self.commentaryLayerName = layerName
                            self.commentaryFieldNames = "commentary; "
        if self.yearsOnlyUsed:
            self.dateDisplayFormat = "Year"
        if self.commentaryLayerFound:
            self.commentary.setCommentary("")
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.commentary)
        else:
            if self.commentaryLayerSet:
                QMessageBox.warning(None, "Commentary table not found", self.commentaryLayerName)
            
        self.setWindowTitle("Date control")
        self.timer = QTimer()
        self.setTimeUnits()
#        QMessageBox.warning(None, "End date", "%s" % self.endDate)
        self.slrDate.setValue(0)
        self.btnStartDate.setText(self.formatDate(self.startDate))
        self.btnEndDate.setText(self.formatDate(self.endDate))

        self.currentDate = self.startDate
        timedelta1 = self.endDate - self.startDate
        timedelta1 = self.dateFunctions.getDayNumberFromDecimalYear(self.endDate)
        timedelta1 -= self.dateFunctions.getDayNumberFromDecimalYear(self.startDate)
        self.slrDate.setMaximum(timedelta1)

        self.cbxUnits.setCurrentIndex(0)
        self.spbIncrement.setValue(1)
        self.setIncrement()
        self.spbDelay.setValue(10)
        self.setDelay()
        self.timeFlow = 1
        self.updateForNewDate()
        self.eventList = []

        self.btnNextEvent.setEnabled(False)
        self.btnPreviousEvent.setEnabled(False)
        self.connect(self.timer, SIGNAL("timeout()"), self.updateTime)
        
        if not self.selectedLayer is None:
            if self.selectedLayer.name() in self.layerDataDic:
                self.getEventsFromLayerlist([self.selectedLayer.name()])
        if len(self.eventList) == 0:
            if self.commentaryLayerFound:
                self.getEventsFromLayerlist([self.commentaryLayerName])
            elif len(self.layerDataDic) > 0:
                self.getEventsFromLayerlist([self.layerDataDic.keys()[0]])


    def getNumericDate(self, useDate, minDate=None, maxDate=None):
        dlg = GetNumericDateDialog(useDate, minDate, maxDate)
        dlg.newDate = useDate
        dlg.show()
        # Run the dialog event loop
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            return dlg.newDate
        else:
            return useDate

    def getPreviousEvent(self):
#   moves the date back to the previous event in the list (from the current project date)
        event = self.eventList[self.eventNo]
        while event[0] < self.currentDate and self.eventNo < len(self.eventList) - 1:
            self.eventNo += 1
            event = self.eventList[self.eventNo]
        while self.eventNo > 0 and event[0] >= self.currentDate and event[0] >= self.startDate:
            self.eventNo -= 1
            event = self.eventList[self.eventNo]
            
    def getStartDate(self):
        activeTimer = self.timer.isActive()
        self.stopTimer()
        newStartDate = self.getDate(self.startDate, None, self.endDate)
        if self.startDate != newStartDate:
            self.startDate = newStartDate
            self.btnStartDate.setText(self.formatDate(self.startDate))
            if self.startDate > self.currentDate:
                self.currentDate = self.startDate
                self.updateForNewDate()
            self.setIncrement()
        if activeTimer:
            self.startTimer()

    def getTextDateFormat(self, layer, idx):
        iter = layer.getFeatures()
        for feature in iter:
            startDate = feature.attributes()[idx]
            if not startDate is None:
                try:
                    startDate = startDate.strip()
                except:
                    continue
                self.textDateLength  = len(startDate)
                if self.textDateLength == 10:
                    self.textDateSeparator = startDate[4]
                else:
                    self.textDateSeparator = ""
                return True

    def help(self):
        path = os.path.dirname(os.path.realpath(__file__))
        path = path + "\help\HTML\Date Control.html"
        self.iface.openURL("file://" + path,False)
    
    def nextEvent(self):
#   moves the date forward to the next event in the list (from the current project date)
        if not self.eventNo is None:
            event = self.eventList[self.eventNo]
            while event[0] > self.currentDate and self.eventNo  > 0:
                self.eventNo -= 1
                event = self.eventList[self.eventNo]
            while self.eventNo < len(self.eventList) - 1 and event[0] <= self.currentDate and event[0] <= self.endDate:
                self.eventNo += 1
                event = self.eventList[self.eventNo]
            self.currentDate = event[0]
            self.updateForNewDate()

    def previousEvent(self):
#   moves the date back to the previous event in the list (from the current project date)
        if not self.eventNo is None:
            self.getPreviousEvent()
            self.currentDate = self.eventList[self.eventNo][0]
            self.updateForNewDate()

    def resetLayerQueries(self):
        try:
#   resets the layer queries when the addin is closed
            self.stopTimer()
            if not self.layerDataDic is None:
                keys = self.layerDataDic.keys()
                for layerName in keys:
                    dataTuple = self.layerDataDic[layerName]
                    layer = dataTuple[0]
                    layerName2 = "%s" % layer.name()
                    if layerName2 == layerName:
                        layer.setSubsetString(dataTuple[1])
            self.layerDataDic = {}
        except:
            pass
        try:
            self.iface.mapCanvas().refresh()
            self.commentary.close()
        except:
            pass
        
    def setCommentary(self, layer, startField, endField, startFieldName, endFieldName):
        fieldNameList = self.commentaryFieldNames.split("; ")
        idxList = []
        for fieldName in fieldNameList:
            try:
                idx = layer.fieldNameIndex(fieldName.strip("; "))
                if idx != -1:
                    idxList.append(idx)
            except:
                pass
        idxList.sort()
        idxStart = layer.fieldNameIndex(startFieldName)
        idxEnd = layer.fieldNameIndex(endFieldName)
        iter = layer.getFeatures()
        commentary = ""
        commentaryList = []
        fullCommentary = self.formatDate(self.currentDate)+ "\n"
        for feature in iter:
            commentary = ""
            for idx in idxList:
                try:
                    commentary += feature.attributes()[idx] + "; "
                except:
                    pass
            if len(commentary) > 0:
                try:
                    startDate = feature.attributes()[idxStart]
                    startDateTxt = self.formatDate(self.conversions.convertToDate(feature.attributes()[idxStart], startField))
                except:
                    startDate = None
                    startDateTxt = ""
                try:
                    endDateTxt = self.formatDate(self.conversions.convertToDate(feature.attributes()[idxEnd], endField, False))
                except:
                    endDateTxt = ""
                commentaryList.append((startDate, startDateTxt, endDateTxt, commentary))
        commentaryList.sort(key=lambda date: date[0], reverse = True)
        testDate = None
        for dateTuple in commentaryList:
            fullCommentary = fullCommentary + "From " + dateTuple[1] + " to " + dateTuple[2] +"\n" + "%s" % dateTuple[3] + "\n\n"
        self.commentary.setCommentary(fullCommentary)
  
            
    def setDateFromSlr(self):
#   sets the current date from the slider position
        if self.IgnoreSlrChange:
            return
        if self.slrDate.minimum() == self.slrDate.maximum():
            return
        timerActive = self.timer.isActive()
        self.stopTimer()
        fullDateRange = (self.endDate - self.startDate)
        self.currentDate = self.startDate + fullDateRange * self.slrDate.value() / (self.slrDate.maximum() - self.slrDate.minimum())
        self.updateForNewDate()
        if timerActive:
            self.startTimer()
    
    def setDateRange(self, newStartDate, newEndDate):
        if not newStartDate is None:
            self.startDate = newStartDate
            self.btnStartDate.setText(self.formatDate(self.startDate))
            if self.startDate > self.currentDate:
                self.currentDate = self.startDate
        if not newEndDate is None:
            self.endDate = newEndDate
            self.btnEndDate.setText(self.formatDate(self.endDate))
            if self.endDate < self.currentDate:
                self.currentDate = self.endDate
        if not newStartDate is None:
                self.currentDate = self.startDate
        self.updateForNewDate()
        self.setIncrement()

    def setDelay(self):
        self.timeDelay = 1000 * self.spbDelay.value()
        if self.timer.isActive():
            self.startTimer()

    def setIncrement(self):
        if self.cbxUnits.currentText() == "Day":
            timedelta1 = self.dateFunctions.getDayNumberFromDecimalYear(self.endDate)
            timedelta1 -= self.dateFunctions.getDayNumberFromDecimalYear(self.startDate)
            self.slrDate.setMaximum(timedelta1)
            self.slrDate.setPageStep(7)
            self.timeIncrement = self.spbIncrement.value()
            self.slrDate.setSingleStep(self.timeIncrement)
            self.slrDate.setPageStep(self.timeIncrement * 7)
        elif self.cbxUnits.currentText() == "Week":
            timedelta1 = self.dateFunctions.getDayNumberFromDecimalYear(self.endDate)
            timedelta1 -= self.dateFunctions.getDayNumberFromDecimalYear(self.startDate)
            self.slrDate.setMaximum(int((timedelta1 + 4)/7))
            self.timeIncrement = self.spbIncrement.value() * 7
            self.slrDate.setSingleStep(self.timeIncrement / 7)
            self.slrDate.setPageStep(self.timeIncrement * 4 / 7)
        else:
            self.timeIncrement = self.spbIncrement.value()
            timedelta1 = self.endDate - self.startDate
            self.slrDate.setMaximum(int(timedelta1))
            self.slrDate.setSingleStep(self.timeIncrement)
            self.slrDate.setPageStep(self.timeIncrement * 5)
        if self.spbIncrement.value() > self.spbRange.value():
            self.spbRange.setValue(self.spbIncrement.value())
            
    def setLayerQueries(self):
#   sets the layer queries for the current date range & the field formats & current date format
#        if not self.isVisible():
#            return
        keys = self.layerDataDic.keys()
        for layerName in keys:
            dataTuple = self.layerDataDic[layerName]
#          dataTuple = (layer, subsetString, startDateFieldName, endDateFieldName, startDateField, endDateField, (textDateLength, textDateSeparator))
            layer = dataTuple[0]
            dp = layer.dataProvider()
            dpStorageType = "%s" % dp.storageType().lower()
            originalSubsetString = dataTuple[1]
            startDateFieldName = dataTuple[2]
            endDateFieldName = dataTuple[3]
            startDateField = dataTuple[4]
            endDateField = dataTuple[5]
            subsetString = ""
            if len(dataTuple[1]) > 0:
                subsetString = "(" + dataTuple[1] + ") and "
            endOfRangeDate = self.getEndOfRangeDate()
#          converts the current date to a suitable date string fpr the subset string
            startDateString = self.conversions.convertToSubsetDateString(self.currentDate, startDateField, dataTuple[6][0], dataTuple[6][1], True)
            endDateString = self.conversions.convertToSubsetDateString(endOfRangeDate, endDateField, dataTuple[6][0], dataTuple[6][1], False)
            if startDateFieldName == endDateFieldName:
                gtOperator = ">="
            else:
                gtOperator = ">="
            if startDateString is None or endDateString is None:
                subsetString = subsetString + "False"
            else:
                if startDateField.typeName().lower() in self.conversions.dateTypeTuple :
                    if dpStorageType == 'esri shapefile':
                        subsetString = subsetString + '(cast("' + startDateFieldName + '" as character) <= ' + "'" + endDateString + "'" + ' OR "' + startDateFieldName + '" is NULL)'
                        subsetString = subsetString + " and (cast(" + '"' + endDateFieldName + '" as character) ' + gtOperator + " '" + startDateString + "'" 
                        subsetString = subsetString + ' OR "' + endDateFieldName + '" is NULL)'
                    else:
                        subsetString = subsetString + '("' + startDateFieldName + '" <= ' + "'" + endDateString + "'" + ' OR "' + startDateFieldName + '" is NULL)'
                        subsetString = subsetString + " and (" + '"' + endDateFieldName + '" ' + gtOperator + " '" + startDateString + "'" 
                        subsetString = subsetString + ' OR "' + endDateFieldName + '" is NULL)'
                elif startDateField.typeName().lower() in self.conversions.dateStringTuple :
                    subsetString = subsetString + '("' + startDateFieldName + '" <= ' + "'" + endDateString + "'" + ' OR "' + startDateFieldName + '" is NULL)'
                    subsetString = subsetString + " and (" + '"' + endDateFieldName + '" ' + gtOperator + " '" + startDateString + "'" 
                    subsetString = subsetString + ' OR "' + endDateFieldName + '" is NULL)'
                elif startDateField.typeName().lower() in self.conversions.dateRealTuple or startDateField.typeName().lower() in self.conversions.dateIntegerTuple:
                    subsetString = subsetString + '("' + startDateFieldName + '" <= ' + endDateString  + ' OR "' + startDateFieldName + '" is NULL)'
                    subsetString = subsetString + " and (" + '"' + endDateFieldName + '" ' + gtOperator + " " + startDateString 
                    subsetString = subsetString + ' OR "' + endDateFieldName + '" is NULL)'
            layer.setSubsetString(subsetString)
            if layerName == self.commentaryLayerName:
                self.setCommentary(layer, startDateField, endDateField, startDateFieldName, endDateFieldName)
        self.iface.mapCanvas().refresh()

    def setSlrValueFromDate(self):
#   sets the slider value from the current date
        fullDateRange = (self.endDate - self.startDate)
        if fullDateRange == 0:
            QMessageBox.warning(None, "Date range = 0", "Error: date range for slider = 0")
            return
        self.IgnoreSlrChange = True
        slrDays = (self.currentDate - self.startDate)
        if slrDays < 0:
            self.slrDate.setValue(self.slrDate.minimum())
        elif slrDays > fullDateRange:
            self.slrDate.setValue(self.slrDate.maximum())
        else:
            slrValue  = self.slrDate.minimum() + round(((self.slrDate.maximum() - self.slrDate.minimum()) * slrDays / fullDateRange), 0)
            self.slrDate.setValue(slrValue)
        self.IgnoreSlrChange = False

    def setTimeUnits(self):
        itemsList = []
        self.startDate = 0.0
        self.currentDate = self.startDate
        dateValue = date.today()
        self.endDate = self.dateFunctions.getDecimalYear(dateValue.year,  dateValue.month, dateValue.day)
        if self.dateDisplayFormat == "Year":
            itemsList = ["Year"]
        else:
            itemsList = ["Day", "Week", "Year"]
        self.cbxUnits.clear()
        self.cbxUnits.addItems(itemsList)
       
    def sortEventList(self):
#      sorts dates & creates a list without duplicates
        self.tempEventList.sort(key=lambda date: date[0])
        testDate = None
        for dateTuple in self.tempEventList:
            if len(self.eventList) == 0:
                self.eventList.append(dateTuple)
            else:
                if dateTuple[0] != testDate:
                    self.eventList.append(dateTuple)
            testDate = dateTuple[0]

    def startTimer(self):
        self.stopTimer() 
        self.timer.start(self.timeDelay/10)

    def stopTimer(self):
        if self.timer.isActive():
            self.timer.stop()

    def timeBack(self):
        self.timeFlow = -1
        self.startTimer()
        
    def timeEnd(self):
        self.slrDate.setValue(self.slrDate.maximum())

    def timeForward(self):
        self.timeFlow = 1
        self.startTimer()
        
    def timePause(self):
        self.stopTimer()

    def timeStart(self):
        self.slrDate.setValue(self.slrDate.minimum())

    def updateForNewDate(self):
        endOfRangeDate = self.getEndOfRangeDate()
        self.setWindowTitle(self.formatDate(self.currentDate))
        self.btnGetCurrentDate.setText(self.formatDate(self.currentDate) + " - " + self.formatDate(endOfRangeDate))
        self.setLayerQueries()
        self.setSlrValueFromDate()
        if not self.eventNo is None and len(self.eventList ) > 0:
            if self.currentDate != self.eventList[self.eventNo][0]:
                self.getPreviousEvent()
            self.lblEventNo.setText('%s of\n%s' % (self.eventNo + 1, len(self.eventList)))

    def updateTime(self):
#   sets the current date by incrementing or decrementing using the units & time increment (no of units)
        try:
            if self.cbxUnits.currentText() == "Day" or self.cbxUnits.currentText() == "Week":
                currentDays  = self.dateFunctions.getDayNumberFromDecimalYear(self.currentDate)
                currentDays += self.timeFlow * self.timeIncrement
                newDate = self.dateFunctions.getDecimalYearFromDayNumber(currentDays)
            else:
                newDate = self.currentDate + self.timeFlow * self.timeIncrement
            if ((self.endDate - newDate) < 0) or ((self.startDate - newDate) > 0): 
                self.stopTimer()
            else:
                self.currentDate = newDate
            self.updateForNewDate()
        except:
            self.stopTimer()
            QMessageBox.warning(None, "updateTime error", "Error: %s" % e)

       


          
