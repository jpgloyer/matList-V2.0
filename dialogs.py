from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
import re


def naturalSortKey(s):
    """Sort strings naturally so that 200j comes after 21"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(re.compile('([0-9]+)'), s)]


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


class addItemDialog(QDialog):
    def __init__(self, masterMatList=None, existingItems=None):
        super(addItemDialog, self).__init__()
        self.masterMatList = masterMatList or {}
        self.existingItems = existingItems or []
        self.selectedItems = []
        self.useAndLogic = True  # Default to AND logic
        self.keywordEdits = []
        
        self.setWindowTitle("Add Items to Material List")
        self.setMinimumSize(1200, 700)
        self.resize(1200, 700)
        
        mainLayout = QVBoxLayout()
        
        # Title and instructions
        titleLabel = QLabel("Select items to add (only items not already in the list are shown):")
        mainLayout.addWidget(titleLabel)
        
        # Search section
        searchSectionLayout = QVBoxLayout()
        searchSectionLabel = QLabel("Search Descriptions:")
        searchSectionLayout.addWidget(searchSectionLabel)
        
        # Keywords input area
        keywordsLayout = QVBoxLayout()
        self.keywordsContainer = QWidget()
        self.keywordsContainerLayout = QVBoxLayout()
        self.keywordsContainer.setLayout(self.keywordsContainerLayout)
        
        # Add first keyword field
        self.addKeywordField()
        
        keywordsLayout.addWidget(self.keywordsContainer)
        searchSectionLayout.addLayout(keywordsLayout)
        
        # Logic buttons row
        logicLayout = QHBoxLayout()
        logicLayout.addSpacing(20)
        
        andButton = QPushButton("AND", clicked=lambda: self.setLogicMode(True))
        andButton.setMaximumWidth(60)
        andButton.setCheckable(True)
        andButton.setChecked(True)
        self.andButton = andButton
        
        orButton = QPushButton("OR", clicked=lambda: self.setLogicMode(False))
        orButton.setMaximumWidth(60)
        orButton.setCheckable(True)
        self.orButton = orButton
        
        logicLayout.addWidget(QLabel("Logic:"))
        logicLayout.addWidget(andButton)
        logicLayout.addWidget(orButton)
        logicLayout.addStretch()
        
        searchSectionLayout.addLayout(logicLayout)
        mainLayout.addLayout(searchSectionLayout)
        
        # Table widget for items with resizable rows
        self.itemTableWidget = QTableWidget()
        self.itemTableWidget.setColumnCount(2)
        self.itemTableWidget.setHorizontalHeaderLabels(["Item", "Description"])
        self.itemTableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.itemTableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.itemTableWidget.verticalHeader().setVisible(True)
        self.itemTableWidget.setSelectionMode(QAbstractItemView.NoSelection)
        self.itemTableWidget.setColumnWidth(0, 200)
        self.itemTableWidget.setWordWrap(True)
        self.itemTableWidget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.itemTableWidget.verticalScrollBar().setSingleStep(15)
        
        self.checkBoxes = {}
        self.itemRows = {}  # Store row index for each item
        
        # Populate with available items (not already in table), sorted naturally
        availableItems = sorted([item for item in self.masterMatList.keys() if item not in self.existingItems], key=naturalSortKey)
        self.itemTableWidget.setRowCount(len(availableItems))
        
        for rowIndex, item in enumerate(availableItems):
            # Add checkbox in first column
            checkbox = QCheckBox(item)
            checkbox.setMinimumWidth(180)
            self.itemTableWidget.setCellWidget(rowIndex, 0, checkbox)
            
            # Add description in second column
            itemDescription = QTableWidgetItem(self.masterMatList[item].replace('<br/>', '\n'))
            itemDescription.setFlags(itemDescription.flags() & ~QtCore.Qt.ItemIsEditable)
            self.itemTableWidget.setItem(rowIndex, 1, itemDescription)
            
            self.checkBoxes[item] = checkbox
            self.itemRows[item] = rowIndex
        
        # Resize rows to fit content
        self.itemTableWidget.resizeRowsToContents()
        
        mainLayout.addWidget(self.itemTableWidget)
        
        # Confirmation buttons
        confirmLayout = QHBoxLayout()
        addButton = QPushButton("Add Selected Items", clicked=self.confirmAdd)
        cancelButton = QPushButton("Cancel", clicked=self.reject)
        confirmLayout.addStretch()
        confirmLayout.addWidget(addButton)
        confirmLayout.addWidget(cancelButton)
        mainLayout.addLayout(confirmLayout)
        
        self.setLayout(mainLayout)
    
    def addKeywordField(self):
        """Add a new keyword search field"""
        fieldLayout = QHBoxLayout()
        keywordEdit = QLineEdit()
        keywordEdit.setPlaceholderText(f"Keyword {len(self.keywordEdits) + 1}...")
        keywordEdit.textChanged.connect(self.filterItems)
        
        # Hide + button on all existing fields and show on new one
        for i in range(self.keywordsContainerLayout.count()):
            item = self.keywordsContainerLayout.itemAt(i)
            if item and isinstance(item, QHBoxLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if isinstance(widget, QPushButton) and widget.text() == "+":
                        widget.setVisible(False)
        
        addButton = QPushButton("+", clicked=self.addKeywordField)
        addButton.setMaximumWidth(40)
        
        fieldLayout.addWidget(keywordEdit)
        fieldLayout.addWidget(addButton)
        
        self.keywordEdits.append(keywordEdit)
        self.keywordsContainerLayout.addLayout(fieldLayout)
    
    def setLogicMode(self, andMode):
        """Toggle between AND and OR logic"""
        self.useAndLogic = andMode
        self.andButton.setChecked(andMode)
        self.orButton.setChecked(not andMode)
        self.filterItems()
    
    def filterItems(self):
        """Filter items based on keywords and logic mode"""
        # Get all non-empty keywords
        keywords = [edit.text().lower().strip() for edit in self.keywordEdits if edit.text().strip()]
        
        if not keywords:
            # Show all items if no keywords
            for rowIndex in self.itemRows.values():
                self.itemTableWidget.showRow(rowIndex)
            return
        
        # Filter items
        for item, rowIndex in self.itemRows.items():
            description = self.masterMatList[item].lower()
            
            if self.useAndLogic:
                # AND logic: all keywords must be in description
                match = all(keyword in description for keyword in keywords)
            else:
                # OR logic: at least one keyword must be in description
                match = any(keyword in description for keyword in keywords)
            
            if match:
                self.itemTableWidget.showRow(rowIndex)
            else:
                self.itemTableWidget.hideRow(rowIndex)
    
    def confirmAdd(self):
        """Collect selected items and close dialog"""
        self.selectedItems = [item for item, checkbox in self.checkBoxes.items() if checkbox.isChecked()]
        if self.selectedItems:
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select at least one item to add.")


class addPanelDialog(QDialog):
    def __init__(self, existingPanelNames=None):
        super(addPanelDialog, self).__init__()
        self.existingPanelNames = existingPanelNames or []
        self.panelName = ""
        self.panelDescription = ""
        
        self.setWindowTitle("Add New Panel")
        self.setMinimumSize(400, 150)
        
        mainLayout = QVBoxLayout()
        
        # Panel name input
        nameLayout = QHBoxLayout()
        nameLabel = QLabel("Panel Name:")
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Enter panel name...")
        nameLayout.addWidget(nameLabel)
        nameLayout.addWidget(self.nameEdit)
        mainLayout.addLayout(nameLayout)
        
        # Panel description input
        descLayout = QHBoxLayout()
        descLabel = QLabel("Description:")
        self.descEdit = QLineEdit()
        self.descEdit.setPlaceholderText("Enter panel description (optional)...")
        descLayout.addWidget(descLabel)
        descLayout.addWidget(self.descEdit)
        mainLayout.addLayout(descLayout)
        
        # Buttons
        buttonLayout = QHBoxLayout()
        addButton = QPushButton("Add Panel", clicked=self.confirmAdd)
        cancelButton = QPushButton("Cancel", clicked=self.reject)
        buttonLayout.addStretch()
        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(cancelButton)
        mainLayout.addLayout(buttonLayout)
        
        mainLayout.addStretch()
        self.setLayout(mainLayout)
    
    def confirmAdd(self):
        """Validate and accept panel creation"""
        self.panelName = self.nameEdit.text().strip()
        
        if not self.panelName:
            QMessageBox.warning(self, "Invalid Input", "Please enter a panel name.")
            return
        
        if self.panelName in self.existingPanelNames:
            QMessageBox.warning(self, "Duplicate Name", f"Panel '{self.panelName}' already exists.")
            return
        
        self.panelDescription = self.descEdit.text().strip()
        self.accept()

class renamePanelDialog(QDialog):
    def __init__(self, currentPanelName="", currentPanelDescription="", existingPanelNames=None):
        super(renamePanelDialog, self).__init__()
        self.currentPanelName = currentPanelName
        self.existingPanelNames = [name for name in (existingPanelNames or []) if name != currentPanelName]
        self.panelName = ""
        self.panelDescription = ""
        
        self.setWindowTitle("Rename Panel")
        self.setMinimumSize(400, 150)
        
        mainLayout = QVBoxLayout()
        
        # Panel name input
        nameLayout = QHBoxLayout()
        nameLabel = QLabel("Panel Name:")
        self.nameEdit = QLineEdit()
        self.nameEdit.setText(currentPanelName)
        self.nameEdit.selectAll()
        nameLayout.addWidget(nameLabel)
        nameLayout.addWidget(self.nameEdit)
        mainLayout.addLayout(nameLayout)
        
        # Panel description input
        descLayout = QHBoxLayout()
        descLabel = QLabel("Description:")
        self.descEdit = QLineEdit()
        self.descEdit.setText(currentPanelDescription)
        self.descEdit.setPlaceholderText("Enter panel description (optional)...")
        descLayout.addWidget(descLabel)
        descLayout.addWidget(self.descEdit)
        mainLayout.addLayout(descLayout)
        
        # Buttons
        buttonLayout = QHBoxLayout()
        renameButton = QPushButton("Rename Panel", clicked=self.confirmRename)
        cancelButton = QPushButton("Cancel", clicked=self.reject)
        buttonLayout.addStretch()
        buttonLayout.addWidget(renameButton)
        buttonLayout.addWidget(cancelButton)
        mainLayout.addLayout(buttonLayout)
        
        mainLayout.addStretch()
        self.setLayout(mainLayout)
    
    def confirmRename(self):
        """Validate and accept panel rename"""
        self.panelName = self.nameEdit.text().strip()
        
        if not self.panelName:
            QMessageBox.warning(self, "Invalid Input", "Please enter a panel name.")
            return
        
        if self.panelName in self.existingPanelNames:
            QMessageBox.warning(self, "Duplicate Name", f"Panel '{self.panelName}' already exists.")
            return
        
        self.panelDescription = self.descEdit.text().strip()
        self.accept()
