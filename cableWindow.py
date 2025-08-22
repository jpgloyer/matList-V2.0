from screeninfo import get_monitors
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import sys
from matlistMainWindow import signalClass
from customWidgets import customCableTableItem


class cableWindow(QMainWindow):
    def __init__(self, signals, cableData = []):
        super(cableWindow,self).__init__()
        self.signals = signals
        self.cableData = cableData

        self.buildWindow()
        self.initializeCableTable()
        self.buildDock()


        self.printOutput = QPushButton()

    def buildDock(self):
        self.dockMenu = QDockWidget()
        self.dockMenuWidget = QWidget()

        self.dockMenuLayout = QFormLayout()
        self.dockMenuButtonAddCable = QPushButton()
        self.dockMenuButtonRemoveCable = QPushButton()
        self.dockMenuButtonAddCable.setText('Add Cable')
        self.dockMenuButtonAddCable.clicked.connect(self.addCable)
        self.dockMenuButtonRemoveCable.setText('Remove Currently Selected Cable')
        self.dockMenuButtonRemoveCable.clicked.connect(self.removeCable)
        self.dockMenuLayout.addRow(self.dockMenuButtonAddCable)
        self.dockMenuLayout.addRow(self.dockMenuButtonRemoveCable)
        self.dockMenuWidget.setLayout(self.dockMenuLayout)

        self.dockMenu.setWidget(self.dockMenuWidget)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dockMenu)

    def buildWindow(self):
        self.monitor = get_monitors()
        self.monitorXSize = int(self.monitor[0].width)
        self.monitorYSize = int(self.monitor[0].height)
        self.xShift = int(self.monitorXSize*.1)
        self.yShift = int(self.monitorYSize*.1)
        self.xSize = int(self.monitorXSize*.8)
        self.ySize = int(self.monitorYSize*.8)
        self.setGeometry(QtCore.QRect(self.xShift,self.yShift,self.xSize,self.ySize))

    def initializeCableTable(self):
        self.cableTable = QTableWidget()
        self.cableTable.setColumnCount(5)
        self.cableTable.setHorizontalHeaderLabels(["Item No", "Cable Type", "Length", "From", "To"])
        self.cableTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setCentralWidget(self.cableTable)

        
        for rowIndex in range(len(self.cableData)):
            if self.cableTable.rowCount() < rowIndex:
                self.cableTable.insertRow(self.cableTable.rowCount())

            self.addCable(self.cableData[rowIndex])

    def addCable(self, cable = False):
        if cable == False:
            cable = {"itemNo":"","cableType":"","length":"0","from":{"relayType":"","deviceNo":"","port":"","panelNo":""},"to":{"relayType":"","deviceNo":"","port":"","panelNo":""}}
        self.cableTable.insertRow(self.cableTable.rowCount())
        rowIndex = self.cableTable.rowCount()-1
        item = QTableWidgetItem()
        item.setText(cable["itemNo"])
        self.cableTable.setItem(rowIndex, 0,item)

        item = QComboBox()
        item.addItem(cable["cableType"])
        item.setCurrentIndex(0)
        #item.addothercableoptions
        self.cableTable.setCellWidget(rowIndex, 1, item)

        item = QSpinBox()
        item.setValue(0)
        item.setRange(0,1000)
        item.setValue(int(cable["length"]))
        self.cableTable.setCellWidget(rowIndex, 2, item)

        item = customCableTableItem(self.signals,self.cableTable, cable["from"])
        self.cableTable.setCellWidget(rowIndex, 3, item)

        item = customCableTableItem(self.signals,self.cableTable, cable["to"])
        self.cableTable.setCellWidget(rowIndex, 4, item)

        pass

    def removeCable(self):
        self.cableTable.removeRow(self.cableTable.currentRow())

    def closeEvent(self,event):
        pass
        #self.developOutputDictionary()
        #self.signals.saveCableData.emit()

    def developOutputDictionary(self):
        for key in self.cableData.keys():
            self.cableData[key] = []
        for rowIndex in range(self.cableTable.rowCount()):
            for columnIndex, column in enumerate(self.cableData.keys()):
                self.cableData[column].append(self.cableTable.item(rowIndex, columnIndex).text())



if  __name__ == "__main__":
    app = QApplication(sys.argv)
    signals = signalClass()
    application = cableWindow(signals,[{"itemNo":"","cableType":"C489","length":10,"from":{"relayType":"311C","deviceNo":"21P","port":"2","panelNo":"1"},"to":{"relayType":"","deviceNo":"","port":"","panelNo":""}}])
    #application = cableWindow(signals,[])
    
    application.show()
    sys.exit(app.exec())