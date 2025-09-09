#NOT RELEASED FOR USE
from screeninfo import get_monitors
import os, re, json, sys

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *

from reportlab.lib import colors
from reportlab.lib.pagesizes import inch
from reportlab.platypus import Paragraph, Table, PageBreak, PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from glob import glob
from PyPDF2 import PdfMerger

import pyodbc
import pandas as pd

import traceback
from revisionWindow import revisionWindow
from cableWindow import cableWindow
from customWidgets import customTableWidgetItem
from signals import signalClass
from pdfCanvases import NumberedPageCanvas8x11, NumberedPageCanvas11x8, NumberedPageCanvas17x11



def naturalSortKey(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(re.compile('([0-9]+)'), s)]

#MAIN WINDOW
class mainProgram(QMainWindow):
    def __init__(self):
        super(mainProgram, self).__init__()
        self.declareVariables()
        self.buildPreferencesWindow()
        self.connectSignals()
        self.connectShortcuts()
        self.startupMessage()
        if self.newFile == False:
            self.loadExistingFile()
        else:
            self.buildNewMatlist()
        self.buildMainWindow()
        self.buildUI()
        self.scaleUI()
        self.selectMasterMatlistFile()
        self.buildMasterMatList()
        self.saved = True

    #INIT FUNCTIONS
    def declareVariables(self):
        self.monitor = get_monitors()
        
        self.signals = signalClass()

        self.saved: bool = False
        self.loosePanelPresent: bool = False
        self.newFile: bool = True
        self.hidingMenu: bool = False

        self.currentlySelectedCell:list = [0,0]
        self.panelNames:list = []
        self.panelDescriptions:list = []
        self.uniqueItemNumbers:list = []

        self.masterMatList: dict = {}
        self.data: dict = {}

        self.masterMatListPath: str = ""
        self.matListFileName: str = ''
        self.pdfFileName: str = ''
        self.cutsheetFolderpath: str = ''

        self.quit = QAction("Quit",self)

        self.addItemButton = QPushButton('Add Item: 0',clicked=self.addItem)
        self.saveButton = QPushButton('Save',clicked=self.save)
        self.saveAsButton = QPushButton('Save As',clicked=self.saveAs)
        self.deleteRowButton = QPushButton(f'Delete Item: ',clicked=self.deleteItem)
        self.addPanelButton = QPushButton('Add Panel',clicked=self.addPanel)
        self.deletePanelButton = QPushButton('Delete Panel', clicked=self.deletePanel)
        self.hintsButton = QPushButton('Hints',clicked=self.displayHints)
        self.renamePanelButton = QPushButton('Rename Panel',clicked=self.renamePanel)
        self.addLooseButton = QPushButton('Add "Loose and Not Mounted"',clicked=self.addLoose)
        self.revisionDataWindowButton = QPushButton("Revisions",clicked=self.showRevisionData)
        self.cableDataWindowButton = QPushButton("Show Cable Data",clicked=self.showCableData)
        self.searchByKeywordButton = QPushButton("Search by Keyword",clicked=self.searchByKeyword)
        self.preferencesWindowButton = QPushButton("Preferences",clicked=self.showPreferencesWindow)
        self.showHideMenuButton = QPushButton("<",clicked=self.showHideMenu)
        self.cutSheetLocationFileDialogButton = QPushButton("Select Cutsheet PDF Directory",clicked=self.showCutsheetLocationFileDialog)
        
        self.includeCutsheetsCheckBox = QCheckBox()

        self.newPanelName = QLineEdit()
        self.newPanelDescription = QLineEdit()

        self.cutsheetLocationFileDialog = QFileDialog()
        self.cutsheetLocationFileDialog.setFileMode(QFileDialog.Directory)

        self.addItemSelect = QComboBox()

        self.dockLayout = QFormLayout()

        self.dockMenu = QWidget()
        self.mainWindowWidget = QWidget()

        self.dock = QDockWidget('Menu')

        self.tableWidget = QTableWidget()

        self.mainWindowLayout = QGridLayout()
        self.searchResultsLayout = QGridLayout()

        self.searchResults = QDialog()

        self.searchResultsList = QListWidget()

        self.descriptionWidget = QLabel()
        
        self.refreshCellsShortcut = QShortcut(QtGui.QKeySequence(self.tr("R")),self)
        self.refreshDockShortcut = QShortcut(QtGui.QKeySequence(self.tr("D")),self)
        self.helpShortcut = QShortcut(QtGui.QKeySequence(self.tr("H")),self)
        self.cellNoteShortcut = QShortcut(QtGui.QKeySequence(self.tr('N')),self)

        self.scaleWidget = QSpinBox()
        

        self.preferencesWindow = QDialog()
        self.preferencesWindowLayout = QGridLayout()
        






        #self.revisionDataWindow1 = revisionWindow()
        #self.cableDataWindow = cableWindow()
        #self.selectMasterMatlistButton = QPushButton("Select Master Material List",clicked=self.selectMasterMatlistFile)

    def buildPreferencesWindow(self):
        self.scaleWidget.setValue(100)
        self.scaleWidget.setMinimum(10)#10% size
        self.scaleWidget.setMaximum(300)#300% size
        self.scaleWidget.valueChanged.connect(self.scaleUI)
        self.preferencesWindowLayout.addWidget(QLabel("UI Scale"),0,0)
        self.preferencesWindowLayout.addWidget(self.scaleWidget,0,1)
        self.preferencesWindowLayout.addWidget(QLabel("Include Cutsheets"),1,0)
        self.preferencesWindowLayout.addWidget(self.includeCutsheetsCheckBox,1,1)
        self.preferencesWindowLayout.addWidget(QLabel("Cutsheet Location"),2,0)
        self.preferencesWindowLayout.addWidget(self.cutSheetLocationFileDialogButton,2,1)
        self.preferencesWindow.setLayout(self.preferencesWindowLayout)
        self.preferencesWindow.setWindowTitle("User Preferences")
        self.preferencesWindow.setMinimumSize(500,500)



    def showCutsheetLocationFileDialog(self):
        self.cutsheetLocationFileDialog.exec()


    def connectSignals(self):
        self.signals.saveCellData.connect(self.saveCellData)
        self.quit.triggered.connect(self.closeEvent)
    def connectShortcuts(self):
        self.refreshCellsShortcut.activated.connect(self.refreshCells)
        #self.refreshDockShortcut.activated.connect(self.buildDock)
        self.helpShortcut.activated.connect(self.displayHints)
        self.cellNoteShortcut.activated.connect(self.addCellNote)
    def startupMessage(self):
        newFileDialog = QDialog()
        newFileDialogLayout = QGridLayout()
        newFileDialogMessage = QLabel("Create New Material List?")
        newFileRadioButtonYes = QRadioButton()
        newFileRadioButtonNo = QRadioButton()
        newFileDialogAccept = QPushButton('Enter')

        newFileDialog.setWindowTitle('New Material List?')
        newFileDialog.setMinimumSize(400,50)
        newFileRadioButtonYes.setText('New Material List')
        newFileRadioButtonNo.setText('Select Existing Material List')
        newFileDialogAccept.clicked.connect(newFileDialog.close)

        newFileDialogLayout.addWidget(newFileDialogMessage,0,0)
        newFileDialogLayout.addWidget(newFileRadioButtonYes,1,0)
        newFileDialogLayout.addWidget(newFileRadioButtonNo,1,1)
        newFileDialogLayout.addWidget(newFileDialogAccept)

        newFileDialog.setLayout(newFileDialogLayout)
        newFileDialog.exec()

        if newFileRadioButtonYes.isChecked():
            self.newFile = True
        if newFileRadioButtonNo.isChecked():
            self.newFile = False
        if not (newFileRadioButtonYes.isChecked() or newFileRadioButtonNo.isChecked()):
            sys.exit()
    def loadExistingFile(self):
        file = QFileDialog()
        file.setNameFilters(["Text files (*.csv *.json)"])
        file.exec()
        try:
            self.matListFileName = file.selectedFiles()[0]
            self.pdfFileName = os.path.splitext(self.matListFileName)[0]+'.pdf'
            with open(self.matListFileName) as jsonFile:
                self.data = json.load(jsonFile)
            self.panelNames = [header for header in self.data if header not in ["revisions","cables", "miscellaneousInfo"]]
            self.panelDescriptions = [self.data[header]["description"] for header in self.data if header not in ["revisions","cables", "miscellaneousInfo"] and "description" in self.data[header]]
            self.loosePanelPresent = 'Loose and Not Mounted' in self.data
            self.masterMatListPath = self.data["miscellaneousInfo"]["masterMatListPath"]
            self.uniqueItemNumbers = [item for item in self.data[list(self.data.keys())[0]] if item != 'description']
            self.uniqueItemNumbers.sort(key=naturalSortKey)
        except:
            message = QMessageBox(text='Error Loading File\nNew File Being Created')
            message.exec()
            self.newFile = True
    def buildNewMatlist(self):
        self.matListFileName = 'newFile.json'
        self.pdfFileName = os.path.splitext(self.matListFileName)[0]+'.pdf'
        self.panelNames = []
        self.data = {}
        self.data['revisions'] = {"date":[],"user":[],"description":[]}
        self.data['cables'] = []
        self.data['miscellaneousInfo'] = {"masterMatListPath":""}
    def buildMainWindow(self):
        self.setGeometry(QtCore.QRect(int(self.monitor[0].width*.1),int(self.monitor[0].height*.1),int(self.monitor[0].width*.8),int(self.monitor[0].height*.8)))
        filename = os.path.basename(self.matListFileName).split('.')[0]
        self.setWindowTitle(f'{filename} Contract List')    
    def buildUI(self):
        self.tableWidget.setColumnCount(len(self.panelNames))
        self.tableWidget.setRowCount(len(self.uniqueItemNumbers))
        self.tableWidget.setHorizontalHeaderLabels(self.panelNames)
        self.tableWidget.setVerticalHeaderLabels(self.uniqueItemNumbers)
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setTabKeyNavigation(False)
        self.tableWidget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tableWidget.verticalScrollBar().setSingleStep(20)
        self.tableWidget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tableWidget.horizontalScrollBar().setSingleStep(20)
        self.tableWidget.itemSelectionChanged.connect(self.tableItemSelectionChanged)
        self.tableWidget.cellDoubleClicked.connect(self.showItemDescription)
        for rowIndex, row in enumerate(self.uniqueItemNumbers):
            for columnIndex, column in enumerate(self.panelNames):
                self.tableWidget.setCellWidget(rowIndex,columnIndex,customTableWidgetItem(self.signals, self.tableWidget, count=int(self.data[column][row]['count']) if self.data[column][row]['count'] != '1 Lot' else '1 Lot',deviceNames=self.data[column][row]['names'],coordinates=(rowIndex,columnIndex), note=self.data[column][row]['note']))
        self.refreshCells()
        
        self.addItemSelect.currentTextChanged.connect(self.updateAddRowButton)
        for item in self.masterMatList.keys():
            self.addItemSelect.addItem(item)

        self.newPanelName.setPlaceholderText('Panel Name')
        self.newPanelDescription.setPlaceholderText('Panel Description')
            
        self.mainWindowLayout.addWidget(self.addItemSelect,0,0)
        self.mainWindowLayout.addWidget(self.addItemButton,1,0)
        self.mainWindowLayout.addWidget(self.deleteRowButton,4,0)
        self.mainWindowLayout.addWidget(self.searchByKeywordButton,2,0)

        self.mainWindowLayout.addWidget(self.newPanelName,0,1)
        self.mainWindowLayout.addWidget(self.newPanelDescription,1,1)
        self.mainWindowLayout.addWidget(self.addPanelButton,2,1)
        self.mainWindowLayout.addWidget(self.renamePanelButton,5,1)
        self.mainWindowLayout.addWidget(self.deletePanelButton,4,1)
        self.mainWindowLayout.addWidget(self.addLooseButton,3,1)
        if self.loosePanelPresent == True:
            self.addLooseButton.setDisabled(True)
            self.addLooseButton.hide()
        
        self.mainWindowLayout.addWidget(self.revisionDataWindowButton,12,1)
        self.mainWindowLayout.addWidget(self.cableDataWindowButton,8,1)

        self.mainWindowLayout.addWidget(self.saveButton,13,1)
        self.mainWindowLayout.addWidget(self.saveAsButton,14,1)
        self.mainWindowLayout.addWidget(self.hintsButton,14,0)
        #self.mainWindowLayout.addWidget(self.scaleWidget,13,0)
        self.mainWindowLayout.addWidget(self.preferencesWindowButton,13,0)

        self.mainWindowLayout.addWidget(self.showHideMenuButton,0,2,15,1)

        self.mainWindowLayout.addWidget(self.tableWidget,0,3,15,1)

        self.mainWindowWidget.setLayout(self.mainWindowLayout)
        self.setCentralWidget(self.mainWindowWidget)

    def scaleUI(self):
        buttonWidth = int(self.monitor[0].width*.1*self.scaleWidget.value()/100)
        self.newPanelDescription.setFixedWidth(buttonWidth)
        self.newPanelName.setFixedWidth(buttonWidth)
        self.searchByKeywordButton.setFixedWidth(buttonWidth)
        self.cableDataWindowButton.setFixedWidth(buttonWidth)
        self.revisionDataWindowButton.setFixedWidth(buttonWidth)
        self.addLooseButton.setFixedWidth(buttonWidth)
        self.renamePanelButton.setFixedWidth(buttonWidth)
        self.hintsButton.setFixedWidth(buttonWidth)
        self.deletePanelButton.setFixedWidth(buttonWidth)
        self.addPanelButton.setFixedWidth(buttonWidth)
        self.deleteRowButton.setFixedWidth(buttonWidth)
        self.saveAsButton.setFixedWidth(buttonWidth)
        self.saveButton.setFixedWidth(buttonWidth)
        self.addItemButton.setFixedWidth(buttonWidth)


    def showPreferencesWindow(self):
        self.preferencesWindow.exec()

    def showHideMenu(self):
        if self.hidingMenu == False:
            self.addItemButton.hide()
            self.saveButton.hide()
            self.saveAsButton.hide()
            self.deleteRowButton.hide()
            self.addPanelButton.hide()
            self.deletePanelButton.hide()
            self.hintsButton.hide()
            self.renamePanelButton.hide()
            self.addLooseButton.hide()
            self.revisionDataWindowButton.hide()
            self.cableDataWindowButton.hide()
            self.searchByKeywordButton.hide()
            self.preferencesWindowButton.hide()
            self.cutSheetLocationFileDialogButton.hide()
            self.newPanelName.hide()
            self.newPanelDescription.hide()
            self.addItemSelect.hide()

            #rest of buttons here
            self.hidingMenu = True
            self.showHideMenuButton.setText(">")
            pass
        else:
            self.addItemButton.show()
            self.saveButton.show()
            self.saveAsButton.show()
            self.deleteRowButton.show()
            self.addPanelButton.show()
            self.deletePanelButton.show()
            self.hintsButton.show()
            self.renamePanelButton.show()
            self.addLooseButton.show()
            self.revisionDataWindowButton.show()
            self.cableDataWindowButton.show()
            self.searchByKeywordButton.show()
            self.preferencesWindowButton.show()
            self.cutSheetLocationFileDialogButton.show()
            self.newPanelName.hide()
            self.newPanelDescription.hide()
            self.addItemSelect.hide()
            #rest of buttons here
            self.hidingMenu = False
            self.showHideMenuButton.setText("<")
            pass



    def selectMasterMatlistFile(self):
        if not self.masterMatListPath:
            fileDialog = QFileDialog()
            fileDialog.setWindowTitle("Select Master Material List Database")
            fileDialog.setNameFilters(["Access Database files (*.accdb)"])
            fileDialog.exec()
            self.masterMatListPath = fileDialog.selectedFiles()[0]
    def buildMasterMatList(self):
        self.masterMatList = self.queryDatabase("SELECT [ItemNo], [Desc] FROM MaterialDescriptionforPython ORDER BY ItemNo",self.masterMatListPath)
        self.masterMatList = {item[0].lstrip(): item[1] for item in self.masterMatList}
        for item in sorted(self.masterMatList.keys(), key=naturalSortKey):
            self.addItemSelect.addItem(item)


    #MISC FUNCTIONS TO BE SORTED LATER
    def searchByKeyword(self):
        keywordEntry = QInputDialog.getText(self,'Search by Keyword','Enter Keywords (split by "%") to Search in Item Descriptions:')
        if keywordEntry[1] == True and keywordEntry[0] != '':
            results = []
            keywords = keywordEntry[0].split("%")
            for item in self.masterMatList:
                itemNumberValid = True
                for keyword in keywords:
                    if keyword.lower() not in self.masterMatList[item].lower():
                        itemNumberValid = False
                if itemNumberValid == True:
                    results.append(item)
            #results = [item for item in self.masterMatList if keyword[0].lower() in self.masterMatList[item].lower()]
            results.sort(key=naturalSortKey)
            
            self.searchResults.setMaximumWidth(1000)
            self.searchResults.setMinimumWidth(1000)
            self.searchResults.setMaximumHeight(1000)
            self.searchResults.setMinimumHeight(1000)
            
            
            self.descriptionWidget.setWordWrap(True)
            
            self.searchResultsList.setMaximumWidth(200)
            self.searchResultsList.setMinimumWidth(200)
            self.searchResultsList.currentTextChanged.connect(self.showDescription)
            for item in results:
                self.searchResultsList.addItem(item)


            self.searchResults.setWindowTitle('Search Results')
            self.searchResultsLayout.addWidget(QLabel(f'Items containing "{keywordEntry[0]}":'),0,0)
            self.searchResultsLayout.addWidget(self.searchResultsList,1,0)
            self.searchResultsLayout.addWidget(self.descriptionWidget,1,2)
            
            self.searchResults.setLayout(self.searchResultsLayout)
            self.searchResultsList.setCurrentRow(0)
            self.searchResults.exec()
    def showDescription(self):
        self.descriptionWidget.setText("Item " + self.searchResultsList.currentItem().text() + ":\n" + self.masterMatList[self.searchResultsList.currentItem().text()].replace('<br/>','\n'))


    #GETTER FUNCTIONS
    def getAllDeviceNames(self):
        deviceNames = []
        for rowIndex in range(len(self.uniqueItemNumbers)):
            for columnIndex in range(len(self.panelNames)):
                deviceNames.extend([deviceName.text() for deviceName in self.tableWidget.cellWidget(rowIndex,columnIndex).deviceNames])
        return deviceNames
    def getCableOptions(self):
        cableOptions = self.queryDatabase("SELECT [Material.ItemNo], [Part Number], [Length] FROM Material WHERE Length <> 0 AND Manufacturer = 'SEL' ORDER BY ItemNo;",self.masterMatListPath)
        itemNumbers = [cableOptions[i][0].lstrip() for i in range(len(cableOptions))]
        cableTypes = [cableOptions[i][1] for i in range(len(cableOptions))]
        cableLengths = [cableOptions[i][2] for i in range(len(cableOptions))]
        availableCableNumbers = list(set(itemNumbers)&set(self.uniqueItemNumbers))
        availableCableTypes = [cableTypes[itemNumbers.index(availableCableNumbers[i])].split("-")[0] for i in range(len(availableCableNumbers))]
        availableCableLengths = [cableLengths[itemNumbers.index(availableCableNumbers[i])] for i in range(len(availableCableNumbers))]
        return [{"itemNo":availableCableNumbers[i],"cableType":availableCableTypes[i],"length":str(availableCableLengths[i])} for i in range(len(availableCableNumbers))]
    def getRelayTypes(self):
        availableRelayShortnames = self.queryDatabase("SELECT [ItemNo], [Short Name] FROM Material WHERE Material.Manufacturer = 'SEL' AND [Short Name] IS NOT NULL ORDER BY Material.ItemNo;",self.masterMatListPath)
        availableRelayShortnames = list(set([availableRelayShortnames[i][1] for i in range(len(availableRelayShortnames)) if availableRelayShortnames[i][0].lstrip() in self.uniqueItemNumbers]))
        availableRelayShortnames.sort()
        availableRelayShortnames = [name.split(" ")[0] for name in availableRelayShortnames]
        return availableRelayShortnames
    def getCableRoutingOptions(self):
        return {"relayTypes":self.getRelayTypes(), "deviceNames":self.getAllDeviceNames(), "panelNos":self.panelNames}

    #KEY SHORTCUTS FUNCTIONS
    def refreshCells(self):
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
    def displayHints(self):
        hints = QMessageBox()
        hints.setWindowTitle('Hints')
        hints.setText('Shortcuts:\n\'R\': Resize Cells to Fit Contents\n\'D\': Show Menu\n\'H\': Display Hints\n\'N\': Add Note to Currently Selected Cell\nDouble-Click Cell: Show Item Description\nType: "<br/>" when entering data to force a new line')
        hints.exec()
    def addCellNote(self):
        self.saved = False
        self.currentlySelectedCell = (self.tableWidget.currentRow(),self.tableWidget.currentColumn())
        self.tableWidget.cellWidget(self.currentlySelectedCell[0],self.currentlySelectedCell[1]).note = QInputDialog.getText(self,'Cell Note',f"Enter Note for item {self.uniqueItemNumbers[self.currentlySelectedCell[0]]} on panel {self.panelNames[self.currentlySelectedCell[1]]}",text=self.tableWidget.cellWidget(self.currentlySelectedCell[0],self.currentlySelectedCell[1]).note)[0]

    #SIGNAL FUNCTIONS
    def saveCellData(self):
        self.saved = False

    #SAVING FUNCTIONS
    def developOutputDictionary(self):
        outputDictionary = {}
        for column, panel in enumerate(self.panelNames):
            outputDictionary[panel] = {"description":self.panelDescriptions[column] if column < len(self.panelDescriptions) else ""}
            for row, item in enumerate(self.uniqueItemNumbers):
                outputDictionary[panel][item] = {"names": [i.text() for i in self.tableWidget.cellWidget(row,column).deviceNames], "description":"","note":self.tableWidget.cellWidget(row, column).note,"count":self.tableWidget.cellWidget(row,column).countSelect.value() if not self.tableWidget.cellWidget(row,column).oneLotCheckBox.isChecked() else '1 Lot'} #Fill this dict using one-line method
        outputDictionary['revisions'] = self.data['revisions']
        outputDictionary['cables'] = self.data['cables']
        outputDictionary['miscellaneousInfo'] = {"masterMatListPath":self.masterMatListPath}
        return outputDictionary
    def saveJSONFile(self):
        with open(self.matListFileName,'w') as outfile:
            json.dump(self.developOutputDictionary(),outfile)
    def save(self):
        if self.newFile:
            self.matListFileName = QFileDialog.getSaveFileName(filter="*.json")[0]
            self.pdfFileName = os.path.splitext(self.matListFileName)[0]+'.pdf'
            self.newFile = False
        self.saveJSONFile()
        self.makePDF()
        if self.includeCutsheetsCheckBox.isChecked() == True:
            self.combineCutsheets()
        self.saved = True
        message = QMessageBox()
        message.setText(f'PDF and JSON saved in {os.path.split(self.matListFileName)[0]}')
        message.exec()
    def saveAs(self):
        self.newFile = True
        self.save()

    #MENU FUNCTIONS
    def addItem(self):
        if self.addItemSelect.currentText() not in [self.tableWidget.verticalHeaderItem(row).text() for row in range(self.tableWidget.rowCount())]:
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            for panelIndex in range(self.tableWidget.columnCount()):
                self.tableWidget.setCellWidget(self.tableWidget.rowCount()-1,panelIndex,customTableWidgetItem(self.signals, self.tableWidget, coordinates=(self.tableWidget.rowCount()-1,panelIndex)))
                self.tableWidget.cellWidget(self.tableWidget.rowCount()-1,panelIndex).showDevices = True
            self.uniqueItemNumbers.append(self.addItemSelect.currentText())
        self.tableWidget.setVerticalHeaderLabels(self.uniqueItemNumbers)
        self.refreshCells()
        self.saved = False
    def updateAddRowButton(self):
        self.addItemButton.setText('Add Item: '+self.addItemSelect.currentText())
    def deleteItem(self):
        if len(self.uniqueItemNumbers) > 0:
            items = [self.tableWidget.verticalHeaderItem(row).text() for row in range(self.tableWidget.rowCount())]
            self.uniqueItemNumbers.remove(items[self.currentlySelectedCell[0]])
            self.tableWidget.removeRow(self.currentlySelectedCell[0])
        if len(self.uniqueItemNumbers) > 0:
            self.deleteRowButton.setText(f'Delete Item: {items[self.currentlySelectedCell[0]]}')
        else:
            self.deleteRowButton.setText(f'')
        self.saved = False
    def addPanel(self):        
        self.panelNames.append(self.newPanelName.text())
        self.panelDescriptions.append(self.newPanelDescription.text())
        self.tableWidget.insertColumn(self.tableWidget.columnCount())
        for row in range(self.tableWidget.rowCount()):
            cell = customTableWidgetItem(self.signals,self.tableWidget,coordinates=(row,self.tableWidget.columnCount()-1))
            cell.showDevices = True
            self.tableWidget.setCellWidget(row,self.tableWidget.columnCount()-1,cell)
        self.tableWidget.setHorizontalHeaderLabels(self.panelNames)
        self.newPanelName.setText('')
        self.newPanelDescription.setText('')
        self.refreshCells()
        self.saved = False
    def deletePanel(self):
        if self.panelNames[self.currentlySelectedCell[1]] == 'Loose and Not Mounted':
            self.loosePanelPresent = False
            self.addLooseButton.setDisabled(False)
            self.addLooseButton.show()
        self.panelNames.remove(self.panelNames[self.currentlySelectedCell[1]])
        self.tableWidget.removeColumn(self.currentlySelectedCell[1])
        self.saved = False
    def renamePanel(self):
        newPanelName, ok = QInputDialog.getText(None, "Rename Panel:", "Rename Panel:")
        newPanelDescription, ok2 = QInputDialog.getText(None, "New Panel Description:", "Panel Description:")
        self.panelNames[self.currentlySelectedCell[1]] = newPanelName
        self.panelDescriptions[self.currentlySelectedCell[1]] = newPanelDescription
        self.tableWidget.setHorizontalHeaderLabels(self.panelNames)
        self.saved = False
    def addLoose(self):
        if not self.loosePanelPresent:
            self.panelNames.append('Loose and Not Mounted')
            self.tableWidget.insertColumn(self.tableWidget.columnCount())
            for row in range(self.tableWidget.rowCount()):
                cell = customTableWidgetItem(self.signals,self.tableWidget, coordinates=(row,self.tableWidget.columnCount()-1))
                self.tableWidget.setCellWidget(row,self.tableWidget.columnCount()-1,cell)
            self.tableWidget.setHorizontalHeaderLabels(self.panelNames)
            self.newPanelName.setText('')
            self.refreshCells()
            self.saved = False
            self.loosePanelPresent = True
            self.addLooseButton.setDisabled(True)
            self.addLooseButton.hide()

    #OTHER WINDOWS
    def showRevisionData(self):
        self.revisionDataWindow1 = revisionWindow(self.signals, self.data['revisions'])
        self.revisionDataWindow1.exec()
        if self.data['revisions'] != self.revisionDataWindow1.revisionData:
            self.saved = False
            self.data['revisions'] = self.revisionDataWindow1.revisionData
    def showCableData(self):
        self.cableDataWindow = cableWindow(self.signals,self.data['cables'],self.getCableRoutingOptions(),self.getCableOptions())
        self.cableDataWindow.exec()
        if self.data['cables'] != self.cableDataWindow.cableData:
            self.saved = False
            self.data['cables'] = self.cableDataWindow.cableData

    #DATABASE FUNCTIONS
    def queryDatabase(self, query = "", databaseLocation = ""):
        databaseConnectionInfo = ("DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};""DBQ="+databaseLocation)
        try: 
            connection = pyodbc.connect(databaseConnectionInfo)
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            data = pd.DataFrame.from_records(rows, columns=columns)
        finally:
            if 'connection' in locals() and connection:
                connection.close()
        return data.values.tolist()

    #EVENT INTERCEPTION FUNCTIONS
    def closeEvent(self,event):
        if self.saved == False:
            close = QMessageBox.question(self,'QUIT','Quit Without Saving?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
            if close == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()  
    def showItemDescription(self):
        self.currentlySelectedCell = (self.tableWidget.currentRow(),self.tableWidget.currentColumn())
        description = QMessageBox()
        description.setWindowTitle(self.uniqueItemNumbers[self.tableWidget.currentRow()])
        description.setText(self.masterMatList[self.uniqueItemNumbers[self.tableWidget.currentRow()]].replace('<br/>','\n'))
        description.exec()
    def tableItemSelectionChanged(self):
        self.currentlySelectedCell = (self.tableWidget.currentRow(),self.tableWidget.currentColumn())
        if self.tableWidget.rowCount()>0:
            items = [self.tableWidget.verticalHeaderItem(row).text() for row in range(self.tableWidget.rowCount())]
            self.deleteRowButton.setText('Delete Item: '+items[self.currentlySelectedCell[0]])
        self.deletePanelButton.setText('Delete Panel: '+self.panelNames[self.currentlySelectedCell[1]])
        self.renamePanelButton.setText('Rename Panel: '+self.panelNames[self.currentlySelectedCell[1]])


    #PDF FUNCTIONS ----------- MAKE THESE A DISTINCT CLASS???
    def makeMatlistTable(self):
        styleCustomCenterJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=1, fontSize=8)
        styleCustomLeftJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=0, fontSize=8)
        matlistTableData = [['' for i in range(self.tableWidget.columnCount()+3)] for j in range(self.tableWidget.rowCount()+3)]
        matlistTableData[0][0] = os.path.splitext(os.path.split(self.matListFileName)[1])[0] + " MATERIAL LIST"
        matlistTableData[1][2] = Paragraph('QUANTITY / DEVICE NAMES', styleCustomCenterJustified)
        matlistTableData[2][0] = Paragraph('ITEM NO.',styleCustomCenterJustified)
        matlistTableData[2][1] = Paragraph('EQUIPMENT DESCRIPTION',styleCustomCenterJustified)
        matlistTableData[2][2] = Paragraph('TOTAL',styleCustomCenterJustified)
        #Fill Headers
        for panelIndex, panel in enumerate(self.panelNames):
            matlistTableData[2][panelIndex+3] = Paragraph(panel + "<br/>" + self.panelDescriptions[panelIndex], styleCustomCenterJustified)
        #Fill Item Count and Names Cells
        for rowIndex in range(self.tableWidget.rowCount()):
            for columnIndex in range(0, self.tableWidget.columnCount()):
                if self.tableWidget.cellWidget(rowIndex,columnIndex).oneLotCheckBox.isChecked():
                    matlistTableData[rowIndex+3][columnIndex+3] = Paragraph('1 Lot<br/>'+self.tableWidget.cellWidget(rowIndex,columnIndex).note,styleCustomCenterJustified)
                else:
                    matlistTableData[rowIndex+3][columnIndex+3] = Paragraph('<br/>'.join([str(self.tableWidget.cellWidget(rowIndex,columnIndex).countSelect.value()),'<br/>'.join([i.text() for i in self.tableWidget.cellWidget(rowIndex,columnIndex).deviceNames])])+'<br/>'+self.tableWidget.cellWidget(rowIndex,columnIndex).note,styleCustomCenterJustified)
        #Fill Total Cells    
            if True in [self.tableWidget.cellWidget(rowIndex, columnIndex).oneLotCheckBox.isChecked() for columnIndex in range(0,self.tableWidget.columnCount())]:
                matlistTableData[rowIndex+3][2] = Paragraph('1 Lot',styleCustomCenterJustified)
            else:  
                matlistTableData[rowIndex+3][2] = Paragraph(str(sum([self.tableWidget.cellWidget(rowIndex, columnIndex).countSelect.value() for columnIndex in range(0,self.tableWidget.columnCount())])), styleCustomCenterJustified)
        #Fill Item Numbers and Descriptions
            matlistTableData[rowIndex+3][0] = Paragraph(self.tableWidget.verticalHeaderItem(rowIndex).text(), styleCustomCenterJustified)
            matlistTableData[rowIndex+3][1] = Paragraph(self.masterMatList[self.tableWidget.verticalHeaderItem(rowIndex).text()], styleCustomLeftJustified)
        
        matlistColumnWidths = [40,150,40]
        for i in matlistTableData[0][1:]:
            matlistColumnWidths.append((self.pageWidth*inch-200)/len(matlistTableData[0][1:]))
        matlistTable = Table(matlistTableData, colWidths=matlistColumnWidths, repeatRows=3, style=[
            ('GRID',(0,0),(-1,-1),0.5,colors.black),
            ('SPAN', (0,0), (-1, 0)),
            ('SPAN', (0,1), (1, 1)),
            ('SPAN', (2,1), (-1, 1)),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'TOP')])
        return matlistTable
    def makeRevisionTable(self):
        styleCustomCenterJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=1, fontSize=8)
        revisionTableData = [[Paragraph(key.upper(), styleCustomCenterJustified) for key in list(self.data['revisions'].keys())]]
        for rowIndex in range(len(list(self.data['revisions']['date']))):
            row = [Paragraph(str(self.data['revisions'][key][rowIndex]), styleCustomCenterJustified) for key in self.data['revisions'].keys()]
            revisionTableData.append(row)
        revisionTable = Table(revisionTableData, colWidths=[75, 50, 400], repeatRows=2, style=[  ('GRID',(0,0),(-1,-1),0.5,colors.black),],hAlign='LEFT')
        return revisionTable
    def makeCableTable(self):
        styleCustomCenterJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=1, fontSize=8)
        cableTableData = [['' for i in range(11)] for j in range(len(self.data['cables'])+3)]
        cableTableData[0][0] = os.path.splitext(os.path.split(self.matListFileName)[1])[0] + " CABLE LIST"
        cableTableData[1][1] = Paragraph("",style=styleCustomCenterJustified)
        cableTableData[1][3] = Paragraph("FROM",style=styleCustomCenterJustified)
        cableTableData[1][7] = Paragraph("TO",style=styleCustomCenterJustified)
        cableTableData[1][0] = Paragraph("ITEM NO",style=styleCustomCenterJustified)
        cableTableData[1][1] = Paragraph("CABLE TYPE",style=styleCustomCenterJustified)
        cableTableData[1][2] = Paragraph("CABLE LENGTH",style=styleCustomCenterJustified)
        cableTableData[2][3] = Paragraph("PANEL",style=styleCustomCenterJustified)
        cableTableData[2][4] = Paragraph("DEVICE NAME",style=styleCustomCenterJustified)
        cableTableData[2][5] = Paragraph("DEVICE TYPE",style=styleCustomCenterJustified)
        cableTableData[2][6] = Paragraph("PORT",style=styleCustomCenterJustified)
        cableTableData[2][7] = Paragraph("PANEL",style=styleCustomCenterJustified)
        cableTableData[2][8] = Paragraph("DEVICE NAME",style=styleCustomCenterJustified)
        cableTableData[2][9] = Paragraph("DEVICE TYPE",style=styleCustomCenterJustified)
        cableTableData[2][10] = Paragraph("PORT",style=styleCustomCenterJustified)

        for cableindex, cable in enumerate(self.data['cables']):
            cableTableData[cableindex+3][0] = Paragraph(cable['itemNo'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][1] = Paragraph(cable['cableType'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][2] = Paragraph(cable['length'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][3] = Paragraph(cable['from']['panelNo'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][4] = Paragraph(cable['from']['deviceNo'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][5] = Paragraph(cable['from']['relayType'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][6] = Paragraph(cable['from']['port'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][7] = Paragraph(cable['to']['panelNo'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][8] = Paragraph(cable['to']['deviceNo'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][9] = Paragraph(cable['to']['relayType'],style=styleCustomCenterJustified)
            cableTableData[cableindex+3][10] = Paragraph(cable['to']['port'],style=styleCustomCenterJustified)

        cableTable = Table(cableTableData, colWidths=[50,60,50,70,70,70,70,70,70,70,70], rowHeights=[25 for row in cableTableData], repeatRows=3, style=[
            ('GRID',(0,0),(-1,-1),0.5,colors.black),
            ('SPAN', (0,0), (-1, 0)),#Cable table header
            ('SPAN', (3,1), (6, 1)),#From header
            ('SPAN', (7,1), (10, 1)),#To header
            ('SPAN',(0,1),(0,2)),
            ('SPAN',(1,1),(1,2)),
            ('SPAN',(2,1),(2,2)),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'TOP')])
        return cableTable
    def makePDF(self):
        styleCustomCenterJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=1, fontSize=8)
        styleCustomLeftJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=0, fontSize=8)
        styleCustomRightJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=2, fontSize=8)
        self.pageWidth = 8.5
        self.pageHeight = 11
        if len(self.panelNames) > 5:
            self.pageWidth = 11
            self.pageHeight = 8.5
        if len(self.panelNames) > 9:
            self.pageWidth = 17
            self.pageHeight = 11
        matlistTable = self.makeMatlistTable()
        revisionTable = self.makeRevisionTable()
        cableTable = self.makeCableTable()
        pagesize = (self.pageWidth * inch, self.pageHeight * inch)
        doc = BaseDocTemplate(self.pdfFileName, pagesize=pagesize, leftMargin=.25*inch, rightMargin=.25*inch, topMargin=.25*inch, bottomMargin=.25*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        self.revisionNumber = Paragraph(f'Rev. {len(self.data['revisions']["date"])-1}', styleCustomLeftJustified)
        template1 = PageTemplate(id='test', frames=frame, onPage=self.drawRevisionNumber)        
        elements = []
        elements.append(matlistTable)
        elements.append(PageBreak())
        elements.append(cableTable)
        elements.append(PageBreak())
        elements.append(revisionTable)
        doc.addPageTemplates([template1])
        canvasSizeSelector = {(8.5,11):NumberedPageCanvas8x11,
                              (11,8.5):NumberedPageCanvas11x8,
                              (17,11):NumberedPageCanvas17x11}
        doc.build(elements, canvasmaker=canvasSizeSelector[(self.pageWidth,self.pageHeight)])
    def drawRevisionNumber(self, canvas, doc):
        w, h = self.revisionNumber.wrap(doc.width, doc.bottomMargin)
        self.revisionNumber.drawOn(canvas, doc.leftMargin, h)
    def combineCutsheets(self):
        rootDir = self.cutsheetLocationFileDialog.selectedFiles()[0]
        outputFileName = self.pdfFileName.rstrip(".pdf")+"(with cutsheets).pdf"
        merger = PdfMerger()
        allpdfs = [a for a in glob("*.pdf", root_dir=rootDir)]
        [merger.append(rootDir+"\\"+pdf) for pdf in allpdfs]
        with open(outputFileName, "wb") as new_file:
            merger.write(new_file)

        
#SIGNALS



if  __name__ == "__main__":
    app = QApplication(sys.argv)
    application = mainProgram()
    application.show()
    sys.exit(app.exec())


