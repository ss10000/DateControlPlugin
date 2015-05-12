
"""
/***************************************************************************
 dateFunctions
 performs various date conversions allowing decimal dates to be used for BCE years, months, & days
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

from datetime import  date, timedelta
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from qgis.core import QGis, QgsMapLayerRegistry, QgsMapLayer
from PyQt4.QtGui import *


class dateFunctions:
    def __init__(self):
        pass
    
    def getDateFromDayNumber(self, dayNumber):
        dayNumber -= 60
        y = int((10000*dayNumber + 14780)/3652425)
        ddd = dayNumber - (int(365*y) + int(y/4) - int(y/100) + int(y/400))
        if ddd < 0:
            y = y - 1
            ddd = dayNumber - (int(365*y) + int(y/4) - int(y/100) + int(y/400))
        mi = int((100*ddd + 52)/3060)
        mm = (mi + 2) % 12 + 1
        y = y + int((mi + 2)/12)
        dd = ddd - int((mi*306 + 5)/10) + 1
        return (y, mm, dd)                                                            
      
    def getDateSubStringFromDecimalYear(self, decimalDate, separator):
        date1 = self.getDateTupleFromDecimalYear(decimalDate)
        return separator.join((str(date1[0]).zfill(4), str(date1[1]).zfill(2),  str(date1[2]).zfill(2)))

    def getDateFromDecimalYear(self, decimalDate):
        date1 = self.getDateTupleFromDecimalYear(decimalDate)
        return date(date1[0], date1[1], date1[2])

    def getDateFromString(self, stringDate):
        dateFound = None
        try:
            stringDate = stringDate.strip()
            if self.stringDateValid(stringDate):
                if "%s" % stringDate != "NULL":
                    if len(stringDate) == 10:
                        dateFound = date(int(stringDate[0:4]),  int(stringDate[5:7]), int(stringDate[8:10]))
                    elif len(stringDate) == 8:
                        dateFound = date(int(stringDate[0:4]),  int(stringDate[4:6]), int(stringDate[6:8]))
        except:
            QMessageBox.warning(None, "dateFunctions: Bad date", "%s" % stringDate) 
        return dateFound

    def getDateTupleFromDecimalYear(self, decimalDate):
        dayNumber = self.getDayNumberFromDecimalYear(decimalDate)
        return self.getDateFromDayNumber(dayNumber)
        
    def getDayNumber(self, years, months, days):
        y = years
        m = months 
        m = (m + 9) % 12
        y = y - m/10
        return 365*y + y/4 - y/100 + y/400 + (m*306 + 5)/10 + days + 59
        
    def getDayNumberFromDecimalYear(self, decimalDate):
        years = int(decimalDate)
        if float(years) > decimalDate:
            years -= 1
        daysInYear = float(self.isLeapYear(years)[1])
        dayInYear = int(round((float(daysInYear) * (decimalDate - float(years))), 0))
        dayNumber = self.getDayNumber(years, 1, 1)
#        QMessageBox.warning(None, "dIY; dN; dsIY; years,dD", "%s; %s; %s; %s;%s" % (dayInYear, dayNumber, daysInYear, years, decimalDate)) 
        dayNumber += dayInYear
        return dayNumber
           
    def getDecimalYear(self, years, months, days):
        totalDays = float(self.getDayNumber(years, months, days))
        yearDays = float(self.getDayNumber(years, 1, 1))
        daysInYear = float(self.isLeapYear(years)[1])
        return float(years) + (float(totalDays) - float(yearDays)) / float(daysInYear)
        
    def getDecimalYearFromDayNumber(self, dayNumber):
        date1 = self.getDateFromDayNumber(dayNumber)
        return self.getDecimalYear(date1[0], date1[1], date1[2])

    def getDecimalYearFromString(self, stringDate):
        date1 = self.getDateFromString(stringDate)
        if date1 is None:
            return None
        else:
            return self.getDecimalYear(date1.year, date1.month, date1.day)
        
    def isLeapYear(self, years):
        leapYear = False
        if years % 4 == 0:
            if years %100 == 0:
                if years % 400 == 0:
                    leapYear = True
            else:
                leapYear = True
        if leapYear:
            return (leapYear, 366)
        else:
            return (leapYear, 365)
            

    def stringDateValid(self, stringDate, allowNull=True):
        stringDate = "%s" % stringDate
        if stringDate == "NULL":
            if allowNull:
                return True
            else:
                return False
        if len(stringDate) == 0:
            if allowNull:
                return True
            else:
                return False
        if not(len(stringDate) == 10 or len(stringDate) == 8):
            QMessageBox.warning(None, "dateFunctions: Invalid date length", "%s; %s" % (len(stringDate), stringDate)) 
            return False
        try:
            if len(stringDate) == 10:
                dateFound = date(int(stringDate[0:4]),  int(stringDate[5:7]), int(stringDate[8:10]))
                dayNo = self.getDayNumber(int(stringDate[0:4]),  int(stringDate[5:7]), int(stringDate[8:10]))
            else:
                dateFound = date(int(stringDate[0:4]),  int(stringDate[4:6]), int(stringDate[6:8]))
                dayNo = self.getDayNumber(int(stringDate[0:4]),  int(stringDate[4:6]), int(stringDate[6:8]))
            date1 = self.getDateFromDayNumber(dayNo)
            if dateFound != date(date1[0], date1[1], date1[2]):
                QMessageBox.warning(None, "dateFunctions: Invalid date form", "%s; %s; %s-%s-%s" % (stringDate, dayNo, date1[0], date1[1], date1[2])) 
            return dateFound == date(date1[0], date1[1], date1[2])
        except ValueError, e:
            QMessageBox.warning(None, "dateFunctions: Invalid date form", "%s" % (stringDate)) 
            return False
