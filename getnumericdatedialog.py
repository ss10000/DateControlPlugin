# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GetDateDialog
 gets a date as years or as a decimal year
                             -------------------
        begin                : 2014-03-05
        copyright            : (C) 2014 by S Sinclair
        email                : ss10000"cam.ac.uk
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
from PyQt4.QtGui import *
from ui_getNumericDate import Ui_dlgGetNumericDate
from dateFunctions import dateFunctions
# create the dialog for zoom to point


class GetNumericDateDialog(QtGui.QDialog, Ui_dlgGetNumericDate):
    def __init__(self, numericDate, minDate=None, maxDate=None, getYears=True):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.getYears = getYears
        self.dateFunctions = dateFunctions()
        if getYears:
            self.spbDateNumber.setDecimals(0)
            self.spbDays.setEnabled(False)
            self.spbMonths.setEnabled(False)
            self.spbYears.setValue(numericDate)
        else:
            dateTuple = self.dateFunctions.getDateTupleFromDecimalYear(numericDate)
            self.spbYears.setValue(dateTuple[0])
            self.spbMonths.setValue(dateTuple[1])
            self.spbDays.setValue(dateTuple[2])
        self.minDate = minDate
        self.maxDate = maxDate
        self.spbDateNumber.setValue(numericDate)
        self.connect(self.spbDays,SIGNAL("valueChanged(int)"), self.setDate)
        self.connect(self.spbMonths,SIGNAL("valueChanged(int)"), self.setDate)
        self.connect(self.spbYears,SIGNAL("valueChanged(int)"), self.setDate)
        self.connect(self.spbDateNumber,SIGNAL("valueChanged(double)"), self.setDateAsDate)
        self.connect(self.spbDateNumber,SIGNAL("valueChanged(int)"), self.setDateAsDate)
        self.connect(self.btnOK, SIGNAL("clicked()"), self.OK)

    def checkDate(self):
        validDate = True
        newDate = self.spbDateNumber.value()
        if not self.minDate is None:
            if newDate < self.minDate:
                validDate = False
                QMessageBox.warning(None, "Invalid date entered", "The date is too early, it must not be earlier than: " +
                                    "%s" % self.maxDate)
        if not self.maxDate is None:
            if newDate > self.maxDate:
                validDate = False
                QMessageBox.warning(None, "Invalid date entered", "The date is too late, it must not be later than: " +
                                    "%s" % self.maxDate)
        if validDate:
            self.newDate = newDate
            QtGui.QDialog.accept(self)
        return validDate
    
    def OK(self):
        if self.checkDate():
            self.newDate = self.spbDateNumber.value()
            QtGui.QDialog.accept(self)

    def setDate(self):
        if self.getYears:
            self.spbDateNumber.setValue(self.spbYears.value())
        else:
            years = self.spbYears.value()
            months = self.spbMonths.value()
            days = self.spbDays.value()
            self.spbDateNumber.setValue(self.dateFunctions.getDecimalYear(int(years),  int(months), int(days)))

    def setDateAsDate(self):
        if self.getYears:
            self.spbYears.setValue(int(self.spbDateNumber.value()))
        else:
            date1 = self.dateFunctions.getDateTupleFromDecimalYear(self.spbDateNumber.value())
            self.spbYears.setValue(date1[0])
            self.spbMonths.setValue(date1[1])
            self.spbDays.setValue(date1[2])

