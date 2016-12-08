# -*- coding: utf-8 -*-

# QDraw: plugin that makes drawing easier
# Author: Jérémy Kalsron
#         jeremy.kalsron@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4.QtCore import SIGNAL, QTranslator, QSettings, Qt, QPoint, QSize
from PyQt4.QtGui import QAction, QIcon, QDockWidget, QVBoxLayout, QListWidget, QListWidgetItem, QWidget, QToolBar, QColor, QToolButton, QMenu

from qgis.core import *
from qgis.gui import *

import os
import resources

class AnnotationManager:

    def __init__(self, iface):
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            os.path.dirname(__file__),
            'i18n',
            'annotationManager_{}.qm'.format(locale))
        
        self.translator = None
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            QCoreApplication.installTranslator(self.translator)
    
        self.iface = iface
        self.iface.projectRead.connect(self.projectOpen)
        
        self.dock = QDockWidget(self.tr('Annotations manager') )
        self.manager = QWidget()
        toolbar = QToolBar()
        
        self.annotationList = QListWidget()
        self.annotationList.itemClicked.connect(self.selectAnnotation)
        self.annotationList.itemChanged.connect(self.checkItem)  
        action_refresh = QAction(QIcon(':/plugins/annotationManager/resources/mActionDraw.png'), self.tr('Refresh the annotations list'), self.manager)
        action_refresh.triggered.connect(self.refreshAnnotations)
        action_remove = QAction(QIcon(':/plugins/annotationManager/resources/mActionRemoveAnnotation.png'), self.tr('Remove the selected annotation'), self.manager)
        action_remove.triggered.connect(self.removeAnnotation)

        viewMenu = QMenu()
        action_showAll = QAction(QIcon(':/plugins/annotationManager/resources/mActionShowAll.png'), self.tr('Show all annotations'), self.manager)
        action_showAll.triggered.connect(self.showAll)
        action_hideAll = QAction(QIcon(':/plugins/annotationManager/resources/mActionHideAll.png'), self.tr('Hide all annotations'), self.manager)
        action_hideAll.triggered.connect(self.hideAll)
        viewMenu.addAction(action_showAll)
        viewMenu.addAction(action_hideAll)
        viewButton = QToolButton()
        viewButton.setIcon(QIcon(':/plugins/annotationManager/resources/mActionShowAll.png'))
        viewButton.setPopupMode(2)
        viewButton.setMenu(viewMenu)

        toolbar.addAction(action_refresh)
        toolbar.addAction(action_remove)
        toolbar.addWidget(viewButton)
        toolbar.setIconSize(QSize(16, 16))
        
        p1_vertical = QVBoxLayout()
        p1_vertical.setContentsMargins(0,0,0,0)
        p1_vertical.addWidget(toolbar)
        p1_vertical.addWidget(self.annotationList)
        self.manager.setLayout(p1_vertical)
        
        self.dock.setWidget(self.manager)
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
        self.rb = QgsRubberBand(self.iface.mapCanvas(), QGis.Polygon)
        self.annotations = []
        self.annotationsName = []
        
    def checkItem(self, item):
        row = self.annotationList.row(item)
        self.annotationsName[row] = item.text()
        if item.checkState() == Qt.Checked:
            self.annotations[row].show()
        else:
            self.annotations[row].hide()
            if item.isSelected():
                item.setSelected(False)
                self.rb.reset()
    
    def selectAnnotation(self):
        index = self.annotationList.currentRow()
        self.rb.reset()
        self.rb.setColor(QColor(0,0,255, 128))
        mapTool = QgsMapTool(self.iface.mapCanvas())
        point = self.annotations[index].pos().toPoint()
        pt1 = mapTool.toMapCoordinates(QPoint(point.x()-10, point.y()-10))
        pt2 = mapTool.toMapCoordinates(QPoint(point.x()+10, point.y()+10))
        rect = QgsRectangle(pt1, pt2)
        poly = QgsGeometry().fromRect(rect)
        self.rb.setToGeometry(poly, None)

    def showAll(self):
        count = self.annotationList.count()
        for i in range(count):
            self.annotationList.item(i).setCheckState(Qt.Checked)

    def hideAll(self):
        count = self.annotationList.count()
        for i in range(count):
            self.annotationList.item(i).setCheckState(Qt.Unchecked)
    
    def unload(self):
        del self.dock
        
    def tr(self, message):
        return QCoreApplication.translate('AnnotationManager', message)

    def getAnnotations(self):
        annotations = []
        items = self.iface.mapCanvas().items()
        for item in items:
            if item.data(0) == 'AnnotationItem':
                annotations.append(item)
        return annotations
        
    def refreshAnnotations(self):
        self.annotations = []
        self.annotationsName = []
        for annotation in self.getAnnotations():
            self.annotations.append(annotation)
            title = annotation.document().toPlainText().replace('\n', ' ')
            if len(title) > 40:
                title = title[:40]+'(...)'
            self.annotationsName.append(title)

        i = 0
        to_del = []
        for annotation in self.annotations:
            if annotation not in self.getAnnotations():
                to_del.append(i)
            i += 1
        i = 0
        for index in to_del:
            self.annotations.pop(index)
            self.annotationsName.pop(index)       
        self.annotationList.clearSelection()
        self.annotationList.clear()
        
        # argh
        for annotation in self.annotations:
            item = QListWidgetItem(self.annotationsName[i])
            if annotation.isVisible():
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.annotationList.addItem(item)
            i += 1
        # fin argh
            
    def removeAnnotation(self):
        if len(self.annotationList.selectedItems())>0:
            index = self.annotationList.currentRow()
            self.annotationList.takeItem(index)
            self.annotationList.clearSelection()
            self.annotationList.clearFocus()
            self.iface.mapCanvas().scene().removeItem(self.annotations[index])
            self.annotations.pop(index)
            self.annotationsName.pop(index)
            self.rb.reset()
            
    def projectOpen(self):
        del self.annotations[:]
        del self.annotationsName[:]
        self.refreshAnnotations()
        
    def initGui(self):
        self.refreshAnnotations()
 
