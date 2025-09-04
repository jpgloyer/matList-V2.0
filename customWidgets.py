from PyQt5.QtWidgets import QWidget, QLineEdit, QCheckBox, QSpinBox, QGridLayout, QComboBox, QLabel
from PyQt5 import QtCore


#Custom Widgets for Main Table
class customTableWidgetItem(QWidget):
    def __init__(self,signalClass, tableWidget, count=0,deviceNames=[], coordinates=(), note = ''):
        super(customTableWidgetItem,self).__init__()
        self.signals=signalClass
        self.coordinates = coordinates
        self.note = note
        self.tableWidget = tableWidget
        self.deviceNames = [QLineEdit() for i in deviceNames]

        self.buildDeviceNames(deviceNames)
        self.buildLayout()
        self.buildCheckBoxes()
        self.buildCountSelect(count)    
        self.updateDeviceNameSlots()

    def buildDeviceNames(self, deviceNames):
        for i in range(len(deviceNames)):
            self.deviceNames[i].setText(deviceNames[i])
            self.deviceNames[i].editingFinished.connect(self.lineEditFinished)
    def buildLayout(self):
        self.oneLotCheckBox = QCheckBox("One Lot")
        self.showDeviceNamesCheckBox = QCheckBox("Show Device Names")
        self.showDeviceNamesCheckBox.hide()
        self.countSelect = QSpinBox()
        self.countSelect.setMaximumWidth(80)
        self.layout1 = QGridLayout()
        self.layout1.addWidget(self.countSelect,0,0)
        for i in range(len(self.deviceNames)):
            self.layout1.addWidget(self.deviceNames[i],i+2,0,1,3)
        self.layout1.addWidget(self.oneLotCheckBox, 0, 1)
        self.layout1.addWidget(self.showDeviceNamesCheckBox, 0, 2)
        self.setLayout(self.layout1)
    def buildCheckBoxes(self):
        self.oneLotCheckBox.clicked.connect(self.updateOneLot)
        self.showDeviceNamesCheckBox.clicked.connect(self.updateDeviceNameSlots)
        if len(self.deviceNames) > 0:
            self.showDeviceNamesCheckBox.setChecked(True)
    def buildCountSelect(self, count):
        self.countSelect.setMaximum(999)
        self.countSelect.valueChanged.connect(self.spinBoxChanged)
        self.countSelect.valueChanged.connect(self.updateDeviceNameSlots)
        if count == '1 Lot':
            self.oneLotCheckBox.setChecked(True)
            self.updateOneLot()
        else:
            self.countSelect.setValue(count)
    def updateDeviceNameSlots(self):
        if self.showDeviceNamesCheckBox.isChecked():
            while self.countSelect.value() != len(self.deviceNames):
                if self.countSelect.value() > len(self.deviceNames):
                    self.addDeviceNameSlot()
                if self.countSelect.value() < len(self.deviceNames):
                    self.removeDeviceNameSlot()    
        else:
            while len(self.deviceNames) > 0:
                self.removeDeviceNameSlot()
        QtCore.QTimer.singleShot(0, self.tableWidget.resizeRowsToContents)
        QtCore.QTimer.singleShot(0, self.tableWidget.resizeColumnsToContents)

    def updateOneLot(self):
        if self.oneLotCheckBox.isChecked():
            self.countSelect.setValue(0)
            self.countSelect.setDisabled(True)
            self.showDeviceNamesCheckBox.setChecked(False)
            self.showDeviceNamesCheckBox.setDisabled(True)
            self.updateDeviceNameSlots()
        else:
            self.countSelect.setDisabled(False)
            self.showDeviceNamesCheckBox.setDisabled(False)
    def addDeviceNameSlot(self):
        self.deviceNames.append(QLineEdit())
        self.layout1.addWidget(self.deviceNames[-1],len(self.deviceNames)+2,0,1,3)
        self.signals.saveCellData.emit()
    def removeDeviceNameSlot(self):
        self.layout1.removeWidget(self.deviceNames[-1])
        self.deviceNames.pop()
        self.signals.saveCellData.emit()

    def spinBoxChanged(self):
        if self.countSelect.value() == 0:
            self.showDeviceNamesCheckBox.setChecked(False)
            self.showDeviceNamesCheckBox.hide()
            self.oneLotCheckBox.setChecked(False)
            self.oneLotCheckBox.show()
        else:
            self.showDeviceNamesCheckBox.show()
            self.oneLotCheckBox.setChecked(False)
            self.oneLotCheckBox.hide()
        self.signals.saveCellData.emit()
    def lineEditFinished(self):
        self.signals.saveCellData.emit()

class customCableTableItem(QWidget):
    def __init__(self,signalClass, tableWidget, cable = {"relayType":"","deviceNo":"","port":"","panelNo":""},relayTypes = [],deviceNames = [], panelNos = []):
        super(customCableTableItem,self).__init__()
        self.signals=signalClass
        self.tableWidget = tableWidget
        self.cable = cable
        self.relayTypes = relayTypes
        self.panelNos = panelNos
        self.deviceNames = deviceNames
        self.declareVariables()
        self.buildLayout()
        self.fillOptions()
        
    def declareVariables(self):
        self.layout1 = QGridLayout()
        self.relayType = QComboBox()
        self.deviceName = QComboBox()
        self.port = QComboBox()
        self.panelNo = QComboBox()
        self.relayLabel = QLabel("Relay Type")
        self.deviceLabel = QLabel("Device No")
        self.portLabel = QLabel("Port")
        self.panelLabel = QLabel("Panel No")
    def buildLayout(self):
        self.relayType.setEditable(True)
        self.deviceName.setEditable(True)
        self.port.setEditable(True)
        
        self.layout1.addWidget(self.relayLabel, 3, 0)
        self.layout1.addWidget(self.deviceLabel, 1, 0)
        self.layout1.addWidget(self.portLabel, 2, 0)
        self.layout1.addWidget(self.panelLabel, 0, 0)
        self.layout1.addWidget(self.relayType, 3, 1)
        self.layout1.addWidget(self.deviceName, 1, 1)
        self.layout1.addWidget(self.port, 2, 1)
        self.layout1.addWidget(self.panelNo, 0, 1)
        self.setLayout(self.layout1)

        QtCore.QTimer.singleShot(0, self.tableWidget.resizeRowsToContents)
        QtCore.QTimer.singleShot(0, self.tableWidget.resizeColumnsToContents)
    def fillOptions(self):
        for i in range(100):
            self.port.addItem(str(i))
        for relayType in self.relayTypes:
            self.relayType.addItem(relayType)
        for deviceName in self.deviceNames:
            self.deviceName.addItem(deviceName)
        for panel in self.panelNos:
            self.panelNo.addItem(panel)
        self.relayType.setCurrentText(self.cable["relayType"])
        self.deviceName.setCurrentText(self.cable["deviceNo"])
        self.port.setCurrentText(self.cable["port"])
        self.panelNo.setCurrentText(self.cable["panelNo"])
        

        

