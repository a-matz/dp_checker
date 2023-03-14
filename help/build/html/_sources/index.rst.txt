.. dpChecker documentation master file, created by
   sphinx-quickstart on Sun Feb 12 17:11:03 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Dokumentation zum Dichtheitsprüfung-Checker
============================================

Laden von Dichtheitsprüfungen 
-----------------------------

Bevor alle weiteren Funktionen verwenden werden können, müssen die *.sew*-Dateien der Dichtheitsprüfungen geladen werden.
Durch Klicken auf den |load_btn| Button kann zum gewünschten Ordner navigiert werden. Durch anschließendes Klicken auf *Dichtheitsprüfungen laden*
werdn die einzelnen Dateien ausgelesen und die Tabelle befüllt.

.. |load_btn| image:: /figures/load_button.png


Ignorieren von Prüfungen
-------------------------
Die Funktion steht nur zur Verfügung, wenn kein Filter für die Datenprüfung gewählt wurde.
Duch das Markieren einer Zeile bzw. Zelle der entsprechenden Zeile und anschließendem klicken auf |ignore_btn| wird die gewählte Prüfung in der laufenden 
Bearbeitung ignoriert. Durch erneutes Laden aller *.sew*-Dateien steht sie wieder zur Verfügung. Die Aktion kann nicht rückgängig gemacht werden.

.. |ignore_btn| image:: /figures/ignore_button.png

Erzeugen von Punkten aus GPS-Koordinaten
-----------------------------------------
Nach dem die Prüfungen eingelesen wurden können Punkte auf Basis der gespeicherten GPS-Koordinaten erzeugt werden. Das Koordinatensystem kann dabei vom Benutzer definiert werden.
Wird ein Layer mit Stammdaten geladen, so wird automatisch dessen Koordinatensystem in also Voreinstellung gewählt.

|load_points|

.. |load_points| image:: /figures/load_points.png

Verknüpfen von Stammdaten
--------------------------
Optional können weitere Prüfungen durchgeführt werden, indem Stammdaten und Excel-Listen geladen werden.

*Wichtig* ist, dass die Haltungsbezeichnung eindeutig ist.

Zur inhaltlichen Prüfung können die Dichtheitsprüfungen mit den Stammdaten der Haltung verknüpft werden. Dafür muss der entsprechende Layer in QGis geladen sein. 
Durch die Auswahl des Layers können anschließend die Attributnamen zugewiesen werden. Wichtig ist, dass die Bezeichnung der Haltung gewählt wird.
Die *Haltungslänge* wird aus der Geometrie des Layers ermittelt, sofern kein Attribut zugewiesen wurde.


**Verwenden eines Filter-Ausdrucks**

Wenn *kein* Filter angegeben ist, dann werden nur jene Haltungen geladen, für die eine Dichtheitsprüfung vorhanden ist. Um die Vollständigkeit der Dichtheitsprüfungen
zu kontrollieren, kann ein Filter gesetzt werden. Die optional geladenen Exce-Listen werden als *full-join* mit den Dichtheitsprüfungen verknüpft.
Alle Einträge der Listen sind somit in der geladenen Tabelle enthalten.

Wenn ein Filterausdruck definiert wurde, dann werden Haltungen und Dichtheitsprüfung mittels eines *full-joins* verknüpft. Wird für eine Haltung keine passende
Prüfung gefunden, ist sie trotzdem in der Tabelle ersichtlich. Wenn zusätzlich noch Excel-Listen geladen werden, dann werden diese als *left-join* verknüpft:
Sollte eine Haltung in einer Excel-Liste vorhanden sein, aber weder im gefilterten Haltungslayer, noch in den Dichtheitsprüfungen, so scheint sie auch nicht in der 
Tabelle auf. 

*Beispiel:* Im Filter werden alle Misch- und Schmutzwasserhaltungen im Gebiet 'West' gewählt. (Gebiet = 'West' and Kanalart in ('KM','KS'))
In der Excel-Liste, in der die Haltungsinspektion dokumentiert wurde, sind auch Regenwasserhaltungen enthalten. Diese scheinen sind in der angezeigten Liste nicht enthalten.

|haltung_filter|

.. |haltung_filter| image:: /figures/haltung_filter.png
	:scale: 75 %

Laden von verknüpften Daten
----------------------------
Wenn entweder Stammdaten oder eine Excel-Liste definiert wurden, können Daten mit dem Button |stammdaten_btn| geladen werden. Durch das laden werden weitere Prüfungen
im Dropdown *Datenprüfung* ermöglicht. 

|check_data|

.. |stammdaten_btn| image:: /figures/stammdaten_button.png
.. |check_data| image:: /figures/check_data.png
	:scale: 75 %

Öffnen einer .sew-Datei
------------------------
Der Button ".sew-Datei öffnen" steht zur Verfügung, sobald Dichtheitsprüfungen geladen wurden. Wenn eine Zeile in der Tabelle gewählt ist, kann die Datei geöffnet werden.
Dies erfolgt im Standard-Programm, welches für die Öffnung dieses Dateityps festgelegt wurde.

Exportieren von Grafiken
-------------------------
Durch klicken auf den Button "alle Prüfverläufe als Bild exportieren" können alle geladenen - und nicht ignorierten - Dichtheitsprüfungen exportiert werden.
Für jede Prüfung wird ein eigenes Bild im gewählten Ordner erzeugt. Sollte eine Datei bereits bestehen, so wird mit der Endung "_1" eine neue Erzeugt.

Für den Dateinamen können drei Variablen verwendet werden:
	- Bezeichnung
	- Ergebnis
	- Datum

Um die Variablen im Dateinamen verwenden zu können, müssen sie mit {} umschlossen sein.

Beispiel: {Bezeichnung}_{Ergebnis}_{Datum}

|export_plots|

.. |export_plots| image:: /figures/export_plots.png
	:scale: 75%

.. toctree::
   :maxdepth: 2
