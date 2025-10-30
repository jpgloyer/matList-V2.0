from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *


class deleteItem(QDialog):
    def __init__(self, itemNos = [], panelNos = []):
        super(deleteItem, self).__init__()
        self.itemNos = itemNos
        self.panelNos = panelNos
        self.windowLayout = QFormLayout()
        self.deleteDialogPanelRadioButton = QRadioButton(text="Panel")
        self.deleteDialogItemRadioButton = QRadioButton(text="Item")
        self.deleteDialogItemSelect = QComboBox()
        self.deleteConfirmButton = QPushButton(text="Delete",clicked=self.confirmDelete)
        self.deletedItem = ["",""]
        self.deleteDialogPanelRadioButton.clicked.connect(self.updateDeleteOptions)
        self.deleteDialogItemRadioButton.clicked.connect(self.updateDeleteOptions)
        self.windowLayout.addWidget(self.deleteDialogItemRadioButton)
        self.windowLayout.addWidget(self.deleteDialogPanelRadioButton)
        self.windowLayout.addWidget(self.deleteDialogItemSelect)
        self.windowLayout.addWidget(self.deleteConfirmButton)
        self.setLayout(self.windowLayout)

    def updateDeleteOptions(self):
        if self.deleteDialogItemRadioButton.isChecked():
            self.deleteDialogItemSelect.clear()
            self.deleteDialogItemSelect.addItems(self.itemNos)
        elif self.deleteDialogPanelRadioButton.isChecked():
            self.deleteDialogItemSelect.clear()
            self.deleteDialogItemSelect.addItems(self.panelNos)

    def confirmDelete(self):
        self.deletedItem = ["Item" if self.deleteDialogItemRadioButton.isChecked() else "Panel",self.deleteDialogItemSelect.currentText()]
        self.accept()