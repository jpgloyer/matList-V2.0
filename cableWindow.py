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

class cableWindow(QDialog):
    def __init__(self, signals, cableData = [], routingOptions = {"relayTypes":[], "deviceNames":[], "panelNos":[]}, cableOptions = [{"itemNo":"","cableType":"","length":""}]):
        super(cableWindow,self).__init__()
        self.declareVariables()
        
        self.signals = signals
        self.cableData = cableData
        
        self.cableOptions = cableOptions
        self.cableTypes.extend(list(dict.fromkeys([cable["cableType"] for cable in cableOptions])))
        self.cableLengths.extend(list(dict.fromkeys([cable["length"] for cable in cableOptions])))
        self.cableTypes.sort(key=naturalSortKey)
        self.cableLengths.sort(key=naturalSortKey)

        self.relayTypes.extend(routingOptions["relayTypes"])
        self.deviceNames.extend(routingOptions["deviceNames"])
        self.panelNos.extend(routingOptions["panelNos"])

        self.buildWindow()
        self.buildUI()
        

    def declareVariables(self):
        self.signals: signalClass

        self.cableData: list = []
        self.relayTypes: list = [""]
        self.deviceNames: list = [""]
        self.panelNos: list = [""]
        self.cableOptions: list = []
        self.cableTypes: list = [""]
        self.cableLengths: list = [""]

        self.addCableButton = QPushButton("Add Cable",clicked=self.addCable)
        self.removeCableButton = QPushButton("Remove Currently Selected Cable",clicked=self.removeCable)
        
        self.cableTable = QTableWidget()

        self.centralLayout = QGridLayout()

    def buildWindow(self):
        monitor = get_monitors()
        monitorXSize = int(monitor[0].width)
        monitorYSize = int(monitor[0].height)
        xShift = int(monitorXSize*.1)
        yShift = int(monitorYSize*.1)
        xSize = int(monitorXSize*.8)
        ySize = int(monitorYSize*.8)
        self.setGeometry(QtCore.QRect(xShift,yShift,xSize,ySize))
    def buildUI(self):
        self.cableTable.setColumnCount(5)
        self.cableTable.setHorizontalHeaderLabels(["Item No", "Cable Type", "Length", "From", "To"])
        self.cableTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.cableTable.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.cableTable.verticalScrollBar().setSingleStep(20)
        self.cableTable.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.cableTable.horizontalScrollBar().setSingleStep(20)
        
        self.centralLayout.addWidget(self.cableTable,0,1,99,1)
        self.centralLayout.addWidget(self.addCableButton,0,0)
        self.centralLayout.addWidget(self.removeCableButton,1,0)

        for rowIndex in range(len(self.cableData)):
            if self.cableTable.rowCount() < rowIndex:
                self.cableTable.insertRow(self.cableTable.rowCount())
            self.addCable(self.cableData[rowIndex])

        self.setLayout(self.centralLayout)
    
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
    def addCableRoutingBox(self, cableRoute, rowIndex, columnIndex):
        item = customCableTableItem(self.signals,self.cableTable, cableRoute)
        item.fillOptions(self.relayTypes, self.deviceNames, self.panelNos)
        item.setCurrentValues()
        self.cableTable.setCellWidget(rowIndex, columnIndex, item)

    def removeCable(self):
        self.cableTable.removeRow(self.cableTable.currentRow())
        #self.requestSave()
    
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
        #self.requestSave()
    def cableLengthChanged(self):
        self.cableTable.cellWidget(self.cableTable.currentRow(),0).setText(self.getItemNoFromDesc(self.cableTable.cellWidget(self.cableTable.currentRow(),1).currentText(), self.sender().currentText()))
        #self.requestSave()
    def getItemNoFromDesc(self,cabletype,cableLength):
        for cable in self.cableOptions:
            if cabletype == cable["cableType"] and cableLength == cable["length"]:
                return cable["itemNo"]
        return None
    
    def closeEvent(self,event):
        self.developOutputDictionary()
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
