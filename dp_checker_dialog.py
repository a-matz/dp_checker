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
import pandas as pd
import numpy as np
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets, QtGui
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

        self.combobox_attribute = [
            self.combobox_haltungnr,
            self.combobox_vonSchacht,
            self.combobox_bisSchacht,
            self.combobox_dn,
            self.combobox_laenge,
            self.combobox_material
        ]

        for combobox in self.combobox_attribute:
            self.combobox_maplayer.layerChanged.connect(combobox.setLayer)
            self.combobox_maplayer.layerChanged.connect(lambda layer, combobox = combobox: self.combobox_reset_index(combobox))
        
        self.combobox_maplayer.setCurrentIndex(-1)
        

    def combobox_reset_index(self,combobox):
        combobox.setCurrentIndex(-1)

    def check_dp_path(self):
        """
        if path is valid enable button to load files
        """
        if os.path.isdir(self.fileWidget.filePath()):
            self.button_load_dp.setEnabled(True)
        else:
            self.button_load_dp.setEnabled(False)

    def timestring_to_seconds(self, time_string):
         time = datetime.strptime(time_string, "%H:%M:%S")
         time = time.seconds + time.minute*60 + time.hour*3600
         return time
    
    def load_dp_files(self):
        """
        load all .sew files
        try to read all attributes - if attribute is not found None is assignes
        combine all files to pandas dataframe and pass it to update_table function
        """
        files = glob.glob(f"{self.fileWidget.filePath()}/*.sew")
        
        # list to store dictionaries 
        df_list = []
        for dp_file in files:
            dp_dict = {}
            xtree = et.parse(dp_file)
            #protocol data
            protocol = xtree.find("document").find("data").find("protocol")
            try:
                dp_dict["Bezeichnung_original"] = protocol.find("examReach").get("value")
            except:
                dp_dict["Bezeichnung_original"] = None
            try:
                dp_dict["Bezeichnung"] = protocol.find("examReach").get("value").split("/")[0].strip()
            except:
                dp_dict["Bezeichnung"] = None
            try:
                dp_dict["Schacht oben"] = protocol.find("upperManhole").get("value")
            except:
                dp_dict["Schacht oben"] = None
            try:
                dp_dict["Schacht unten"] = protocol.find("lowerManhole").get("value")
            except:
                dp_dict["Schacht unten"] = None
            try:
                dp_dict["DN"] = int(protocol.find("sewerDn").get("value"))
            except:
                dp_dict["DN"] = None
            try:
                dp_dict["Länge"]  = round(float(protocol.find("sewerLength").get("value")),2)
            except:
                dp_dict["Länge"] = None
            try:
                dp_dict["Material kürzel"] = protocol.find("sewerMaterialAtv").get("value")
            except:
                dp_dict["Material kürzel"] = None
            try:
                dp_dict["Material"] = protocol.find("sewerMaterial").get("value")
            except:
                dp_dict["Material"] = None
            try:
                dp_dict["Prüfung bestanden"] = bool(protocol.find("examPassed").get("value"))
            except:
                dp_dict["Prüfung bestanden"] = None
            try:
                dp_dict["Ergebnis"] = protocol.find("classification").get("value")
            except:
                dp_dict["Ergebnis"] = None
            #measurement data
            measurement= xtree.find("document").find("data").find("measurement")
            try:
                dp_dict["Druckänderung"] = round(float(measurement.find("pressureChange").get("value")),2)
            except:
                dp_dict["Druckänderung"] = None
            try:
                dp_dict["Prüfdauer"] = datetime.strptime(measurement.find("examDuration").get("value"),"%H:%M:%S")
            except:
                dp_dict["Prüfdauer"] = None
            try:
                dp_dict["Beruhigungszeit"] = datetime.strptime(measurement.find("calmDuration").get("value"), "%H:%M:%S")
            except:
                dp_dict["Beruhigungszeit"] = None

            #gps position at stop
            try:
                gps_position_string = measurement.find("stop").find("gps").get("value")
                gps_list = gps_position_string.split(" ")
                dp_dict["GPS N"] = float(gps_list[6])
                dp_dict["GPS E"] = float(gps_list[10])
            except:
                dp_dict["GPS N"] = None
                dp_dict["GPS E"] = None
            dp_dict["Datei"] = os.path.basename(dp_file)


            df_list.append(dp_dict)
        # create dataframe from list with dictionaries
        self.dp_table = pd.DataFrame(df_list)
        # update tableviewwidget
        self.update_table(self.dp_table)
    
    def update_table(self, data):
        with QSignalBlocker(self.table) as block:

            #tabelle.setItemDelegate(delegate)
            self.table.clear()
            self.table.setSortingEnabled(False)
            self.table.setRowCount(0)
            self.table.setColumnCount(len(data.columns))
            self.table.setRowCount(len(data))        
            
            for i, row in data.iterrows():
                for col,value in enumerate(row):
                    if value != None and not pd.isnull(value):
                        if isinstance(value,pd.datetime):
                            value = value.strftime("%H:%M:%S")
                        item = QTableWidgetItem()
                        
                        #item.setData(Qt.EditRole, value)
                        item.setData(Qt.DisplayRole, value)
                        self.table.setItem(i,col,item)
            
            self.table.setHorizontalHeaderLabels(data.columns.values)
            #self.table.setColumnHidden(self.attributauswahl.index("fid"), True)
            self.table.resizeColumnsToContents()
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(0,Qt.AscendingOrder)





    