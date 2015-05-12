"""
/***************************************************************************
 getEventsdialog 
                                 A QGIS plugin
 allows layers to be selected to obtain a list of dates 
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
from qgis.core import QGis, QgsMapLayerRegistry, QgsMapLayer
from PyQt4.QtGui import *
from ui_geteventsdlg import Ui_getEventsDialog


class GetEventsDialog(QtGui.QDialog, Ui_getEventsDialog):

    def __init__(self, iface, layerDataDic):
        QtGui.QDialog.__init__(self)
        self.iface = iface
        self.layerDataDic = layerDataDic
        self.renderer = self.iface.mapCanvas().mapRenderer()
        self.setupUi(self)

        self.eventLayerList = []
        tableCt = 0
        self.layerList = []
        self.textDateDetailsDic = {}
        for layer in self.iface.legendInterface().layers():
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue
            if not layer.isValid():
                continue
            layerName = "%s" % layer.name()
            if layerName in self.layerDataDic:
                layerData = self.layerDataDic[layerName]
                self.layerList.append(layerName)
                self.tblLayers.setRowCount(tableCt + 1)
                item = QtGui.QTableWidgetItem(layerName, 0)
                self.tblLayers.setItem(tableCt, 0, item)
                item = QtGui.QTableWidgetItem(layerData[2], 0)
                self.tblLayers.setItem(tableCt, 1, item)
                item = QtGui.QTableWidgetItem(layerData[3], 0)
                self.tblLayers.setItem(tableCt, 2, item)
                tableCt += 1
        self.connect(self.buttonBox, SIGNAL("accepted()"), self, SLOT("accept()"))

        self.itemRow = None
        self.tblLayers.resizeRowsToContents()
        self.tblLayers.resizeColumnsToContents()
        

    def accept(self):
        if not self.createEventLayerList():
            return
        QDialog.accept(self)
        
    def createEventLayerList(self):
        self.eventLayerList = []
        selRangeList = self.tblLayers.selectedRanges()
        if len(selRangeList) > 0:
            for selRange in selRangeList:
                topRow = selRange.topRow()
                while topRow <= selRange.bottomRow():
                    self.eventLayerList.append(self.layerList[topRow])
                    topRow += 1
#            QMessageBox.information(self, "eventLayerList[0]", "%s" % self.eventLayerList[0])
            return True


