from screeninfo import get_monitors
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import sys


class revisionWindow(QMainWindow):
    def __init__(self, signals, revisionData: dict = {"date":[],"user":[],"description":[]}):
        super(revisionWindow,self).__init__()
        self.signals = signals
        self.revisionData = revisionData

        self.monitor = get_monitors()
        self.monitorXSize = int(self.monitor[0].width)
        self.monitorYSize = int(self.monitor[0].height)
        self.xShift = int(self.monitorXSize*.1)
        self.yShift = int(self.monitorYSize*.1)
        self.xSize = int(self.monitorXSize*.8)
        self.ySize = int(self.monitorYSize*.8)
        self.setGeometry(QtCore.QRect(self.xShift,self.yShift,self.xSize,self.ySize))

        self.revisionTable = QTableWidget()
        self.dockMenuButtonAddRevision = QPushButton()
        self.dockMenuButtonRemoveRevision = QPushButton()
        self.printOutput = QPushButton()
        self.dockMenuLayout = QFormLayout()
        self.dockMenuWidget = QWidget()
        self.dockMenu = QDockWidget()


        self.dockMenuButtonAddRevision.setText('Add Revision')
        self.dockMenuButtonAddRevision.clicked.connect(self.addRevision)
        self.dockMenuButtonRemoveRevision.setText('Remove Currently Selected Revision')
        self.dockMenuButtonRemoveRevision.clicked.connect(self.removeRevision)
        self.dockMenuLayout.addRow(self.dockMenuButtonAddRevision)
        self.dockMenuLayout.addRow(self.dockMenuButtonRemoveRevision)
        #self.dockMenuLayout.addRow(self.printOutput)
        self.revisionTable.setColumnCount(len(self.revisionData))

        self.revisionTable.setHorizontalHeaderLabels(self.revisionData.keys())
        self.revisionTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)


        self.dockMenuWidget.setLayout(self.dockMenuLayout)
        self.dockMenu.setWidget(self.dockMenuWidget)
        self.setCentralWidget(self.revisionTable)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dockMenu)
        self.fillTable()

    def fillTable(self):
        for rowIndex, row in enumerate(self.revisionData['date']):
            self.revisionTable.insertRow(self.revisionTable.rowCount())
            for columnIndex, column in enumerate(self.revisionData.keys()):
                item = QTableWidgetItem()
                item.setText(self.revisionData[column][rowIndex])
                self.revisionTable.setItem(self.revisionTable.rowCount()-1,columnIndex,item)

    def addRevision(self):
        self.revisionTable.insertRow(self.revisionTable.rowCount())
        for columnIndex, column in enumerate(self.revisionData.keys()):
            item = QTableWidgetItem()
            self.revisionTable.setItem(self.revisionTable.rowCount()-1,columnIndex,item)

    def removeRevision(self):
        self.revisionTable.removeRow(self.revisionTable.currentRow())

    def closeEvent(self,event):
        self.developOutputDictionary()
        self.signals.saveRevisionData.emit()

    def developOutputDictionary(self):
        for key in self.revisionData.keys():
            self.revisionData[key] = []
        for rowIndex in range(self.revisionTable.rowCount()):
            for columnIndex, column in enumerate(self.revisionData.keys()):
                self.revisionData[column].append(self.revisionTable.item(rowIndex, columnIndex).text())

class signalClass(QWidget):
    needsSaved = QtCore.pyqtSignal(bool)
    saveRevisionData = QtCore.pyqtSignal()


if  __name__ == "__main__":
    app = QApplication(sys.argv)
    signals = signalClass()
    application = revisionWindow(signals)
    application.show()
    sys.exit(app.exec())