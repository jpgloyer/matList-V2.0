from screeninfo import get_monitors
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import sys
#from matlistMainWindow import signalClass
from customWidgets import customCableTableItem
from signals import signalClass

import re
import pyodbc
import pandas as pd

def naturalSortKey(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(re.compile('([0-9]+)'), s)]

class cableWindow(QMainWindow):
    def __init__(self, signals, cableData = [], routingOptions = {"relayTypes":[], "deviceNames":[], "panelNos":[]}, cableOptions = [{"itemNo":"","cableType":"","length":""}]):
        super(cableWindow,self).__init__()
        self.monitor = get_monitors()
        
        self.signals: signalClass = signals

        self.cableData: list = cableData

        self.relayTypes: list = [""]+routingOptions["relayTypes"]
        self.deviceNames: list = [""]+routingOptions["deviceNames"]
        self.panelNos: list = [""]+routingOptions["panelNos"]

        self.cableOptions: list = cableOptions
        self.itemNos: list = list(dict.fromkeys([""]+[cable["itemNo"] for cable in cableOptions]))
        self.cableTypes: list = list(dict.fromkeys([""]+[cable["cableType"] for cable in cableOptions]))
        self.cableLengths: list = list(dict.fromkeys([""]+[cable["length"] for cable in cableOptions]))
        self.itemNos.sort(key=naturalSortKey)
        self.cableTypes.sort(key=naturalSortKey)
        self.cableLengths.sort(key=naturalSortKey)

        self.dockMenu = QDockWidget()
        self.dockMenuWidget = QWidget()
        self.dockMenuLayout = QFormLayout()
        self.dockMenuButtonAddCable = QPushButton("Add Cable",clicked=self.addCable)
        self.dockMenuButtonRemoveCable = QPushButton("Remove Currently Selected Cable",clicked=self.removeCable)
        self.cableTable = QTableWidget()

        self.buildWindow()
        self.initializeCableTable()
        self.buildDock()

    def buildWindow(self):
        monitorXSize = int(self.monitor[0].width)
        monitorYSize = int(self.monitor[0].height)
        xShift = int(monitorXSize*.1)
        yShift = int(monitorYSize*.1)
        xSize = int(monitorXSize*.8)
        ySize = int(monitorYSize*.8)
        self.setGeometry(QtCore.QRect(xShift,yShift,xSize,ySize))
    def initializeCableTable(self):
        self.cableTable.setColumnCount(5)
        self.cableTable.setHorizontalHeaderLabels(["Item No", "Cable Type", "Length", "From", "To"])
        self.cableTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.cableTable.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.cableTable.verticalScrollBar().setSingleStep(20)
        self.setCentralWidget(self.cableTable)

        for rowIndex in range(len(self.cableData)):
            if self.cableTable.rowCount() < rowIndex:
                self.cableTable.insertRow(self.cableTable.rowCount())
            self.addCable(self.cableData[rowIndex])
    def buildDock(self):
        self.dockMenuLayout.addRow(self.dockMenuButtonAddCable)
        self.dockMenuLayout.addRow(self.dockMenuButtonRemoveCable)
        self.dockMenuWidget.setLayout(self.dockMenuLayout)
        self.dockMenu.setWidget(self.dockMenuWidget)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dockMenu)

    def addItemNoBox(self, itemNo, rowIndex):
        item = QLabel()
        item.setText(itemNo)
        self.cableTable.setCellWidget(rowIndex, 0, item)


    def addCableTypeBox(self, cableType, rowIndex):
        item = QComboBox()
        for cableType1 in self.cableTypes:
            item.addItem(cableType1)
        self.cableTable.setCellWidget(rowIndex, 1, item)
        self.cableTable.cellWidget(rowIndex,1).setCurrentText(cableType)
        self.cableTable.cellWidget(rowIndex,1).currentTextChanged.connect(self.cableTypeChanged)


    def addCableLengthBox(self, cableLength, rowIndex):
        item = QComboBox()
        choices = []
        item.addItem("")
        for cable in self.cableOptions:
            if cable["cableType"] == self.cableTable.cellWidget(rowIndex,1).currentText():
                if item.findText(cable["length"]) == -1:
                    choices.append(cable["length"])
        choices.sort(key=naturalSortKey)
        for choice in choices:
                    item.addItem(choice)

        self.cableTable.setCellWidget(rowIndex, 2, item)
        self.cableTable.cellWidget(rowIndex,2).setCurrentText(cableLength)
        self.cableTable.cellWidget(rowIndex,2).currentTextChanged.connect(self.cableLengthChanged)

    def addCableRoutingBox(self, cableFrom, rowIndex, columnIndex):
        item = customCableTableItem(self.signals,self.cableTable, cableFrom)
        item.fillOptions(self.relayTypes, self.deviceNames, self.panelNos)
        item.setCurrentValues()
        self.cableTable.setCellWidget(rowIndex, columnIndex, item)

    def addCable(self, cable = False):
        if cable == False:
            cable = {"itemNo":"","cableType":"","length":"","from":{"relayType":"","deviceNo":"","port":"","panelNo":""},"to":{"relayType":"","deviceNo":"","port":"","panelNo":""}}
        self.cableTable.insertRow(self.cableTable.rowCount())
        rowIndex = self.cableTable.rowCount()-1
        self.addItemNoBox(cable["itemNo"],rowIndex)
        self.addCableTypeBox(cable["cableType"],rowIndex)
        self.addCableLengthBox(cable["length"],rowIndex)
        self.addCableRoutingBox(cable["from"], rowIndex, 3)
        self.addCableRoutingBox(cable["to"], rowIndex , 4)

    def removeCable(self):
        self.cableTable.removeRow(self.cableTable.currentRow())
    def closeEvent(self,event):
        self.developOutputDictionary()
        self.signals.saveCableData.emit()
    def developOutputDictionary(self):
        self.cableData = []
        for rowIndex in range(self.cableTable.rowCount()):
            cable = {}
            cable["itemNo"] = self.cableTable.cellWidget(rowIndex,0).text()
            cable["cableType"] = self.cableTable.cellWidget(rowIndex,1).currentText()
            cable["length"] = self.cableTable.cellWidget(rowIndex,2).currentText()
            cable["from"] = {}
            cable["from"]["relayType"] = self.cableTable.cellWidget(rowIndex,3).relayType.currentText()
            cable["from"]["deviceNo"] = self.cableTable.cellWidget(rowIndex,3).deviceName.currentText()
            cable["from"]["port"] = self.cableTable.cellWidget(rowIndex,3).port.currentText()
            cable["from"]["panelNo"] = self.cableTable.cellWidget(rowIndex,3).panelNo.currentText()
            cable["to"] = {}
            cable["to"]["relayType"] = self.cableTable.cellWidget(rowIndex,4).relayType.currentText()
            cable["to"]["deviceNo"] = self.cableTable.cellWidget(rowIndex,4).deviceName.currentText()
            cable["to"]["port"] = self.cableTable.cellWidget(rowIndex,4).port.currentText()
            cable["to"]["panelNo"] = self.cableTable.cellWidget(rowIndex,4).panelNo.currentText()
            self.cableData.append(cable)
    
    def getItemNoFromDesc(self,cabletype,cableLength):
        for cable in self.cableOptions:
            if cabletype == cable["cableType"] and cableLength == cable["length"]:
                return cable["itemNo"]
        return None

    def getDescFromItemNo(self,itemNo):
        for cable in self.cableOptions:
            if itemNo == cable["itemNo"]:
                return cable["cableType"], cable["length"]
        return None, None

    def cableTypeChanged(self):
        self.cableTable.cellWidget(self.cableTable.currentRow(),0).setText("")#SET ITEM NO TO BLANK
        self.cableTable.cellWidget(self.cableTable.currentRow(),2).setCurrentText("")#SET LENGTH TO BLANK
        self.cableTable.cellWidget(self.cableTable.currentRow(),2).clear()#CLEAR LENGTH OPTIONS
        #FILL LENGTH OPTIONS
        self.cableTable.cellWidget(self.cableTable.currentRow(),2).addItem("")
        choices = []
        for cable in self.cableOptions:
            if cable["cableType"] == self.sender().currentText():
                if self.cableTable.cellWidget(self.cableTable.currentRow(),2).findText(cable["length"]) == -1:
                    choices.append(cable["length"])
        choices.sort(key=naturalSortKey)
        for choice in choices:
            self.cableTable.cellWidget(self.cableTable.currentRow(),2).addItem(choice)

    def cableLengthChanged(self):
        self.cableTable.cellWidget(self.cableTable.currentRow(),0).setText(self.getItemNoFromDesc(self.cableTable.cellWidget(self.cableTable.currentRow(),1).currentText(), self.sender().currentText()))
