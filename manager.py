# -*- coding: utf-8 -*-

# AnnotationManager: Dock similar to the layer manager that enables to individually show or hide text annotation.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from qgis.PyQt.QtCore import QTranslator, QSettings, Qt, QPoint, QSize, QCoreApplication, QTranslator, qVersion
from qgis.PyQt.QtGui import QIcon, QColor 
from qgis.PyQt.QtWidgets import QWidget, QDockWidget, QListWidget, QListWidgetItem, QAbstractItemView, QAction, QVBoxLayout, QToolBar, QToolButton, QMenu

from qgis.core import QgsWkbTypes, QgsAnnotationManager, QgsProject, QgsGeometry, QgsRectangle
from qgis.gui import QgsMapTool, QgsRubberBand
import os
from . import resources

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

        if qVersion() > '4.3.3':
            QCoreApplication.installTranslator(self.translator)
    
        self.iface = iface
        self.iface.projectRead.connect(self.projectOpen)
        
        self.dock = QDockWidget(self.tr('Annotations manager') )
        self.manager = QWidget()
        toolbar = QToolBar()
        
        self.annotationList = QListWidget()
        self.annotationList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.annotationList.itemSelectionChanged.connect(self.selectAnnotation)
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
        action_showAllSelected = QAction(QIcon(':/plugins/annotationManager/resources/mActionShowAll.png'), self.tr('Show all selected annotations'), self.manager)
        action_showAllSelected.triggered.connect(self.showAllSelected)
        action_hideAllSelected = QAction(QIcon(':/plugins/annotationManager/resources/mActionHideAll.png'), self.tr('Hide all selected annotations'), self.manager)
        action_hideAllSelected.triggered.connect(self.hideAllSelected)
        viewMenu.addAction(action_showAll)
        viewMenu.addAction(action_hideAll)
        viewMenu.addAction(action_showAllSelected)
        viewMenu.addAction(action_hideAllSelected)
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
        
        self.rb = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)

        self.project = QgsProject.instance()
        self.annotationManager = self.project.annotationManager()
        self.annotationManager.annotationAdded.connect(self.refreshAnnotations)
        self.annotationManager.annotationRemoved.connect(self.refreshAnnotations)
        
    def checkItem(self, item):
        index = self.annotationList.row(item)
        if item.checkState() == Qt.Checked:
            self.annotationManager.annotations()[index].setVisible(True)
        else:
            self.annotationManager.annotations()[index].setVisible(False)
            if item.isSelected():
                item.setSelected(False)
                self.rb.reset(QgsWkbTypes.PolygonGeometry)
    
    def selectAnnotation(self):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(QColor(0,0,255, 128))
        for item in self.annotationList.selectedItems():
            index = self.annotationList.row(item)
            mapTool = QgsMapTool(self.iface.mapCanvas())
            point = mapTool.toCanvasCoordinates(self.annotationManager.annotations()[index].mapPosition())
            pt1 = mapTool.toMapCoordinates(QPoint(point.x()-10, point.y()-10))
            pt2 = mapTool.toMapCoordinates(QPoint(point.x()+10, point.y()+10))
            rect = QgsRectangle(pt1, pt2)
            poly = QgsGeometry().fromRect(rect)
            self.rb.addGeometry(poly, None)

    def showAll(self):
        count = self.annotationList.count()
        for i in range(count):
            self.annotationList.item(i).setCheckState(Qt.Checked)

    def hideAll(self):
        count = self.annotationList.count()
        for i in range(count):
            self.annotationList.item(i).setCheckState(Qt.Unchecked)

    def showAllSelected(self):
        for item in self.annotationList.selectedItems():
            item.setCheckState(Qt.Checked)

    def hideAllSelected(self):
        for item in self.annotationList.selectedItems():
            item.setCheckState(Qt.Unchecked)
    
    def unload(self):
        del self.dock
        
    def tr(self, message):
        return QCoreApplication.translate('AnnotationManager', message)

    def refreshAnnotationTitle(self, annotation=None):
        if annotation is None : annotation = self.project.annotationManager().sender()
        item = self.annotationList.item(self.annotationManager.annotations().index(annotation))
        title = annotation.document().toPlainText().replace('\n', ' ')
        if len(title) > 40:
            title = title[:40]+'(...)'
        item.setText(title)

    def refreshAnnotations(self):
        self.annotationList.clearSelection()
        self.annotationList.clear()
        for annotation in self.annotationManager.annotations():
            item = QListWidgetItem()
            annotation.appearanceChanged.connect(self.refreshAnnotationTitle)
            if annotation.isVisible():
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setFlags(item.flags())
            self.annotationList.addItem(item)
            self.refreshAnnotationTitle(annotation)
            
    def removeAnnotation(self):
        if len(self.annotationList.selectedItems())>0:
            self.annotationManager.annotationRemoved.disconnect()
            trash = []
            for item in self.annotationList.selectedItems():
                index = self.annotationList.row(item)
                trash.append(self.annotationManager.annotations()[index])
            while trash:
                self.annotationManager.removeAnnotation(trash.pop())
            self.refreshAnnotations()
            self.annotationManager.annotationRemoved.connect(self.refreshAnnotations)

    def projectOpen(self):
        self.refreshAnnotations()
        
    def initGui(self):
        self.refreshAnnotations()
 
