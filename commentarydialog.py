"""
/***************************************************************************
 commentarydialog 
                                 A QGIS plugin
 accumulates comments for a specified time period in a dockable window 
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
from ui_commentary import Ui_commentary


class CommentaryDialog(QDockWidget, Ui_commentary):

    def __init__(self, iface):
        QDockWidget.__init__(self)
        self.iface = iface
        self.renderer = self.iface.mapCanvas().mapRenderer()
        self.setupUi(self)

    def setCommentary(self, commentary):
        self.brsCommentary.setText(commentary)


