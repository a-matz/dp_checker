# -*- coding: utf-8 -*-
"""
/***************************************************************************
 dpCheckerDialog
                                 A QGIS plugin
 Mit diesem Plugin können Dichtheitsprüfungen des Systems Egger in Kombination mit den Attributen der zugehörigen Haltung auf inhaltlich geprüft werden.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-02-15
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Armin Matzl
        email                : arminmatzl@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import glob
from datetime import datetime
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtCore import Qt, QSignalBlocker
from qgis.PyQt.QtWidgets import QTableWidgetItem
import xml.etree.ElementTree as et
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dp_checker_dialog_base.ui'))


class dpCheckerDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(dpCheckerDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.button_load_dp.clicked.connect(self.load_dp_files)
        self.fileWidget.fileChanged.connect(self.check_dp_path)

        self.combobox_maplayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.combobox_maplayer.layerChanged.connect(self.combobox_haltungnr.setLayer)

        with QSignalBlocker(self.combobox_maplayer):
            self.combobox_maplayer.setCurrentIndex(-1)


    def check_dp_path(self):
        if os.path.isdir(self.fileWidget.filePath()):
            self.button_load_dp.setEnabled(True)
        else:
            self.button_load_dp.setEnabled(False)

    def timestring_to_seconds(self, time_string):
         time = datetime.strptime(time_string, "%H:%M:%S")
         time = time.seconds + time.minute*60 + time.hour*3600
         return time
    
    def load_dp_files(self):
        files = glob.glob(f"{self.fileWidget.filePath()}/*.sew")
        dp_dict = {}
        for dp_file in files:
            xtree = et.parse(dp_file)

            #protocol data
            protocol = xtree.find("document").find("data").find("protocol")
            dp_dict["reach"] = protocol.find("examReach").get("value")
            dp_dict["upperManhole"] = protocol.find("upperManhole").get("value")
            dp_dict["lowerManhole"] = protocol.find("lowerManhole").get("value")
            dp_dict["dn"] =  protocol.find("sewerDn").get("value")
            dp_dict["length"]  = protocol.find("sewerLength").get("value")
            dp_dict["material"] = protocol.find("sewerMaterialAtv").get("value")
            dp_dict["examPassed"] = protocol.find("examPassed").get("value")
            dp_dict["classification"] = protocol.find("classification").get("value")
            #measurement data
            measurement= xtree.find("document").find("data").find("measurement")
            dp_dict["pressureChange"] = measurement.find("pressureChange").get("value")
            dp_dict["calmDuration"] = datetime.strptime(measurement.find("calmDuration").get("value"), "%H:%M:%S")
            dp_dict["examDuration"] = datetime.strptime(measurement.find("examDuration").get("value"),"%H:%M:%S")
            #gps position at stop
            gps_position_string = measurement.find("stop").find("gps").get("value")
            gps_list = gps_position_string.split(" ")
            dp_dict["gps_n"] = gps_list[6]
            dp_dict["gps_e"] = gps_list[10]

            for key, value in dp_dict.items():
                print(f"{key}: {value}")
            self.update_table(dp_dict)
    
    def update_table(self, data):
        with QSignalBlocker(self.table) as block:

            #tabelle.setItemDelegate(delegate)
            self.table.clear()
            self.table.setSortingEnabled(False)
            self.table.setRowCount(0)
            self.table.setColumnCount(len(data))
            self.table.setRowCount(1)        
            
            for i, (key, value) in enumerate(data.items()):
                item = QTableWidgetItem()
                if "Duration" in key:
                    value = value.strftime("%H:%M:%S")
                item.setData(Qt.EditRole, value)
                self.table.setItem(0,i,item)
            
            self.table.setHorizontalHeaderLabels(data.keys())
            #self.table.setColumnHidden(self.attributauswahl.index("fid"), True)
            self.table.resizeColumnsToContents()
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(0,Qt.AscendingOrder)





    