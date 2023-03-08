# -*- coding: utf-8 -*-
"""
/***************************************************************************
 dpCheckerDialog
                                 A QGIS plugin
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
from datetime import datetime, timedelta, time
import pandas as pd
import numpy as np
import processing
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets, QtGui
from qgis.core import (QgsMapLayerProxyModel, QgsGeometry, 
                      QgsProject, QgsFeature, QgsPoint, edit, QgsVectorLayer,
                      QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsField, QgsPointXY,
                      QgsProcessing, Qgis)
from qgis.gui import QgsFileWidget, QgsMessageBar
from qgis.PyQt.QtCore import Qt, QSignalBlocker, QVariant, pyqtSignal
from qgis.PyQt.QtWidgets import QTableWidgetItem, QDialog, QGridLayout, QLabel, QDialogButtonBox, QMessageBox, QSizePolicy
import xml.etree.ElementTree as et
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dp_checker_dialog_base.ui'))

"""
missing: Check if test method is air and not water
"""

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
        self.bar = QgsMessageBar(self)
        self.bar.setMinimumWidth(1000)
        self.bar.setMaximumWidth(10062)
        self.bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.button_load_dp.clicked.connect(self.load_dp_files)
        self.button_load_dp.clicked.connect(lambda: self.update_filter(only_dp = True))
        self.fileWidget.fileChanged.connect(self.check_dp_path)
        self.button_create_point_layer.clicked.connect(self.create_points)
        self.button_preview_protocol_reach.clicked.connect(lambda checked, preview = True: self.load_reach_protocol(preview))
        self.filepath_reach_protocol.fileChanged.connect(lambda file, button = self.button_preview_protocol_reach: self.check_excel_filepath(file,button, bez_spalten_nr=self.reach_protocol_name.value()))
        self.filepath_dp_protocol.fileChanged.connect(lambda file, button = self.button_preview_dp_protocol: self.check_excel_filepath(file,button, bez_spalten_nr = self.dp_protocol_name.value()))
        self.reach_protocol_name.valueChanged.connect(lambda bez_spalten_nr, button = self.button_preview_protocol_reach: self.check_excel_filepath(self.filepath_reach_protocol.filePath(), button, bez_spalten_nr))
        self.dp_protocol_name.valueChanged.connect(lambda bez_spalten_nr, button = self.button_preview_dp_protocol: self.check_excel_filepath(self.filepath_dp_protocol.filePath(), button, bez_spalten_nr))
        self.button_preview_dp_protocol.clicked.connect(lambda checked, preview = True: self.load_dp_protocol(preview))
        self.button_load_base_data.clicked.connect(lambda checked, preview = True: self.load_base_data_layer(preview))
        self.combobox_haltungnr.currentIndexChanged.connect(self.check_enable_basedata_button)
        self.button_csv_export.clicked.connect(self.select_csv_path)
        self.combobox_filter.currentIndexChanged.connect(self.apply_filter)
        self.button_load_extras.clicked.connect(self.load_and_join_extras)
        self.button_load_extras.clicked.connect(self.update_filter)
        self.group_base_data.toggled.connect(self.check_button_load_extras)
        self.group_lists.toggled.connect(self.check_button_load_extras)
        self.button_ignore_file.clicked.connect(self.ignore_file)
        self.button_open_sew.clicked.connect(self.open_sew_file)
        self.filter_name.textEdited.connect(self.apply_filter)
        self.button_box.helpRequested.connect(self.open_help)

        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #e9e7e3")


        self.combobox_maplayer.setFilters(QgsMapLayerProxyModel.LineLayer)

        self.filepath_reach_protocol.setFilter("Excel (*.xlsx)")
        self.filepath_dp_protocol.setFilter("Excel (*.xlsx)")

        # set default crs
        self.projection.setCrs(QgsCoordinateReferenceSystem(3857))
        self.combobox_attribute = {
            "Bezeichnung" : self.combobox_haltungnr,
            "Schacht oben_Stammdaten" : self.combobox_vonSchacht,
            "Schacht unten_Stammdaten" : self.combobox_bisSchacht,
            "DN_Stammdaten" : self.combobox_dn,
            "Länge_Stammdaten" : self.combobox_laenge,
            "Material_Stammdaten" : self.combobox_material
        }

        for combobox in self.combobox_attribute.values():
            self.combobox_maplayer.layerChanged.connect(combobox.setLayer)
            self.combobox_maplayer.layerChanged.connect(lambda layer, combobox = combobox: self.combobox_reset_index(combobox))
        self.combobox_maplayer.layerChanged.connect(self.reach_expression.setLayer)
        
        self.combobox_maplayer.setCurrentIndex(-1)
        self.combobox_maplayer.layerChanged.connect(self.update_crs)

        #read setvalues to check the tests
        self.setvalues = (pd.read_csv(os.path.join(os.path.dirname(__file__),"dpsollwerte.csv"))
                        .set_index("DN"))
        
        self.filter_list =  []
        #self.addFilter("")
    
    def update_crs(self):
        if self.combobox_maplayer.currentLayer() != None:
            self.projection.setCrs(self.combobox_maplayer.currentLayer().crs())
        else:
            self.projection.setCrs(QgsCoordinateReferenceSystem('EPSG:3857'))

    def combobox_reset_index(self,combobox):
        combobox.setCurrentIndex(-1)
    
    def check_excel_filepath(self, file, button, bez_spalten_nr):
        if os.path.isfile(file) and file.endswith(".xlsx") and bez_spalten_nr != 0:
            button.setEnabled(True)
        else:
            button.setEnabled(False)
        
        self.check_button_load_extras()

    
    def check_enable_basedata_button(self):
        if self.combobox_haltungnr.currentIndex() not in (-1,0) and self.combobox_maplayer.currentLayer != None and self.button_create_point_layer.isEnabled():
            self.button_load_base_data.setEnabled(True)
            self.reach_expression.setEnabled(True)

        else:
            self.button_load_base_data.setEnabled(False)
            self.reach_expression.setEnabled(False)

        self.check_button_load_extras()

    def check_button_load_extras(self):
        if (self.button_preview_protocol_reach.isEnabled() or 
        self.button_preview_dp_protocol.isEnabled() or 
        self.button_load_base_data.isEnabled()) and self.button_load_dp.isEnabled():
            self.button_load_extras.setEnabled(True)
        else:
            self.button_load_extras.setEnabled(False)

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
        self.setCursor(Qt.WaitCursor)
        self.ignored_file_list = []
        files = glob.glob(f"{self.fileWidget.filePath()}/*.sew")
        
        # list to store dictionaries 
        df_list = []
        for dp_file in files:
            dp_dict = {}
            xtree = et.parse(dp_file)
            # sensor media
            protocol = xtree.find("document").find("data").find("sensor").find("media").get("value")
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
            #try:
            #    dp_dict["Prüfung bestanden"] = bool(protocol.find("examPassed").get("value"))
            #except:
            #    dp_dict["Prüfung bestanden"] = None
            try:
                dp_dict["Ergebnis"] = protocol.find("classification").get("value")
            except:
                dp_dict["Ergebnis"] = None
            
            try:
                dp_dict["dp_zulässig"] = round(float(protocol.find("allowedLoss").get("value")),2)
            except:
                dp_dict["dp_zulässig"] = 0
            
            try:
                dp_dict["Prüfdruck"] = int(float(protocol.find("measurementPressure").get("value")))
            except:
                dp_dict["Prüfdruck"] = 0

            #measurement data
            measurement= xtree.find("document").find("data").find("measurement")
            try:
                dp_dict["Druckänderung"] = round(float(measurement.find("pressureChange").get("value")),2)
            except:
                dp_dict["Druckänderung"] = None
            try:
                dp_dict["Prüfzeit"] = datetime.strptime(measurement.find("examDuration").get("value"),"%H:%M:%S").time()
            except:
                dp_dict["Prüfzeit"] = None
            try:
                dp_dict["Beruhigungszeit"] = datetime.strptime(measurement.find("calmDuration").get("value"), "%H:%M:%S").time()
            except:
                dp_dict["Beruhigungszeit"] = None
            
            
            if dp_dict["DN"] != None and dp_dict["Material kürzel"] != None:
                pruef_dn = min(self.setvalues.index, key=lambda x:abs(x-dp_dict["DN"]))
                pruefzeiten = self.setvalues.loc[pruef_dn]
                if dp_dict["dp_zulässig"] == 15 or (dp_dict["dp_zulässig"] == 10 and pruef_dn >= 1100):
                    pruefzeit_factor = 1
                elif dp_dict["dp_zulässig"] == 7.5 or (dp_dict["dp_zulässig"] == 5 and pruef_dn >= 1100):
                    pruefzeit_factor = 0.5


        

                if dp_dict["Material kürzel"].lower() in ("b", "stb", "ob", "pc","pcc", "sfb", "spb", "sb", "szb"):
                    material_col = "beton"
                else:
                    material_col = "andere"

                calm = timedelta(seconds = int(pruefzeiten.beruhigungszeit))
                dp_dict["Beruhigungszeit_soll"] = datetime.strptime(str(calm), "%H:%M:%S").time()
                test_time = timedelta(seconds = int(pruefzeiten[material_col])*pruefzeit_factor)
                dp_dict["Prüfzeit_soll"] = datetime.strptime(str(test_time), "%H:%M:%S").time()
            
            else:
                dp_dict["Beruhigungszeit_soll"] = None
                dp_dict["Prüfzeit_soll"] = None


            #gps position at stop
            try:
                gps_position_string = measurement.find("stop").find("gps").get("value")
                gps_list = gps_position_string.split(" ")
                dp_dict["GPS N"] = float(gps_list[6])
                dp_dict["GPS E"] = float(gps_list[10])
            except:
                dp_dict["GPS N"] = None
                dp_dict["GPS E"] = None
            try:
                date = gps_position_string = measurement.find("end").find("date").get("value")
                dp_dict["Datum"] = datetime.strptime(date, "%Y.%m.%d")
            except:
                dp_dict["Datum"] = None
            try:
                date = gps_position_string = measurement.find("end").find("time").get("value")
                dp_dict["Zeit"] = datetime.strptime(date, "%H:%M:%S").time()
            except:
                dp_dict["Zeit"] = None

            try:
                dp_dict["Bemerkung"] = protocol.find("remarks").get("value")
            except:
                dp_dict["Bemerkung"] = None
            
            try:
                dp_dict["Besonderheit"] = protocol.find("particularities").get("value")
            except:
                dp_dict["Besonderheit"] = None
            
            dp_dict["Datei"] = os.path.basename(dp_file)
            dp_dict["Pfad"] = dp_file


            df_list.append(dp_dict)
        # create dataframe from list with dictionaries
        self.dp_table = pd.DataFrame(df_list)
        # update tableviewwidget
        self.update_table(self.dp_table)
        self.button_create_point_layer.setEnabled(True)
        self.filter_name.setEnabled(True)
        self.check_enable_basedata_button()
        self.setCursor(Qt.ArrowCursor)
        #self.addFilter(["Falsche Beruhigungszeit", "Falsche Prüfzeit","Doppelte Prüfungen"])

        #self.bar.pushMessage("Geladen",f"Es wurden {len(files)} Dateien erfolgreich geladen", level = Qgis.Success, duration = 5)
        self.bar.pushSuccess("Geladen",f"Es wurden {len(files)} Dateien erfolgreich geladen")
        #self.bar.pushSuccess("Geladen",f"<a href= 'C:/temp/test.qgz'> C:/temp  </a>")
    def update_filter(self, preview = False, only_dp = False):
        filter = [""]
        if not preview:
            if self.button_load_dp.isEnabled():
                filter.extend(["Doppelte Prüfungen / Listeineinträge","Falsche Beruhigungszeit","Falsche Prüfzeit","Ergebnis Druckprüfung stimmt nicht mit Druckabfall überein"])
            if not only_dp:
                if self.group_base_data.isChecked() and self.button_load_base_data.isEnabled():
                    filter.extend(["keine Druckprüfung vorhanden","Fehler in Stammdatenabgleich: Länge","Fehler in Stammdatenabgleich: Länge (1m Toleranz)"])
                    if self.combobox_vonSchacht.currentText() != "":
                        filter.append("Fehler in Stammdatenabgleich: Schacht oben")
                    if self.combobox_bisSchacht.currentText() != "":
                        filter.append("Fehler in Stammdatenabgleich: Schacht unten")
                    if self.combobox_dn.currentText() != "":
                        filter.append("Fehler in Stammdatenabgleich: DN")
                    if self.combobox_material.currentText() != "":
                        filter.append("Fehler in Stammdatenabgleich: Material")

                if self.group_lists.isChecked() and self.button_preview_protocol_reach.isEnabled():
                    filter.append("Druckprüfung fehlt - optische Beurteilung vorhanden")

        self.addFilter(filter)

    def addFilter(self, name):
        with QSignalBlocker(self.combobox_filter):
            self.combobox_filter.clear()
            self.filter_list = []
            if isinstance(name, str):
                name = [name]
            for i in name:
                if i not in self.filter_list:
                    self.filter_list.append(i)
                    self.combobox_filter.addItem(i)
            self.combobox_filter.setCurrentIndex(-1)
    
    def update_table(self, data, filter = False, preview = False):
        self.setCursor(Qt.WaitCursor)
        if self.filter_name.text() != "":
            if filter:
                data = data[data.Bezeichnung.str.lower().str.startswith(self.filter_name.text().lower())]
            else:
                with QSignalBlocker(self.filter_name):
                    self.filter_name.setText("")


        if "Pfad" in data.columns:
            data = data[~data["Pfad"].isin(self.ignored_file_list)]
        with QSignalBlocker(self.table):

            #tabelle.setItemDelegate(delegate)
            self.table.clear()
            self.table.setSortingEnabled(False)
            self.table.setRowCount(0)
            self.table.setColumnCount(len(data.columns))
            self.table.setRowCount(len(data))        
            for i, (index,row) in enumerate(data.iterrows()):
                for col,value in enumerate(row):
                    if value != None and not pd.isnull(value):
                        if isinstance(value,pd.datetime):
                            value = value.strftime("%Y-%m-%d")   
                        if isinstance(value, time):
                            value = str(value)
                        item = QTableWidgetItem()
                        
                        #item.setData(Qt.EditRole, value)
                        item.setData(Qt.DisplayRole, value)
                        self.table.setItem(i,col,item)
            
            self.table.setHorizontalHeaderLabels(data.columns.values)
            if "Pfad" in data.columns:
                self.table.setColumnHidden(np.where(data.columns == "Pfad")[0][0], True)
            self.table.resizeColumnsToContents()
            self.table.setSortingEnabled(True)
            if not preview:
                self.table.sortByColumn(0,Qt.AscendingOrder)
        if not filter:
            self.active_table = data
        self.active_view = data
        
        self.button_csv_export.setEnabled(True)

        if "Pfad" in self.active_view.columns:
            self.button_open_sew.setEnabled(True)
            self.button_ignore_file.setEnabled(True)
        else:
            self.button_open_sew.setEnabled(False)
            self.button_ignore_file.setEnabled(False)

        self.setCursor(Qt.ArrowCursor)

    def ignore_file(self):
        row = self.table.currentRow()
        if row >= 0:
            col = self.active_view.columns.get_loc("Pfad")
            try:
                file_name = self.table.item(row,col).text()
                self.ignored_file_list.append(file_name)
                self.update_table(self.active_table)
                self.apply_filter()
            except:
                QMessageBox.warning(self,"Keine Datei gefunden","In der gewählten Zeile ist keine Datei hinterlegt. Vermutlich handelt es sich um einen Eintrag aus den Stammdaten bzw. Excel-Listen zu denen keine Dichtheitsprüfung gefunden wurde.")

    def open_sew_file(self):
        row = self.table.currentRow()
        if row >= 0:
            col = self.active_view.columns.get_loc("Pfad")
            try:
                file_name = self.table.item(row,col).text()
                os.startfile(file_name)
            except:
                QMessageBox.warning(self,"Keine Datei gefunden","In der gewählten Zeile ist keine Datei hinterlegt. Vermutlich handelt es sich um einen Eintrag aus den Stammdaten bzw. Excel-Listen zu denen keine Dichtheitsprüfung gefunden wurde.")


    def create_points(self):
        layer = QgsVectorLayer("point?crs=epsg:4326", "punkte", "memory")
        pr = layer.dataProvider()
        pr.addAttributes(
            [QgsField('Bezeichnung',QVariant.String),
            QgsField('SchachtOben', QVariant.String),
            QgsField('SchachtUnten',QVariant.String),
            QgsField('ErgebnisDP',QVariant.String)]
        )
        layer.updateFields()

        for id,row in self.dp_table.iterrows():
            feat = QgsFeature()
            feat.setAttributes([row["Bezeichnung"],row["Schacht oben"], row["Schacht unten"], row["Ergebnis"]])
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(row["GPS E"], row["GPS N"])))
            with edit(layer):
                layer.addFeature(feat)

        #sourceCrs = QgsCoordinateReferenceSystem(4326)
        #d#estCrs = self.projection.crs()
        #tr = QgsCoordinateTransform(sourceCrs,destCrs, QgsProject.instance())

        alg_params = {
                    'INPUT': layer,
                    'OPERATION': '',
                    'TARGET_CRS': self.projection.crs(),
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}

        out = processing.run('native:reprojectlayer', alg_params)
        out["OUTPUT"].setName("Dichtheitsprüfung")
        QgsProject.instance().addMapLayer(out["OUTPUT"])

    def load_reach_protocol(self, preview):
        self.setCursor(Qt.WaitCursor)
        path = self.filepath_reach_protocol.filePath()
        names = ["Bezeichnung", "Ergebnis OI"]
        skip = self.reach_protocol_skip.value()
        reach_name = self.reach_protocol_name.value()
        result = self.reach_protocol_result.value()

        df = self.load_excel(path, skip, [reach_name,result], names, preview)
        df = df[~df.Bezeichnung.isnull()]
        if not preview:
            return df
        self.setCursor(Qt.ArrowCursor)

    def load_dp_protocol(self,preview):
        self.setCursor(Qt.WaitCursor)
        path = self.filepath_dp_protocol.filePath()
        names = ["Bezeichnung", "Kommentar"]
        skip = self.dp_protocol_skip.value()
        reach_name = self.dp_protocol_name.value()
        comment = self.dp_protocol_comment.value()

        df = self.load_excel(path, skip, [reach_name,comment], names)
        df = df[~df.Bezeichnung.isnull()]
        if not preview:
            return df
        self.setCursor(Qt.ArrowCursor)

    def load_excel(self, path, skip_rows, read_cols,col_names, preview = True):
        """
        path str: Path to .xlsx file
        skip_rows int: number of rows to skip
        read_cols list: list of cols to import
        preview bool: if true loads to tableviewwidget, when fals function returns table
        """
        #col numbers to letters and remove name if colnr = 0
        self.setCursor(Qt.WaitCursor)
        letters_list = [] 
        remove_col = []
        for i,nr in enumerate(read_cols):
            if nr > 0:
                letters_list.append(chr(ord('@') + nr))
            else:
                remove_col.append(i)
        if len(remove_col) > 0:
            [col_names.pop(i) for i in sorted(remove_col, reverse = True)]

        

        letters = ",".join(letters_list)
        df = pd.read_excel(path, skiprows = skip_rows, usecols = letters)
        old_names = df.columns.values
        rename_dict = {}
        for i,old in enumerate(old_names):
            rename_dict[old] = col_names[i]
        
        df.rename(columns = rename_dict, inplace = True)
        if preview:
            self.update_table(df, preview = True)
            self.combobox_filter.clear()
        return df
        self.setCursor(Qt.ArrowCursor)
    
    def select_csv_path(self):
        dlg = saveCSV(self)
        dlg.show()
        dlg.path_selected.connect(self.export_to_csv)
    
    def export_to_csv(self,path):
        if path != None and path != "":
            self.active_view.to_csv(path, sep = ";", decimal = ",", index = False, encoding = "cp1252")

    def load_base_data_layer(self, preview, names_list = None, filter = None):
        """
        names_list = list with all reach names to load
        """
        self.setCursor(Qt.WaitCursor)
        layer = self.combobox_maplayer.currentLayer()
        subset = layer.subsetString()
        if names_list == None:
            names_list = self.dp_table["Bezeichnung"].tolist()
        names = "','".join(names_list)
        if names_list != None and filter == None:
            layer.setSubsetString(f"{self.combobox_haltungnr.currentField()} in ('{names}')")
        elif filter != None:
            layer.setSubsetString(filter)

        if layer.featureCount() == 0:
            QMessageBox.warning(self,"Keine Haltungen gefunden","Zu den aktuell gladenen Druckprüfungen wurde keine Haltungen gefunden.")
            self.combobox_maplayer.setLayer(QgsVectorLayer())
            self.setCursor(Qt.ArrowCursor)
            return None
        # get not emtpy attributes
        attributes = {}
        for name, combobox in self.combobox_attribute.items():
            if combobox.currentField() != "" and combobox.currentField() != None:
                attributes[name] = combobox.currentField()
        if "Länge_Stammdaten" not in attributes.keys():
            length_from_geom = True
        else:
            length_from_geom = False
        
        df_list = []
        for feature in layer.getFeatures():
            row_dict = {}
            for name, attribute in attributes.items():
                row_dict[name] = feature.attribute(attribute)
            if length_from_geom:
                row_dict["Länge_Stammdaten"] = round(feature.geometry().length(),2)
            df_list.append(row_dict)
        df_base_data = pd.DataFrame(df_list)

        layer.setSubsetString(subset)
        if preview:
            self.update_table(df_base_data, preview = True)
            self.combobox_filter.clear()
        else:
            return df_base_data
        self.setCursor(Qt.ArrowCursor)
    
    def apply_filter(self):
        query_name = self.combobox_filter.currentText()

        if query_name == "Falsche Beruhigungszeit":
            query = "Beruhigungszeit < Beruhigungszeit_soll"
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Beruhigungszeit", "Beruhigungszeit_soll",
                            "Prüfzeit", "Prüfzeit_soll","dp_zulässig", "Druckänderung",
                            "DN", "Material kürzel", "Material", "Ergebnis","Bemerkung", "Besonderheit", "Datei","Pfad"]
            df_filter = self.active_table.query(query).loc[:,display_cols]
        elif query_name == "Falsche Prüfzeit":
            query = "Prüfzeit < Prüfzeit_soll"
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Beruhigungszeit", "Beruhigungszeit_soll",
                            "Prüfzeit", "Prüfzeit_soll","dp_zulässig", "Druckänderung",
                            "DN", "Material kürzel", "Material", "Ergebnis","Bemerkung", "Besonderheit", "Datei","Pfad"]
            df_filter = self.active_table.query(query).loc[:,display_cols]

        elif query_name == "Doppelte Prüfungen / Listeineinträge":
            reach = self.active_table["Bezeichnung"]
            df_filter = self.active_table[reach.isin(reach[reach.duplicated()])].query("Datei != None")

        elif query_name == "Fehler in Stammdatenabgleich: DN":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","DN","DN_Stammdaten","Bemerkung", "Besonderheit","Pfad"]
            df_filter = self.active_table[~self.active_table.Datei.isnull()].query("DN != DN_Stammdaten").loc[:,display_cols]

        elif query_name == "Fehler in Stammdatenabgleich: Länge":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Länge","Länge_Stammdaten","Bemerkung", "Besonderheit","Pfad"]
            df_filter = self.active_table[~self.active_table.Datei.isnull()].query("Länge != Länge_Stammdaten").loc[:,display_cols]

        elif query_name == "Fehler in Stammdatenabgleich: Länge (1m Toleranz)":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Länge","Länge_Stammdaten","Bemerkung", "Besonderheit","Pfad"]
            df_filter = self.active_table[~self.active_table.Datei.isnull()].query("(Länge - Länge_Stammdaten) > 1 ").loc[:,display_cols]

        elif query_name == "Fehler in Stammdatenabgleich: Schacht oben":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Schacht oben_Stammdaten"]
            if "Schacht unten_Stammdaten" in self.active_table.columns:
                display_cols.append("Schacht unten_Stammdaten")
            display_cols.extend(["Bemerkung", "Besonderheit","Pfad"])
            df_filter = self.active_table[~self.active_table.Datei.isnull()].query("`Schacht oben` != `Schacht oben_Stammdaten`").loc[:,display_cols]

        elif query_name == "Fehler in Stammdatenabgleich: Schacht unten":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten"]
            if "Schacht oben_Stammdaten" in self.active_table.columns:
                display_cols.append("Schacht oben_Stammdaten")
            display_cols.extend(["Schacht unten_Stammdaten","Bemerkung", "Besonderheit","Pfad"])
            df_filter = self.active_table[~self.active_table.Datei.isnull()].query("`Schacht unten` != `Schacht unten_Stammdaten`").loc[:,display_cols]

        elif query_name == "Fehler in Stammdatenabgleich: Material":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Material kürzel", "Material_Stammdaten","Bemerkung", "Besonderheit","Pfad"]
            df_filter = self.active_table[~self.active_table.Datei.isnull()].query("`Material kürzel` != Material_Stammdaten").loc[:,display_cols]

        elif query_name == "Ergebnis Druckprüfung stimmt nicht mit Druckabfall überein":
            display_cols = ["Bezeichnung","DN","Material","dp_zulässig","Druckänderung","Ergebnis"]
            if "Kommentar" in self.active_table.columns:
                display_cols.append("Kommentar")
            display_cols.extend(["Bemerkung", "Besonderheit","Pfad"])
            df_filter = self.active_table.query("(abs(dp_zulässig)*-1 < Druckänderung and Ergebnis == 'undicht') or (abs(dp_zulässig)*-1 > Druckänderung and Ergebnis == 'dicht')").loc[:,display_cols]

        elif query_name == "Druckprüfung fehlt - optische Beurteilung vorhanden":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Ergebnis","Ergebnis OI", "DN", "Material"]
            if "Kommentar" in self.active_table.columns:
                display_cols.append("Kommentar")
            display_cols.extend(["Bemerkung", "Besonderheit","Pfad"])
            df_filter = self.active_table[(self.active_table["Ergebnis OI"].str.lower() == "optisch dicht") & (self.active_table.Ergebnis.isnull())].loc[:,display_cols]

        elif query_name == "keine Druckprüfung vorhanden":
            display_cols = ["Bezeichnung","Schacht oben", "Schacht unten","Ergebnis","DN", "Material"]
            if "Kommentar" in self.active_table.columns:
                display_cols.append("Kommentar")
            if "Ergebnis OI" in self.active_table.columns:
                display_cols.append("Ergebnis OI")
            display_cols.extend(["Bemerkung", "Besonderheit","Pfad"])
            df_filter = self.active_table[self.active_table.Ergebnis.isnull()].loc[:,display_cols]
        else:
            df_filter = self.active_table

        self.update_table(df_filter, filter = True)


    def load_and_join_extras(self):
        # dp protokolle self.dp_table
        self.setCursor(Qt.WaitCursor)
        tab_show = self.dp_table
        
        
        if self.group_base_data.isChecked() and self.combobox_maplayer.currentLayer() != None:
            if self.reach_expression.currentText == "" or not self.reach_expression.isValidExpression():
                if self.group_lists.isChecked():
                    if os.path.isfile(self.filepath_reach_protocol.filePath()):
                        # excel tv-inspection
                        tv_excel = self.load_reach_protocol(preview = False)
                        tab_show = tab_show.merge(tv_excel, on = "Bezeichnung", how = "outer")
                    if os.path.isfile(self.filepath_dp_protocol.filePath()):
                        # excel dp
                        dp_excel = self.load_dp_protocol(preview = False)
                        tab_show = tab_show.merge(dp_excel, on = "Bezeichnung", how = "outer")
                names = tab_show["Bezeichnung"].tolist()
                df_base_layer = self.load_base_data_layer(preview = False, names_list = np.unique(names).tolist())
                if isinstance(df_base_layer, pd.DataFrame):
                    tab_show = tab_show.merge(df_base_layer, on = "Bezeichnung", how = "outer")
            else:
                df_base_layer = self.load_base_data_layer(preview = False, filter = self.reach_expression.currentText())
                if isinstance(df_base_layer, pd.DataFrame) and len(df_base_layer) > 0:
                    tab_show = tab_show.merge(df_base_layer, on = "Bezeichnung", how = "outer")

                if os.path.isfile(self.filepath_reach_protocol.filePath()):
                    # excel tv-inspection
                    tv_excel = self.load_reach_protocol(preview = False)
                    tab_show = tab_show.merge(tv_excel, on = "Bezeichnung", how = "left")
                if os.path.isfile(self.filepath_dp_protocol.filePath()):
                    # excel dp
                    dp_excel = self.load_dp_protocol(preview = False)
                    tab_show = tab_show.merge(dp_excel, on = "Bezeichnung", how = "left")

        elif self.group_lists.isChecked():
            if os.path.isfile(self.filepath_reach_protocol.filePath()):
                # excel tv-inspection
                tv_excel = self.load_reach_protocol(preview = False)
                tab_show = tab_show.merge(tv_excel, on = "Bezeichnung", how = "outer")
            if os.path.isfile(self.filepath_dp_protocol.filePath()):
                # excel dp
                dp_excel = self.load_dp_protocol(preview = False)
                tab_show = tab_show.merge(dp_excel, on = "Bezeichnung", how = "outer")
        
        self.update_table(tab_show)
        self.setCursor(Qt.ArrowCursor)

    def open_help(self):
        help_file = os.path.join(os.path.dirname(__file__),"help","index.html")
        os.startfile(help_file)
        




        #layer.setSubsetString(subset)

class saveCSV(QDialog):
    path_selected = pyqtSignal(str)
    def __init__(self, parent):
        QDialog.__init__(self, parent)

        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(10,10,10,10)
        self.setWindowTitle("Pfad wählen..")
        
        #Überschrift festlegen
        self.ueberschrift = QLabel()
        self.pfad = QgsFileWidget()
        self.pfad.setStorageMode(3)
        self.pfad.setFilter("Komma-getrennte Werte (*.csv)")
        self.ueberschrift.setText("Pfad wählen..")
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


        self.layout().addWidget(self.ueberschrift,0,0,1,1)
        self.layout().addWidget(self.pfad,1,0,1,1)
        self.layout().addWidget(self.buttonBox,2,0,1,1)
    
    def accept(self):
        self.path_selected.emit(self.pfad.filePath())
        self.close()
        self.deleteLater()
    