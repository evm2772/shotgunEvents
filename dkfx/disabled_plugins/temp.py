# import os
# import subprocess
#
# script = os.path.normpath(os.path.join(os.path.dirname(__file__), '../sh/sync_textures.sh'))
# print ('script = %s' % script)
# subprocess.call([script])


#! /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, multiprocessing, re, subprocess
# from PySide.QtGui  import *
# from PySide.QtCore import *

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


inputArgs = sys.argv[1:]
if len(inputArgs)==1:
    if re.match("^/tmp/.*\.lst$",inputArgs[0]):
        with open(inputArgs[0], "r") as filesList:
            inputArgs = filesList.readlines()



imageFormats = ["bmp","exr","gif","hdr","jpeg","jpg","png","psd","tiff","tif","tga"]


mayaInputSpaceNames = [
    'ACES2065-1',
    'ACEScg',
    'ARRI LogC',
    'camera Rec 709',
    'gamma 1.8 Rec 709',
    'gamma 2.2 Rec 709',
    'gamma 2.4 Rec 709 (video)',
    'Log film scan (ADX)',
    'Log-to-Lin (cineon)',
    'Log-to-Lin (jzp)',
    'Raw',
    'scene-linear CIE XYZ',
    'scene-linear DCI-P3',
    'scene-linear Rec 2020',
    'scene-linear Rec 709/sRGB',
    'Sony SLog2',
    'sRGB',
    ]


convertersValues = {
    "utilitesNames":[
        "arnold",
        "redshift",
        "houdini",
    ],
    "enable":[
        1,
        1,
        1,
    ],
    "utilitePath":[
        "/opt/solidangle/mtoa/2018/bin/maketx",
        "/opt/redshift/bin/redshiftTextureProcessor",
        "/opt/hfs16.5.405/bin/iconvert",
    ],
    "options":[
        " --threads 1 --opaque-detect --constant-color-detect --fixnan black --oiio --unpremult",
        "",
        "",
    ],
    "file_format":[
        "tx",
        "rs",
        "rat",
    ],
    "srgb":[
        "sRGB",
        "-s",
        "",
    ],
    "linear":[
        "linear",
        "-l",
        "",
    ],
}


def runProcess(command,conn):
    print "command",command
    # print "tg",tg
    # print "app",app

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=1)

    while True:
        output = proc.stdout.readline()
        if output == '' and proc.poll() is not None:
            # print "proc Done"
            self.statBar.showMessage("AAAAAAAAAAAA")
            QApplication.processEvents()
            # print "tg.stateProgress.value()",tg.stateProgress.value()
            # print "tg.persentVal",tg.persentVal
            # tg.stateProgress.setValue(tg.stateProgress.value()+tg.persentVal)
            # tg.updateUI("stateProgress", progressVal = tg.stateProgress.value()+tg.persentVal)
            print "Done", command.split(" ")[-1]
            # conn.send(['hello'])
            # print "((("
            conn.close()
            break
            # return "proc Done"


class FileDialog(QFileDialog):
    def __init__(self, *args):
        QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(QTreeView)

    def openClicked(self):
        inds = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()),str(i.data().toString())))
        self.selectedFiles = files
        self.done(1)

    def filesSelected(self):
        return self.selectedFiles


class mainWindow(QWidget):
    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle("Texture Converter")
        self.setMinimumWidth(900)
        self.setWindowIcon(QIcon('/prefs/scripts/tx_converter.png'))
        self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)

        # self.qsettings()

        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        self.mainLayout.setObjectName("mainLayout")
        self.mainLayout.setContentsMargins(3,3,3,0)
        self.mainLayout.setSpacing(3)
# ------------ pathWidget --------------- #
        self.pathWidget = QWidget(self)
        self.pathLayout = QHBoxLayout(self.pathWidget)
        self.pathLayout.setContentsMargins(0,0,0,0)
        self.pathLayout.setSpacing(3)

        self.pathLabel = QLabel(self)
        self.pathLabel.setText("Path String")
        self.pathLayout.addWidget(self.pathLabel)

        self.pathString = QLineEdit(self)
        # self.pathString.setText("/home/asergeev/_work/test_folder/textures/leaves_color/v01")
        self.pathString.setText("/fd" if len(inputArgs)==0 else (", ".join(inputArgs)))
        self.pathLayout.addWidget(self.pathString)

        self.pathButton = QPushButton(self)
        self.pathButton.setMaximumWidth(35)
        self.pathButton.setIcon(QIcon("/usr/share/icons/default.kde4/22x22/places/folder.png"))
        self.pathButton.clicked.connect(self.pathSelect)
        self.pathLayout.addWidget(self.pathButton)

        self.mainLayout.addWidget(self.pathWidget)
    # ------------ pathPropWidget --------------- #
        self.pathPropWidget = QWidget(self)
        self.pathPropLayout = QHBoxLayout(self.pathPropWidget)
        self.pathPropLayout.setContentsMargins(0,0,0,0)
        self.pathPropLayout.setSpacing(3)

        self.pathCheck = QCheckBox("Subfolders",self)
        self.pathCheck.setChecked(True)
        self.pathPropLayout.addWidget(self.pathCheck)
        self.pathPropLayout.addStretch(10)

        self.mainLayout.addWidget(self.pathPropWidget)

        sepPath = QFrame(self)
        sepPath.setFrameShape(QFrame.HLine)
        # sepPath.setFrameShadow(QFrame.Sunken)
        self.mainLayout.addWidget(sepPath)
# ------------ settingsWidget --------------- #
        self.settingsWidget = QWidget(self)
        self.settingsLayout = QHBoxLayout(self.settingsWidget)
        self.settingsLayout.setContentsMargins(0,0,0,0)
        self.settingsLayout.setSpacing(3)
        self.mainLayout.addWidget(self.settingsWidget)
        self.mainLayout.addStretch(10)
    # ------------ formVidget --------------- #
        self.formVidget = QWidget(self)
        self.sformLayout = QVBoxLayout(self.formVidget)
        self.sformLayout.setContentsMargins(0,0,0,0)
        self.sformLayout.setSpacing(3)
        self.settingsLayout.addWidget(self.formVidget)

        for i in range(3):
            widget = QCheckBox("*.{0} ({1})".format(convertersValues["file_format"][i],convertersValues["utilitesNames"][i]),self)
            widget.setProperty("arrCount",i)
            widget.setChecked(1 if not i else 0)
            widget.setEnabled(convertersValues["enable"][i])
            self.sformLayout.addWidget(widget)
            widget.setObjectName("_".join([convertersValues["utilitesNames"][i],"format","QCheckBox"]))

        self.sformLayout.addStretch(10)

        sepForm = QFrame(self)
        sepForm.setFrameShape(QFrame.VLine)
        sepForm.setFrameShadow(QFrame.Sunken)
        self.settingsLayout.addWidget(sepForm)
    # ------------ attrVidget --------------- #
        self.attrVidget = QWidget(self)
        self.attrLayout = QVBoxLayout(self.attrVidget)
        self.attrLayout.setContentsMargins(0,0,0,0)
        self.attrLayout.setSpacing(3)

        self.filterTypesCheck = QCheckBox("Filter Inputs Types",self)
        self.filterTypesCheck.setChecked(False)
        self.filterTypesCheck.clicked.connect(lambda:self.updateUI("filterTypesCheck"))
        self.attrLayout.addWidget(self.filterTypesCheck)

        self.filterTypesString = QLineEdit(self)
        self.filterTypesString.setText("")
        self.filterTypesString.setToolTip("""Type need formats separated with comma (,)
If first symbol minus, formats are excluded
Examples:
  Only .tif:   'tif,tiff'
  All except for .png and .jpg:   '-png,jpg'
Supported formats: """+str(imageFormats))

        self.filterTypesString.setEnabled(False)
        self.attrLayout.addWidget(self.filterTypesString)

        filterTypesForm = QFrame(self)
        filterTypesForm.setFrameShape(QFrame.HLine)
        filterTypesForm.setFrameShadow(QFrame.Sunken)
        self.attrLayout.addWidget(filterTypesForm)

        self.settingsLayout.addWidget(self.attrVidget)
        # ------------ colorProfWidget --------------- #
        self.colorProfWidget = QWidget(self)
        self.colorProfLayout = QHBoxLayout(self.colorProfWidget)
        self.colorProfLayout.setContentsMargins(0,0,0,0)
        self.colorProfLayout.setSpacing(3)

        difLable = QLabel(self)
        difLable.setText("_color")
        self.colorProfLayout.addWidget(difLable)
        self.difCombo = QComboBox(self)
        self.difCombo.addItems(["srgb","linear",])
        self.difCombo.setCurrentIndex(0)
        self.colorProfLayout.addWidget(self.difCombo)
        otherLable = QLabel(self)
        otherLable.setText("other")
        self.colorProfLayout.addWidget(otherLable)
        self.otherCombo = QComboBox(self)
        self.otherCombo.addItems(["srgb","linear",])
        self.otherCombo.setCurrentIndex(1)
        self.colorProfLayout.addWidget(self.otherCombo)
        self.acesCheck = QCheckBox("ACEScg",self)
        self.acesCheck.setChecked(True)
        self.colorProfLayout.addWidget(self.acesCheck)
        self.colorProfLayout.addStretch(10)
        self.replaceExists = QCheckBox("Replace Exists",self)
        self.replaceExists.setChecked(True)
        self.colorProfLayout.addWidget(self.replaceExists)

        self.attrLayout.addWidget(self.colorProfWidget)
        # ------------ resizesWidget --------------- #
        self.resizesWidget = QWidget(self)
        self.resizesLayout = QHBoxLayout(self.resizesWidget)
        self.resizesLayout.setContentsMargins(0,0,0,0)
        self.resizesLayout.setSpacing(3)

        self.origCheck = QCheckBox("Original size",self)
        self.origCheck.setChecked(True)
        self.origCheck.setProperty("postfix","")
        self.origCheck.setObjectName("origCheck_resize_QCheckBox")
        self.resizesLayout.addWidget(self.origCheck)
        sepSizes = QFrame(self)
        sepSizes.setFrameShape(QFrame.VLine)
        sepSizes.setFrameShadow(QFrame.Sunken)
        self.resizesLayout.addWidget(sepSizes)
        resizesLable = QLabel(self)
        resizesLable.setText("Resize to:")
        self.resizesLayout.addWidget(resizesLable)
        for chName in ["0.5 K","1 K","2 K","4 K",]:
            widget = QCheckBox(chName,self)
            widget.setChecked(False)
            widget.setProperty("postfix","_{0}{1}".format(chName[:1],chName[-1:].lower(),))
            widget.setObjectName("_".join(["{0}{1}".format(chName[:1],(chName[-1:].lower())),"resize","QCheckBox"]))
            self.resizesLayout.addWidget(widget)

        self.resizesLayout.addStretch(10)

        self.attrLayout.addWidget(self.resizesWidget)

        # ------------ applyWidget --------------- #
        self.applyWidget = QWidget(self)
        self.applyLayout = QHBoxLayout(self.applyWidget)
        self.applyLayout.setContentsMargins(0,0,0,0)
        self.applyLayout.setSpacing(3)

        self.stateProgress = QProgressBar(self)
        self.stateProgress.setMaximumHeight(15)
        self.stateProgress.setValue(0)
        self.applyLayout.addWidget(self.stateProgress)

        self.applyButton = QPushButton("Convert",self)
        self.applyButton.clicked.connect(self.textures_collector)
        self.applyLayout.addWidget(self.applyButton)
        ###############################
        # self.testButton = QPushButton("->",self)
        # self.testButton.clicked.connect(self.test_command)
        # self.testButton.setMaximumWidth(25)
        # self.applyLayout.addWidget(self.testButton)

        self.attrLayout.addWidget(self.applyWidget)


        self.statBar = QStatusBar(self)
        self.statBar.setSizeGripEnabled(0)
        self.mainLayout.addWidget(self.statBar)
        self.statBar.showMessage("Hello!",6000)

        self.persentVal = 0


    def updateUI(self, *args, **kwargs):
        print "updateUI",args,kwargs
        if "filterTypesCheck" in args:
            self.filterTypesString.setEnabled(self.filterTypesCheck.checkState())
        elif "stateProgress" in args:
            self.stateProgress.setValue(kwargs["progressVal"])
        elif "statBar" in args:
            self.statBar.showMessage(kwargs["text"])

    def pathSelect(self):
        pathUI = self.pathString.text().split(", ")[-1]
        pathFolder = FileDialog(self,'Open folder',pathUI)

        if pathFolder.exec_():
            listFiles = list(pathFolder.filesSelected())
            print "listFiles",listFiles
            self.pathString.setText(", ".join(listFiles))


    def textures_collector(self):
        if self.filterTypesCheck.isChecked():
            exclude = 0
            text = self.filterTypesString.text().replace(" ","")
            if text:
                if text[0]=="-":
                    text = text[1:]
                    exclude = 1
            filterFormats = str(text).split(",")
            if not exclude:
                localImageFormats = list(set(imageFormats) & set(filterFormats))
            else:
                localImageFormats = list(set(imageFormats) - set(filterFormats))
        else:
            localImageFormats = imageFormats

        pathUI = str(self.pathString.text()).split(", ")

        origImagesSet = set()

        def filter_file_type(link):
            # print "filter_file_type(link)",link
            formatImage = link.split(".")[-1].lower()
            if formatImage in localImageFormats:
                if link not in origImagesSet:
                    origImagesSet.add(link)

        def pars_folders(link):
            for (dirpath, dirnames, filenames) in os.walk(link):
                if self.pathCheck.checkState() == 0:
                    break
                # print dirnames, filenames
                for path in [os.path.join(dirpath,i) for i in filenames]:
                    filter_file_type(path)

        for link in pathUI:
            if os.path.isfile(link):
                filter_file_type(link)
            else:
                pars_folders(link)

        # print "origImagesSet",origImagesSet

        resizeCommands = []
        convertCommands = []

        def generate_string(inputPath,fileFormatNum,resize):
            # print "generate_string inputs: ",inputPath,fileFormatNum,resize

            inFolder,inName = inputPath.rsplit("/",1)

            tiles={"_0k":512,
                    "_1k":1024,
                    "_2k":2048,
                    "_4k":4096}

            if resize != "":
                outName = inName[:inName.find(".")]+resize+inName[inName.find("."):].rsplit(".",1)[0]+".tif"

                resizeCommands.append("ffmpeg -i %s -vf scale=%i:-1 -y %s" % (inputPath,tiles[resize],os.path.join(inFolder,outName)))
            else:
                outName = inName
            # maketx -v -u --oiio --checknan --filter lanczos3 path/to/fileIn.tif -o path/to/fileOut.tx
            # iconvert [-d depth] [-n informat] [-t outformat] [-g (off|auto)] [-L <lut>] [-O <lut>] infile outfile [tag tagvalue]

            output_colorSpace = convertersValues[str(self.difCombo.currentText())][fileFormatNum] if "_color" in inName else convertersValues[str(self.otherCombo.currentText())][fileFormatNum]

            # print "output_colorSpace",output_colorSpace
            # print "output",os.path.join(inFolder,".".join([outName.rsplit(".")[0],convertersValues["file_format"][fileFormatNum]]))
            # print outName

            if fileFormatNum == 0:
                finalString = "{util} {opts} --colorconvert {colorConv} {colorRange} {input} -o {output}".format(
                                    util = convertersValues["utilitePath"][fileFormatNum],
                                    colorRange = "ACEScg" if self.acesCheck.isChecked() else "sRGB",
                                    opts = convertersValues["options"][fileFormatNum],
                                    colorConv = output_colorSpace,
                                    input = os.path.join(inFolder,outName),
                                    output = os.path.join(inFolder,".".join([outName.rsplit(".",1)[0],convertersValues["file_format"][fileFormatNum]]))
                )
                convertCommands.append(finalString)
            elif fileFormatNum == 1:
                pass
            elif fileFormatNum == 2:
                finalString = "{util} {input} {output}".format(
                                    util = convertersValues["utilitePath"][fileFormatNum],
                                    input = os.path.join(inFolder,outName),
                                    output = os.path.join(inFolder,".".join([outName.rsplit(".",1)[0],convertersValues["file_format"][fileFormatNum]]))
                )
                convertCommands.append(finalString)

            # print "\tfinalString",finalString


        typesCheckers = self.findChildren(QCheckBox,QRegExp("format_QCheckBox"))
        for typeCheck in typesCheckers:
            if typeCheck.isChecked():
                fileFormatNum = typeCheck.property("arrCount").toInt()[0]
                sizeCheckers = self.findChildren(QCheckBox,QRegExp("resize_QCheckBox"))
                for sizeChecker in sizeCheckers:
                    if sizeChecker.isChecked():
                        resize = str(sizeChecker.property("postfix").toString())
                        for inputPath in origImagesSet:
                            generate_string(inputPath,fileFormatNum,resize)


        resizeCommands=list(set(resizeCommands))
        convertCommands=list(set(convertCommands))

        doneResize = 0
        doneConvert = 0
        # child_processes = []
        # allProcCount = 0

        # print "resizeCommands:",resizeCommands
        # print "convertCommands:",convertCommands

        self.persentVal = 100.0/(len(convertCommands)+len(resizeCommands))
        # print persentVal
        # progressBar = 0

        self.updateUI("statBar",text="Resize {0} textures ({1} done), convert {2} textures ({3} done)".format(len(resizeCommands),doneResize,len(convertCommands),doneConvert))

        # pool = multiprocessing.Pool()


        # if len(resizeCommands)>0:
        #     for resizeCommand in resizeCommands:
                # progressBar+=persentVal
                # self.updateUI("stateProgress", progressVal = progressBar)
                # if runProcess(resizeCommand):
                #     doneResize+=1
                #     self.updateUI("statBar",text="Resize {0} textures ({1} done), convert {2} textures ({3} done)".format(len(resizeCommands),doneResize,len(convertCommands),doneConvert))


        if len(convertCommands)>0:

            for convertCommand in convertCommands:
                # print "convertCommand",convertCommand,type(convertCommand)
                # progressBar+=persentVal
                # self.updateUI("stateProgress", progressVal = progressBar)

                # print "self",self
                # print "tg",tg
                # print "app",app
                parent_conn, child_conn = multiprocessing.Pipe()

                result = multiprocessing.Process(target=runProcess, args=(convertCommand,child_conn,))
                result.start()
                # print parent_conn.recv(),"printed"
                # result.join()

                # result = pool.apply_async(oneProc, args=(tg,))
                # result = pool.apply(self.runProcess, (convertCommand,))
                # result = pool.apply_async(self.runProcess, (convertCommand,))

                # if result.get() == "proc Done":
                    # print "YES!"

                # pool.apply(command, (convertCommand,))
                # pool.close()
                # pool.join()

                # pool.apply(runProcess, [convertCommand])
                # pool.apply_async(runProcess, args=(i,))
                # p = multiprocessing.Process(target=runProcess, args=(convertCommand,))
                # p.start()



                # if runProcess(convertCommand):
                #     doneConvert+=1
                #     self.updateUI("statBar",text="Resize {0} textures ({1} done), convert {2} textures ({3} done)".format(len(resizeCommands),doneResize,len(convertCommands),doneConvert))

    # def runProcess(self,command,conn):
    #     print "command",command
    #     proc = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=1)

    #     while True:
    #         output = proc.stdout.readline()
    #         if output == '' and proc.poll() is not None:
    #             # self.updateUI("stateProgress", progressVal = self.stateProgress.value()+self.persentVal)
    #             conn.send(['hello'])
    # # conn.close()
    #             break
    #             # return "proc Done"
    #             # return True

    def test_command(self):
        print "test button"


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tg = mainWindow()
    tg.show()
    # tg.pathString.setText("/home/asergeev/_work/test_folder/textures/leaves_color/v01/leaves_color.1001.tif")
    # tg.pathString.setText("/home/asergeev/_work/test_folder/textures/branches_color/v01")
    tg.pathString.setText("/home/asergeev/_work/test_folder/textures/leaves_color/v01/leaves_color.1001.tif, /home/asergeev/_work/test_folder/textures/leaves_color/v01/leaves_diffuse.1001.tif")
    # tg.pathString.setText(", ".join(["/home/asergeev/_work/test_folder/textures/leaves_color/v01",
    #                                 "/home/asergeev/_work/test_folder/textures/branches_color/v01/vprchecker.png",
    #                                 "/home/asergeev/_work/test_folder/textures/branches_color/v01/arc_big_disp_16.1001.tif",
    #                                 "/home/asergeev/_work/test_folder/textures/leaves_opacity"]))
    app.exec_()
