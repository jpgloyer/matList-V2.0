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


import pyodbc
import pandas as pd

import traceback
from revisionWindow import revisionWindow
from cableWindow import cableWindow
from customWidgets import customTableWidgetItem
from pdfCanvases import NumberedPageCanvas8x11, NumberedPageCanvas11x8, NumberedPageCanvas17x11



def naturalSortKey(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(re.compile('([0-9]+)'), s)]

#Main Windows


class mainProgram(QMainWindow):
    def __init__(self):
        super(mainProgram, self).__init__()
        
        #Variable Declarations
        self.masterMatList = {}
        self.masterMatListPath = ""
        self.signals = signalClass()
        self.initComplete = False
        self.saved = False
        self.currentlySelectedCell = [0,0]
        self.loosePanelPresent = False
        self.uniqueItemNumbers = []
        #Signal/Function Connections
        self.signals.needsSaved.connect(self.needsSaved)
        self.signals.saveRevisionData.connect(self.saveRevisionData)
        self.signals.saveCableData.connect(self.saveCableData)
        #Keyboard Shortcut/Function Connections
        self.refreshCellsShortcut = QShortcut(QtGui.QKeySequence(self.tr("R")),self)
        self.refreshCellsShortcut.activated.connect(self.refreshCells)
        self.refreshDockShortcut = QShortcut(QtGui.QKeySequence(self.tr("D")),self)
        self.refreshDockShortcut.activated.connect(self.buildRightDock)
        self.helpShortcut = QShortcut(QtGui.QKeySequence(self.tr("H")),self)
        self.helpShortcut.activated.connect(self.displayHints)
        self.cellNoteShortcut = QShortcut(QtGui.QKeySequence(self.tr('N')),self)
        self.cellNoteShortcut.activated.connect(self.addCellNote)
        self.quit = QAction("Quit",self)
        self.quit.triggered.connect(self.closeEvent)



        self.startupMessage()
        if self.newFile == False:
            file = QFileDialog()
            file.setNameFilters(["Text files (*.csv *.json)"])
            file.exec()
            try:
                self.matListFileName = file.selectedFiles()[0]
                self.pdfFileName = os.path.splitext(self.matListFileName)[0]+'.pdf'
                data = self.importProject(self.matListFileName)
                self.getUniqueItemNumbers(data)
            except:
                message = QMessageBox(text='Error Loading File\nNew File Being Created')
                message.exec()
                self.newFile = True
        if self.newFile == True:
            data = self.buildNewMatlist()

        self.revisionData = data['revisions']
        self.cableData = data['cables']

        self.buildMainWindow()
        #self.getUniqueItemNumbers(data)
        self.buildInitialTable(data)
        self.buildRightDock()
        self.saved = True
        self.initComplete = True

    def startupMessage(self):
        "REFACTORED"
        newFileDialog = QDialog()
        newFileDialog.setWindowTitle('New Material List?')
        newFileDialog.setMinimumSize(400,50)
        newFileDialogLayout = QGridLayout()
        newFileDialogMessage = QLabel("Create New Material List?")
        newFileRadioButtonYes = QRadioButton()
        newFileRadioButtonYes.setText('New Material List')
        newFileRadioButtonNo = QRadioButton()
        newFileRadioButtonNo.setText('Select Existing Material List')
        newFileDialogAccept = QPushButton('Enter')
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

    def buildNewMatlist(self):
        self.matListFileName = 'newFile.json'
        self.pdfFileName = os.path.splitext(self.matListFileName)[0]+'.pdf'
        self.columnHeaders = []
        data = {}
        data['revisions'] = {"date":[],"user":[],"description":[]}
        data['cables'] = []
        data['miscellaneousInfo'] = {"masterMatListPath":""}
        return data
    
    def excludedColumnHeaders(self):
        "Returns a list of JSON headers that do not represent panels (or loose)"
        return ["revisions","cables", "miscellaneousInfo"]

    def importProject(self, inputFile):
        "REFACTORED"
        data = {}
        with open(inputFile) as jsonFile:
            data = json.load(jsonFile)
        self.columnHeaders = [header for header in data if header not in self.excludedColumnHeaders()]
        self.loosePanelPresent = 'Loose and Not Mounted' in data
        self.masterMatListPath = data["miscellaneousInfo"]["masterMatListPath"]

        return data   

    def buildMainWindow(self):
        self.monitor = get_monitors()
        self.setGeometry(QtCore.QRect(int(self.monitor[0].width*.1),int(self.monitor[0].height*.1),int(self.monitor[0].width*.8),int(self.monitor[0].height*.8)))
        filename = os.path.basename(self.matListFileName).split('.')[0]
        self.setWindowTitle(f'{filename} Contract List')

    def getUniqueItemNumbers(self,data):
        self.uniqueItemNumbers = [item for item in data[list(data.keys())[0]] if item != 'description']
        self.uniqueItemNumbers.sort(key=naturalSortKey)

    def buildInitialTable(self, data):

        dimensions = [len(self.uniqueItemNumbers),len(self.columnHeaders)]
        self.tableWidget = QTableWidget()                   
        self.tableWidget.setColumnCount(dimensions[1])
        self.tableWidget.setRowCount(dimensions[0])
        self.tableWidget.setHorizontalHeaderLabels(self.columnHeaders)
        self.tableWidget.setVerticalHeaderLabels(self.uniqueItemNumbers)
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setTabKeyNavigation(False)
        self.tableWidget.itemSelectionChanged.connect(self.tableItemSelectionChanged)
        self.tableWidget.cellDoubleClicked.connect(self.showItemDescription)

        #self.tableWidget.horizontalHeader().setSectionsMovable(True)
        #self.tableWidget.setHorizontalHeader(QtCore.Qt.BottomEdge)


        for rowIndex, row in enumerate(self.uniqueItemNumbers):
            for columnIndex, column in enumerate(self.columnHeaders):
                self.tableWidget.setCellWidget(rowIndex,columnIndex,customTableWidgetItem(self.signals, self.tableWidget, count=int(data[column][row]['count']) if data[column][row]['count'] != '1 Lot' else '1 Lot',deviceNames=data[column][row]['names'],coordinates=(rowIndex,columnIndex), note=data[column][row]['note']))

        self.refreshCells()
        self.setCentralWidget(self.tableWidget)

    def buildRightDock(self):
        if self.initComplete == True:
            self.removeDockWidget(self.dock)
        self.addItemButton = QPushButton('Add Item: 0',clicked=self.addItem)
        self.dockItemSelect = QComboBox()
        self.dockItemSelect.currentTextChanged.connect(self.updateAddRowButton)
        for item in self.masterMatList.keys():
            self.dockItemSelect.addItem(item)

        self.saveButton = QPushButton('Save',clicked=self.save)
        self.saveAsButton = QPushButton('Save As',clicked=self.saveAs)
        self.deleteRow = QPushButton(f'Delete Item: ',clicked=self.deleteItem)
        self.addPanelButton = QPushButton('Add Panel',clicked=self.addPanel)
        self.deletePanelButton = QPushButton('Delete Panel', clicked=self.deletePanel)
        self.newPanelName = QLineEdit()
        self.newPanelName.setPlaceholderText('Panel Name')
        self.hintsButton = QPushButton('Hints',clicked=self.displayHints)
        self.renamePanelButton = QPushButton('Rename Panel',clicked=self.renamePanel)
        self.addLooseButton = QPushButton('Add "Loose and Not Mounted"',clicked=self.addLoose)
        self.revisionDataWindowButton = QPushButton("Show Revision Data",clicked=self.showRevisionData)
        self.cableDataWindowButton = QPushButton("Show Cable Data",clicked=self.showCableData)
        #self.selectMasterMatlistButton = QPushButton("Select Master Material List",clicked=self.selectMasterMatlistFile)

        self.dockLayout = QFormLayout()
        self.dockLayout.addRow(self.dockItemSelect)
        self.dockLayout.addRow(self.addItemButton)
        self.dockLayout.addRow(self.deleteRow)
        self.dockLayout.addItem(QSpacerItem(50,50))
        self.dockLayout.addRow(self.newPanelName)
        self.dockLayout.addRow(self.addPanelButton)
        self.dockLayout.addRow(self.renamePanelButton)
        self.dockLayout.addRow(self.deletePanelButton)
        self.dockLayout.addRow(self.addLooseButton)
        self.dockLayout.addItem(QSpacerItem(50,50))
        self.dockLayout.addRow(self.revisionDataWindowButton)
        self.dockLayout.addRow(self.cableDataWindowButton)
        #self.dockLayout.addRow(self.selectMasterMatlistButton)
        self.dockLayout.addItem(QSpacerItem(50,50))
        self.dockLayout.addRow(self.saveButton)
        self.dockLayout.addRow(self.saveAsButton)
        self.dockLayout.addItem(QSpacerItem(50,300))
        self.dockLayout.addRow(self.hintsButton)
        
        self.dockMenu = QWidget()
        self.dockMenu.setLayout(self.dockLayout)
        self.dock = QDockWidget('Menu')
        self.dock.setWidget(self.dockMenu)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dock) 


        self.selectMasterMatlistFile()

#Key Shortcut Functions
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
        noteBox = QInputDialog()
        self.tableWidget.cellWidget(self.currentlySelectedCell[0],self.currentlySelectedCell[1]).note = noteBox.getText(self,'Cell Note',f"Enter Note for item {self.uniqueItemNumbers[self.currentlySelectedCell[0]]} on panel {self.columnHeaders[self.currentlySelectedCell[1]]}",text=self.tableWidget.cellWidget(self.currentlySelectedCell[0],self.currentlySelectedCell[1]).note)[0]

#Signal-Triggered Functions
    def needsSaved(self):
        self.saved = False

    def saveCableData(self):
        self.cableData = self.cableDataWindow.cableData
        self.saved = False

    def saveRevisionData(self):
        self.revisionData = self.revisionDataWindow1.revisionData
        self.saved = False

#Utility Functions
    def getAllDeviceNames(self):
        deviceNames = []
        for rowIndex in range(len(self.uniqueItemNumbers)):
            for columnIndex in range(len(self.columnHeaders)):
                deviceNames.extend([deviceName.text() for deviceName in self.tableWidget.cellWidget(rowIndex,columnIndex).deviceNames])
        return deviceNames
        
    def developOutputDictionary(self):
        "REFACTORED"
        outputDictionary = {}

        for column, panel in enumerate(self.columnHeaders):
            outputDictionary[panel] = {}
            for row, item in enumerate(self.uniqueItemNumbers):
                outputDictionary[panel][item] = {"names": [i.text() for i in self.tableWidget.cellWidget(row,column).deviceNames], "description":"","note":self.tableWidget.cellWidget(row, column).note,"count":self.tableWidget.cellWidget(row,column).countSelect.value() if not self.tableWidget.cellWidget(row,column).oneLotCheckBox.isChecked() else '1 Lot'} #Fill this dict using one-line method

        outputDictionary['revisions'] = self.revisionData
        outputDictionary['cables'] = self.cableData
        outputDictionary['miscellaneousInfo'] = {"masterMatListPath":self.masterMatListPath}
        return outputDictionary

    def saveJSONFile(self):
        
        with open(self.matListFileName,'w') as outfile:
            json.dump(self.developOutputDictionary(),outfile)

#Right Dock Functions
    def addItem(self):
        if self.dockItemSelect.currentText() not in [self.tableWidget.verticalHeaderItem(row).text() for row in range(self.tableWidget.rowCount())]:
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            for panelIndex in range(self.tableWidget.columnCount()):
                self.tableWidget.setCellWidget(self.tableWidget.rowCount()-1,panelIndex,customTableWidgetItem(self.signals, self.tableWidget, coordinates=(self.tableWidget.rowCount()-1,panelIndex)))
                self.tableWidget.cellWidget(self.tableWidget.rowCount()-1,panelIndex).showDevices = True
            self.uniqueItemNumbers.append(self.dockItemSelect.currentText())
        self.tableWidget.setVerticalHeaderLabels(self.uniqueItemNumbers)
        self.refreshCells()
        self.saved = False

    def updateAddRowButton(self):
        self.addItemButton.setText('Add Item: '+self.dockItemSelect.currentText())

    def save(self):
        #try:
        if self.newFile:
            self.matListFileName = QFileDialog.getSaveFileName(filter="*.json")[0]
            self.pdfFileName = os.path.splitext(self.matListFileName)[0]+'.pdf'
            self.newFile = False

        self.saveJSONFile()
        self.makePDF()
        self.saved = True

        message = QMessageBox()
        message.setText(f'PDF and JSON saved in {os.path.split(self.matListFileName)[0]}')
        message.exec()

        #except Exception as e:
        #    message = QMessageBox()
        #    message.setText(f"Error saving files: {e}")
        #    message.exec()

    def saveAs(self):
        self.newFile = True
        self.save()

    def deleteItem(self):
        if len(self.uniqueItemNumbers) > 0:
            items = [self.tableWidget.verticalHeaderItem(row).text() for row in range(self.tableWidget.rowCount())]
            self.uniqueItemNumbers.remove(items[self.currentlySelectedCell[0]])
            self.tableWidget.removeRow(self.currentlySelectedCell[0])
        if len(self.uniqueItemNumbers) > 0:
            self.deleteRow.setText(f'Delete Item: {items[self.currentlySelectedCell[0]]}')
        else:
            self.deleteRow.setText(f'')
        self.saved = False

    def addPanel(self):        
        self.columnHeaders.append(self.newPanelName.text())
        self.tableWidget.insertColumn(self.tableWidget.columnCount())
        for row in range(self.tableWidget.rowCount()):
            cell = customTableWidgetItem(self.signals,self.tableWidget,coordinates=(row,self.tableWidget.columnCount()-1))
            cell.showDevices = True
            self.tableWidget.setCellWidget(row,self.tableWidget.columnCount()-1,cell)
        self.tableWidget.setHorizontalHeaderLabels(self.columnHeaders)
        self.newPanelName.setText('')
        self.refreshCells()
        self.saved = False

    def deletePanel(self):
        if self.columnHeaders[self.currentlySelectedCell[1]] == 'Loose and Not Mounted':
            self.loosePanelPresent = False
        self.columnHeaders.remove(self.columnHeaders[self.currentlySelectedCell[1]])
        self.tableWidget.removeColumn(self.currentlySelectedCell[1])
        self.saved = False

    def renamePanel(self):
        newPanelName = QInputDialog()
        newPanelName.setWindowTitle("Rename Panel:")
        newPanelName.setLabelText("Rename Panel:")
        newPanelName.exec()
        name = newPanelName.textValue()
        self.columnHeaders[self.currentlySelectedCell[1]] = name
        self.tableWidget.setHorizontalHeaderLabels(self.columnHeaders)

    def addLoose(self):
        if not self.loosePanelPresent:
            self.columnHeaders.append('Loose and Not Mounted')
            self.tableWidget.insertColumn(self.tableWidget.columnCount())
            for row in range(self.tableWidget.rowCount()):
                cell = customTableWidgetItem(self.signals,self.tableWidget, coordinates=(row,self.tableWidget.columnCount()-1))
                
                

                self.tableWidget.setCellWidget(row,self.tableWidget.columnCount()-1,cell)
            self.tableWidget.setHorizontalHeaderLabels(self.columnHeaders)
            self.newPanelName.setText('')
            self.refreshCells()
            self.saved = False
            self.loosePanelPresent = True

    def getCableOptions(self):
        cableOptions = self.queryDatabase("SELECT [Material.ItemNo], [Part Number], [Length] FROM Material WHERE Length <> 0 AND Manufacturer = 'SEL' ORDER BY ItemNo;",self.masterMatListPath)
        
        return [{"itemNo":cableOptions[i][0],"cableType":cableOptions[i][1],"length":str(cableOptions[i][2])} for i in range(len(cableOptions))]

    def getCableRoutingOptions(self):
        return {"relayTypes":[], "deviceNames":self.getAllDeviceNames(), "panelNos":self.columnHeaders}

    def showRevisionData(self):
        self.revisionDataWindow1 = revisionWindow(self.signals, self.revisionData)
        self.revisionDataWindow1.show()

    def showCableData(self):
        self.cableDataWindow = cableWindow(self.signals,self.cableData,self.getCableRoutingOptions(),self.getCableOptions())
        self.cableDataWindow.show()

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
        #return [item[0] for item in data.values.tolist()]

    def selectMasterMatlistFile(self):
        if not self.masterMatListPath:
            try:
                fileDialog = QFileDialog()
                fileDialog.setWindowTitle("Select Master Material List Database")
                fileDialog.setNameFilters(["Access Database files (*.accdb)"])
                fileDialog.exec()
                self.masterMatListPath = fileDialog.selectedFiles()[0]
                self.masterMatList = self.queryDatabase("SELECT [ItemNo], [Desc] FROM MaterialDescriptionforPython ORDER BY ItemNo",self.masterMatListPath)
                self.masterMatList = {item[0].lstrip(): item[1] for item in self.masterMatList}
                
                for item in sorted(self.masterMatList.keys(), key=naturalSortKey):
                    self.dockItemSelect.addItem(item)
            except:
                pass
        else:
            try:
                self.masterMatList = self.queryDatabase("SELECT [ItemNo], [Desc] FROM MaterialDescriptionforPython ORDER BY ItemNo",self.masterMatListPath)
                self.masterMatList = {item[0].lstrip(): item[1] for item in self.masterMatList}
                
                for item in sorted(self.masterMatList.keys(), key=naturalSortKey):
                    self.dockItemSelect.addItem(item)
            except:
                pass

#Parent Function Redefinitions
    def closeEvent(self,event):
        if self.saved == False:
            close = QMessageBox.question(self,'QUIT','Quit Without Saving?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
            if close == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
  
#Table Events
    def showItemDescription(self):
        self.currentlySelectedCell = (self.tableWidget.currentRow(),self.tableWidget.currentColumn())
        description = QMessageBox()
        description.setWindowTitle(self.uniqueItemNumbers[self.tableWidget.currentRow()])
        description.setText(self.masterMatList[self.uniqueItemNumbers[self.tableWidget.currentRow()]].replace('<br/>','\n'))
        description.exec()

    def tableItemSelectionChanged(self):
        self.currentlySelectedCell = (self.tableWidget.currentRow(),self.tableWidget.currentColumn())
        if self.tableWidget.rowCount()>0:
            #self.deleteRow.setText('Delete Item: '+self.tableWidget.cellWidget(self.currentlySelectedCell[0],0).text)
            items = [self.tableWidget.verticalHeaderItem(row).text() for row in range(self.tableWidget.rowCount())]
            self.deleteRow.setText('Delete Item: '+items[self.currentlySelectedCell[0]])
        self.deletePanelButton.setText('Delete Panel: '+self.columnHeaders[self.currentlySelectedCell[1]])

#PDF Functions
    def makeMatlistTable(self):
        styleCustomCenterJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=1, fontSize=8)
        styleCustomLeftJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=0, fontSize=8)
        matlistTableData = [['' for i in range(self.tableWidget.columnCount()+3)] for j in range(self.tableWidget.rowCount()+3)]
        #matlistTableData[0][0] = os.path.basename(self.matListFileName).split('.')[0] + " Material List"
        matlistTableData[0][0] = os.path.splitext(os.path.split(self.matListFileName)[1])[0]
        matlistTableData[1][2] = Paragraph('QUANTITY / DEVICE NAMES', styleCustomCenterJustified)
        matlistTableData[2][0] = Paragraph('ITEM NO.',styleCustomCenterJustified)
        matlistTableData[2][1] = Paragraph('EQUIPMENT DESCRIPTION',styleCustomCenterJustified)
        matlistTableData[2][2] = Paragraph('Total',styleCustomCenterJustified)
        #Fill Headers
        for panelIndex, panel in enumerate(self.columnHeaders):
            matlistTableData[2][panelIndex+3] = Paragraph(panel, styleCustomCenterJustified)
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
        
        matlistColumnWidths = [40,150,30]
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
        revisionTableData = [[Paragraph(key.upper(), styleCustomCenterJustified) for key in list(self.revisionData.keys())]]
        for rowIndex in range(len(list(self.revisionData['date']))):
            row = [Paragraph(str(self.revisionData[key][rowIndex]), styleCustomCenterJustified) for key in self.revisionData.keys()]
            revisionTableData.append(row)
        revisionTable = Table(revisionTableData, colWidths=[75, 50, 400], repeatRows=2, style=[  ('GRID',(0,0),(-1,-1),0.5,colors.black),],hAlign='LEFT')
        return revisionTable

    def makePDF(self):
        styleCustomCenterJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=1, fontSize=8)
        styleCustomLeftJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=0, fontSize=8)
        styleCustomRightJustified = ParagraphStyle(name='BodyText', parent=getSampleStyleSheet()['BodyText'], spaceBefore=6, alignment=2, fontSize=8)
        self.pageWidth = 8.5
        self.pageHeight = 11
        if len(self.columnHeaders) > 5:
            self.pageWidth = 11
            self.pageHeight = 8.5
        if len(self.columnHeaders) > 9:
            self.pageWidth = 17
            self.pageHeight = 11
        matlistTable = self.makeMatlistTable()
        revisionTable = self.makeRevisionTable()
        pagesize = (self.pageWidth * inch, self.pageHeight * inch)
        doc = BaseDocTemplate(self.pdfFileName, pagesize=pagesize, leftMargin=.25*inch, rightMargin=.25*inch, topMargin=.25*inch, bottomMargin=.25*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        self.revisionNumber = Paragraph(f'Rev. {len(self.revisionData["date"])-1}', styleCustomLeftJustified)
        template1 = PageTemplate(id='test', frames=frame, onPage=self.drawRevisionNumber)        
        elements = []
        elements.append(matlistTable)
        elements.append(PageBreak())
        #elements.append(PageBreak())
        elements.append(revisionTable)
        doc.addPageTemplates([template1])
        canvasSizeSelector = {(8.5,11):NumberedPageCanvas8x11,
                              (11,8.5):NumberedPageCanvas11x8,
                              (17,11):NumberedPageCanvas17x11}
        doc.build(elements, canvasmaker=canvasSizeSelector[(self.pageWidth,self.pageHeight)])

    def drawRevisionNumber(self, canvas, doc):
        w, h = self.revisionNumber.wrap(doc.width, doc.bottomMargin)
        self.revisionNumber.drawOn(canvas, doc.leftMargin, h)


        
#Signals
class signalClass(QWidget):
    needsSaved = QtCore.pyqtSignal(bool)
    saveRevisionData = QtCore.pyqtSignal()
    saveCableData = QtCore.pyqtSignal()





        

if  __name__ == "__main__":
    app = QApplication(sys.argv)
    application = mainProgram()
    application.show()
    sys.exit(app.exec())


