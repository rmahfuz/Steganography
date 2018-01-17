import sys
import glob
from scipy.misc import imsave

from PySide.QtCore import *
from PySide.QtGui import *
from SteganographyGUI import *
from Steganography import *
#============================================================================================================
class ModifiedQGraphicsView(QGraphicsView):
    received = Signal()
    def __init__(self, grp, originator):
        super(ModifiedQGraphicsView, self).__init__(grp, originator)
        #self.picArr = None
        self.picAddr = ''
    #--------------------------------------------------------------------------------------------
    def dragEnterEvent(self, e):
        #print('in dragEnterEvent')
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()
    #--------------------------------------------------------------------------------------------
    def dragMoveEvent(self, e):
        #print('in dragMoveEvent')
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()
    #--------------------------------------------------------------------------------------------
    def dropEvent(self, e):
        #print('in dropEvent')
        #print(e.mimeData().urls())
        if e.mimeData().hasUrls and str(e.mimeData().urls()[0]).split('.')[-1] == "png')":
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            for url in e.mimeData().urls():
                fname = str(url.toLocalFile())
            self.fname = fname
            #print('fname = ',fname)
            self.picAddr = fname
            self.received.emit()
            self.load_image()
        else:
            e.ignore()
    #--------------------------------------------------------------------------------------------
    def load_image(self):
        pixmap = QtGui.QPixmap(self.fname)
        pixmap = pixmap.scaled(500, 500, QtCore.Qt.KeepAspectRatio)
        scene = QtGui.QGraphicsScene()
        scene.addPixmap(pixmap)
        self.setScene(scene)
        self.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
#============================================================================================================
class Processor(QMainWindow, Ui_MainWindow):
#--------------------------------------------------------------------------------------------
    def __init__(self, parent=None):

        super(Processor, self).__init__(parent)
        self.setupUi(self)

        self.carrier1 = None
        self.carrier2 = None
        self.payload1 = None
        self.payload2 = None

        self.enableDragDrop()
        self.chkApplyCompression.stateChanged.connect(self.compressionChkChanged)
        self.slideCompression.valueChanged.connect(self.sliderChanged)
        self.btnSave.clicked.connect(self.handleSaveRequest)
        self.btnExtract.clicked.connect(self.extractCarrier)
        self.btnClean.clicked.connect(self.cleanCarrier)
        self.chkOverride.stateChanged.connect(self.chkEmbedEligibility)
#--------------------------------------------------------------------------------------------
    def enableDragDrop(self):
        self.viewCarrier1 = ModifiedQGraphicsView(self.grpCarrier1, self)
        self.viewCarrier1.setObjectName('self.viewCarrier1')
        self.viewCarrier1.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewCarrier1.received.connect(self.handleNewCarrier1)
        self.viewCarrier1.received.connect(self.chkEmbedEligibility)
        #.................................................................
        self.viewPayload1 = ModifiedQGraphicsView(self.grpPayload1, self)
        self.viewPayload1.setObjectName('self.viewPayload1')
        self.viewPayload1.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewPayload1.received.connect(self.handleNewPayload1)
        self.viewPayload1.received.connect(self.chkEmbedEligibility)
        #.................................................................
        self.viewCarrier2 = ModifiedQGraphicsView(self.grpCarrier2, self)
        self.viewCarrier2.setObjectName('self.viewCarrier2')
        self.viewCarrier2.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewCarrier2.received.connect(self.handleNewCarrier2)
#--------------------------------------------------------------------------------------------
    def handleNewCarrier1(self):
        #print('handling new carrier 1')
        self.carrier1 = Carrier(imread(self.viewCarrier1.picAddr))
        self.txtCarrierSize.setText(str(self.carrier1.img.shape[0] * self.carrier1.img.shape[1]))
        if self.carrier1.payloadExists():
            self.lblPayloadFound.setText(QtGui.QApplication.translate("MainWindow", ">>>>Payload Found<<<<", None, QtGui.QApplication.UnicodeUTF8))
            self.chkOverride.setEnabled(True)
        else:
            self.chkOverride.setEnabled(False)
            self.chkOverride.setChecked(False)
            self.lblPayloadFound.setText(QtGui.QApplication.translate("MainWindow", "", None, QtGui.QApplication.UnicodeUTF8))
#--------------------------------------------------------------------------------------------
    def handleNewPayload1(self):
        #print('handling new payload 1')
        self.payload1 = Payload(imread(self.viewPayload1.picAddr))
        self.txtPayloadSize.setText(str(len(self.payload1.json)))
        #self.txtPayloadSize.setText(str(self.calcPayloadSize(self.viewPayload1.picAddr)))
        self.chkApplyCompression.setChecked(False)
        self.txtCompression.setText('0')
        self.slideCompression.setTickPosition(QtGui.QSlider.TicksBelow)
        self.slideCompression.setProperty("value", 0)
        self.txtCompression.setEnabled(False)
        self.slideCompression.setEnabled(False)
        self.lblLevel.setEnabled(False)
#--------------------------------------------------------------------------------------------
    def handleNewCarrier2(self):
        #print('handling new carrier 2')
        self.carrier2 = Carrier(imread(self.viewCarrier2.picAddr))
        #clear viewPayload2
        clearedScene = QtGui.QGraphicsScene()
        clearedScene.clear()
        self.viewPayload2.setScene(clearedScene)
        self.viewPayload2.show()
        self.payload2 = None
        if self.carrier2.payloadExists() == False:
            self.lblCarrierEmpty.setText(QtGui.QApplication.translate("MainWindow", ">>>>Carrier Empty<<<<", None, QtGui.QApplication.UnicodeUTF8))
            self.btnExtract.setEnabled(False)
            self.btnClean.setEnabled(False)
        else:
            self.lblCarrierEmpty.setText(QtGui.QApplication.translate("MainWindow", "", None, QtGui.QApplication.UnicodeUTF8))
            self.btnExtract.setEnabled(True)
            self.btnClean.setEnabled(True)
#--------------------------------------------------------------------------------------------
    def compressionChkChanged(self):
        if self.chkApplyCompression.isChecked():
            self.txtCompression.setEnabled(True)
            self.slideCompression.setEnabled(True)
            self.lblLevel.setEnabled(True)
            self.payload1 = Payload(imread(self.viewPayload1.picAddr), self.slideCompression.value())
            self.txtPayloadSize.setText(str(len(self.payload1.json)))
        else:
            self.txtCompression.setEnabled(False)
            self.slideCompression.setEnabled(False)
            self.lblLevel.setEnabled(False)
            self.txtCompression.setText(str(self.slideCompression.value()))
            self.payload1 = Payload(imread(self.viewPayload1.picAddr))
            self.txtPayloadSize.setText(str(len(self.payload1.json)))
#--------------------------------------------------------------------------------------------
    def sliderChanged(self):
        self.txtCompression.setText(str(self.slideCompression.value()))
        self.payload1 = Payload(imread(self.viewPayload1.picAddr), self.slideCompression.value())
        self.txtPayloadSize.setText(str(len(self.payload1.json)))
        #self.txtPayloadSize.setText(str(self.calcPayloadSize(self.viewPayload1.picAddr, int(self.slideCompression.value()))))
#--------------------------------------------------------------------------------------------
    def handleSaveRequest(self):
        filePath = QFileDialog.getSaveFileName(self, caption='Please choose target')
        if not filePath:
            return
        if filePath[0][-4:] == '.png':
            whereToSave = filePath[0]
        else:
            whereToSave = filePath[0] + '.png'
        #print('going to save at ', whereToSave)
        imsave(whereToSave, self.carrier1.embedPayload(self.payload1, True))
        #print('done saving at ', whereToSave)
#--------------------------------------------------------------------------------------------
    def chkEmbedEligibility(self): #enable/disable self.btnSave accordingly
        eligible = True
        if self.carrier1 == None or self.payload1 == None:
            eligible = False  #both carrier and payload are not available
        if eligible and (len(self.payload1.json) > (self.carrier1.img.shape[0] * self.carrier1.img.shape[1])):
            eligible = False #carrier is too small
        if eligible and (self.carrier1.payloadExists() and (self.chkOverride.isChecked() == False)):
            eligible = False
        if eligible == False:
            self.btnSave.setEnabled(False)
        else:
            self.btnSave.setEnabled(True)
        return eligible
#--------------------------------------------------------------------------------------------
    def extractCarrier(self): #extracts viewCarrier2 and displays on viewPayload2
        #print('Extracting carrier')
        self.payload2 = self.carrier2.extractPayload()
        imsave('tmp.png', self.payload2.rawData)
        pixmap = QtGui.QPixmap('tmp.png')
        pixmap = pixmap.scaled(500, 500, QtCore.Qt.KeepAspectRatio)
        scene = QtGui.QGraphicsScene()
        scene.addPixmap(pixmap)
        self.viewPayload2.setScene(scene)
        self.viewPayload2.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
        #print('Done extracting carrier')
#--------------------------------------------------------------------------------------------
    def cleanCarrier(self): #saves cleaned image to viewCarrier2.picAddr
        #print('going to clean carrier')
        cleaned = self.carrier2.clean()
        imsave(self.viewCarrier2.picAddr, cleaned)
        #print('done saving cleaned file')
        #clear viewPayload2
        clearedScene = QtGui.QGraphicsScene()
        clearedScene.clear()
        self.viewPayload2.setScene(clearedScene)
        self.viewPayload2.show()
        self.payload2 = None
        self.lblCarrierEmpty.setText(QtGui.QApplication.translate("MainWindow", ">>>>Carrier Empty<<<<", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExtract.setEnabled(False)
        self.btnClean.setEnabled(False)

#============================================================================================================
if __name__ == '__main__':
    currentApp = QApplication(sys.argv)
    currentForm = Processor()

    currentForm.show()
    currentApp.exec_()
#============================================================================================================
