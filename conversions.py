
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
from dateFunctions import dateFunctions


class conversions:
    def __init__(self):
        self.dateTypeTuple = ("date",)
        self.dateIntegerTuple = ("int", "integer", "smallint", "bigint")
        self.dateRealTuple = ("real", "decimal")
        self.dateStringTuple = ("string", "text", "character")
        self.dateFunctions = dateFunctions()
    
    def convertToDate(self, dateValue, field, isStart = True):
#   converts the value in the field to decimal year as a tuple giving the min & max date
        if True:
            if str(dateValue) == 'NULL':
                return None
            elif field.typeName().lower() in self.dateTypeTuple:
                # converts QDate
                return self.dateFunctions.getDecimalYear(int(dateValue.year()),  int(dateValue.month()), int(dateValue.day()))
            elif field.typeName().lower() in self.dateRealTuple:
                return dateValue
            elif field.typeName().lower() in self.dateIntegerTuple:
                return int(dateValue)
            elif field.typeName().lower() in self.dateStringTuple:
                return self.dateFunctions.getDecimalYearFromString(dateValue)
            else:
                QMessageBox.warning(None, "conversions: Cannot use that type of field", "%s;  %s" % (dateValue, field.typeName())) 
                return None
#        except:
#            QMessageBox.warning(None, "conversions: Bad date", "Value: %s; field name: %s; field type: %s" % (dateValue, field.name(), field.typeName()) )
        return None

    def convertToSubsetDateString(self, dateValue, field, dateLength = 10, dateSeparator = "/", isStart = True):
#   converts project decimal year into a date suitable for the subset expession, depending on the type of field
        if field.typeName().lower() in self.dateRealTuple:
            return str(round(dateValue, field.precision()))
        elif field.typeName().lower() in self.dateIntegerTuple:
            return str(int(dateValue + 0.5))
        elif field.typeName().lower() in self.dateTypeTuple:
            if dateValue < 0:
                QMessageBox.warning(None, "ConvertDate: Cannot return date from negative value", "%s" % dateValue) 
                return None        
            else:   
                return self.dateFunctions.getDateSubStringFromDecimalYear(dateValue, "/")
        elif field.typeName().lower() in self.dateStringTuple:
            if dateValue < 0:
                QMessageBox.warning(None, "ConvertDate: Cannot return date from negative value", "%s" % dateValue) 
                return None
            else:
                return self.dateFunctions.getDateSubStringFromDecimalYear(dateValue, dateSeparator if dateLength == 10 else "")
        else:
            QMessageBox.warning(None, "Cannot use that type of field", "%s" % field.typeName()) 
        return None
    
