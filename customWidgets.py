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
        
    def buildDeviceNames(self, deviceNames):
        for i in range(len(deviceNames)):
            self.deviceNames[i].setText(deviceNames[i])
            self.deviceNames[i].editingFinished.connect(self.lineEditFinished)

    def buildLayout(self):
        self.oneLotCheckBox = QCheckBox("One Lot")
        self.showDeviceNamesCheckBox = QCheckBox("Show Device Names")
        self.countSelect = QSpinBox()
        self.layout1 = QGridLayout()
        self.layout1.addWidget(self.countSelect,0,0)
        for i in range(len(self.deviceNames)):
            self.layout1.addWidget(self.deviceNames[i],i+2,0,1,2)
        self.layout1.addWidget(self.oneLotCheckBox, 0, 1)
        self.layout1.addWidget(self.showDeviceNamesCheckBox, 1, 1)
        self.setLayout(self.layout1)
        
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

    def addDeviceNameSlot(self):
        self.deviceNames.append(QLineEdit())
        self.layout1.addWidget(self.deviceNames[-1],len(self.deviceNames)+2,0,1,2)
        self.signals.needsSaved.emit(True)

    def removeDeviceNameSlot(self):
        self.layout1.removeWidget(self.deviceNames[-1])
        self.deviceNames.pop()
        self.signals.needsSaved.emit(True)

    def spinBoxChanged(self):
        self.signals.needsSaved.emit(True)

    def lineEditFinished(self):
        self.signals.needsSaved.emit(True)

class customCableTableItem(QWidget):
    def __init__(self,signalClass, tableWidget, cable = {"relayType":"","deviceNo":"","port":"","panelNo":""}):
        super(customCableTableItem,self).__init__()
        self.signals=signalClass
        self.tableWidget = tableWidget
        self.cable = cable

        self.buildLayout()
   

    def buildLayout(self):
        self.layout1 = QGridLayout()
        self.relayType = QComboBox()
        self.relayType.addItem(self.cable["relayType"])
        self.relayType.setCurrentIndex(0)
        self.deviceName = QComboBox()
        self.deviceName.addItem(self.cable["deviceNo"])
        self.deviceName.setCurrentIndex(0)
        self.port = QComboBox()
        self.port.addItem(self.cable["port"])
        self.port.setCurrentIndex(0)
        self.panelNo = QComboBox()
        self.panelNo.addItem(self.cable["panelNo"])
        self.panelNo.setCurrentIndex(0)
        self.relayLabel = QLabel("Relay Type")
        self.deviceLabel = QLabel("Device No")
        self.portLabel = QLabel("Port")
        self.panelLabel = QLabel("Panel No")
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

    def fillOptions(self, relayTypes, deviceNames, panelNos):
        self.relayType.clear()
        self.deviceName.clear()
        self.port.clear()
        self.panelNo.clear()
        for relayType in relayTypes:
            self.relayType.addItem(relayType)
        for deviceName in deviceNames:
            self.deviceName.addItem(deviceName)
        for panel in panelNos:
            self.panelNo.addItem(panel)