from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget

class signalClass(QWidget):
    saveRevisionData = QtCore.pyqtSignal()
    saveCableData = QtCore.pyqtSignal()
    saveCellData = QtCore.pyqtSignal()