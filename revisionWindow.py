from screeninfo import get_monitors
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import sys
from signals import signalClass


class revisionWindow(QDialog):
    def __init__(self, signals, revisionData: dict = {"date":[],"user":[],"description":[]}):
        super(revisionWindow,self).__init__()
        self.declareVariables()
        self.signals = signals
        self.revisionData = revisionData
        self.buildWindow()        
        self.buildUI()

    def declareVariables(self):
        self.signals: signalClass
        self.revisionData:dict = {}

        self.revisionTable = QTableWidget()

        self.addRevisionButton = QPushButton('Add Revision',clicked=self.addRevision)
        self.removeRevisionButton = QPushButton('Remove Currently Selected Revision',clicked=self.removeRevision)
        self.printOutput = QPushButton()

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
        self.revisionTable.setColumnCount(len(self.revisionData))
        self.revisionTable.setHorizontalHeaderLabels(self.revisionData.keys())
        self.revisionTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.revisionTable.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.revisionTable.verticalScrollBar().setSingleStep(20)
        self.revisionTable.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.revisionTable.horizontalScrollBar().setSingleStep(20)

        self.centralLayout.addWidget(self.revisionTable, 0,1,99,1)
        self.centralLayout.addWidget(self.addRevisionButton,0,0)
        self.centralLayout.addWidget(self.removeRevisionButton,1,0)

        for rowIndex, row in enumerate(self.revisionData['date']):
            self.revisionTable.insertRow(self.revisionTable.rowCount())
            for columnIndex, column in enumerate(self.revisionData.keys()):
                item = QTableWidgetItem()
                item.setText(self.revisionData[column][rowIndex])
                self.revisionTable.setItem(self.revisionTable.rowCount()-1,columnIndex,item)

        self.setLayout(self.centralLayout)

    def addRevision(self):
        self.revisionTable.insertRow(self.revisionTable.rowCount())
        for columnIndex, column in enumerate(self.revisionData.keys()):
            item = QTableWidgetItem()
            self.revisionTable.setItem(self.revisionTable.rowCount()-1,columnIndex,item)
    def removeRevision(self):
        self.revisionTable.removeRow(self.revisionTable.currentRow())

    def closeEvent(self,event):
        self.developOutputDictionary()
    def developOutputDictionary(self):
        for key in self.revisionData.keys():
            self.revisionData[key] = []
        for rowIndex in range(self.revisionTable.rowCount()):
            for columnIndex, column in enumerate(self.revisionData.keys()):
                self.revisionData[column].append(self.revisionTable.item(rowIndex, columnIndex).text())

