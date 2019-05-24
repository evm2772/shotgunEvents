import maya.cmds as cmds
import maya.utils as utils
import maya.mel
import os.path
import glob
import re
import sys, os
import subprocess
import threading
import makeTx
import platform
import mtoa.utils as mutils
from arnold import *

from mtoa import core
import os
import fnmatch

from pprint import pformat, pprint
import re


def textures_parser(root_folder):
    masks = ["*.bmp", "*.exr", "*.gif", "*.hdri", "*.jpeg", "*.jpg", "*.png", "*.psd", "*.tiff", "*.tif", "*.tga"]
    includes = '|'.join([fnmatch.translate(x) for x in masks])
    texture_paths = []
    for (dirpath, dirnames, filenames) in os.walk(root_folder):
        #if dirnames:
        if filenames and re.match(r'.*v\d\d', dirpath):
            print dirpath, dirnames, filenames
            files = [f for f in filenames if re.match(includes, f)]
            for f in files:
                texture_paths.append(os.path.join(dirpath, f))
    print('Files for sync: \n %s' % pformat(texture_paths))
    return texture_paths



def textures_parserOLD(root_folder):
    masks = ["*.bmp", "*.exr", "*.gif", "*.hdri", "*.jpeg", "*.jpg", "*.png", "*.psd", "*.tiff", "*.tif", "*.tga"]
    includes = '|'.join([fnmatch.translate(x) for x in masks])
    #print includes
    texture_paths = []
    for (dirpath, dirnames, filenames) in os.walk(root_folder):
        if dirnames:
            # find versions:
            version_dirs = [d for d in dirnames if re.match(r'v\d\d', d)]
            if version_dirs:
                version_dirs.sort() # for any case ;-)
                last_version_dir = os.path.join(dirpath, version_dirs[-1])
                print('Last version dir: {0} --> {1}'.format(version_dirs, last_version_dir))
                for (dirpath, dirnames, filenames) in os.walk(last_version_dir):
                    files = [f for f in filenames if re.match(includes, f)]
                    print ('Found files: %s' % str(files))
                    for f in files:
                        texture_paths.append(os.path.join(last_version_dir, f))

    print('Files for sync: \n %s' % pformat(texture_paths))
    return texture_paths


#import mtoa.ui.arnoldmenu;mtoa.ui.arnoldmenu.arnoldTxManager()
# then here
# def arnoldTxManager():
#     core.createOptions()
#     win = mtoa.txManager.MtoATxManager()
#     win.create()
#     win.refreshList()

# Using:
# import pymel.core as pm
#
# pm.loadPlugin('mtoa')
#
# import traceback
#
# try:
#     from mtoa import txManager_rnd as txm
#
#     reload(txm)
#     txm.do()
#
# except Exception as ex:
#     print traceback.format_exc()



def do(textures_dir):
    core.createOptions()
    man = MtoATxManager()
    #man.create()
    man.selectedFilesFromFolder(textures_dir)
    man.createTx()
    print 'finished'
    #win.refreshList()


def isImage(file):
    ext = os.path.splitext(file)[1]
    if (ext == '.jpeg' or ext == '.jpg' or ext == '.tiff' or ext == '.tif' or
        ext == '.png' or ext == '.exr' or ext == '.hdr' or ext == '.bmp' or
        ext == '.tga'):
        return True
    return False

# def updateProgressMessage(window, created, toCreate, errors):
#     ctrlPath = '|'.join([window, 'groupBox_2', 'label_8']);
#     cmds.text(ctrlPath, edit=True, label="Created: {0} of {1}".format(created,toCreate));
#     if errors is not 0:
#         ctrlPath = '|'.join([window, 'groupBox_2', 'label_9']);
#         cmds.text(ctrlPath, edit=True, label="Warning: {0} errors".format(errors));
#     else:
#         ctrlPath = '|'.join([window, 'groupBox_2', 'label_9']);
#         cmds.text(ctrlPath, edit=True, label="");

class MakeTxThread (threading.Thread):
    def __init__(self,manager):
        self.txManager = manager
        threading.Thread.__init__(self)
        self.filesCreated = 0
        self.createdErrors = 0

    def run (self):
        self.filesCreated = 0
        self.createdErrors = 0
        self.createTx()
        self.txManager.thread = []

    # create a .tx file with the provided options. It will wait until it is finished
    def runMakeTx(self, texture, space):

        ctrlPath = '|'.join([self.txManager.window, 'groupBox_2', 'lineEdit']);
        arg_options = utils.executeInMainThreadWithResult(cmds.textField, ctrlPath, query=True, text=True)
        status = utils.executeInMainThreadWithResult( makeTx.makeTx, texture, colorspace=space, arguments=arg_options)
        return status

    def createTx(self):
        if not self.txManager.selectedItems:
            return

        #ctrlPath = '|'.join([self.txManager.window, 'groupBox_2', 'pushButton_7'])
        #utils.executeDeferred(cmds.button,ctrlPath, edit=True, enable=True)
        maya_version = mutils.getMayaVersion()

        # first we need to make sure the options & color manager node were converted to arnold
        arnoldUniverseActive = AiUniverseIsActive()

        if not arnoldUniverseActive:
            cmds.arnoldScene(mode='create')

        render_colorspace = cmds.colorManagementPrefs(query=True, renderingSpaceName=True)

        cmEnable = cmds.colorManagementPrefs(query=True, cmEnabled=True)

        textureList = []

        #ctrlPath = '|'.join([self.txManager.window, 'groupBox_2', 'lineEdit']);
        #arg_options = utils.executeInMainThreadWithResult(cmds.textField, ctrlPath, query=True, text=True)
        arg_options = u'-v -u --unpremult --oiio'
        for textureLine in self.txManager.selectedItems:
            texture = textureLine[0]
            print texture

            # we could use textureLine[2] for the colorSpace
            # but in case it hasn't been updated correctly
            # it's still better to ask maya again what is the color space
            nodes = textureLine[3]

            colorSpace = 'Raw'
            dir_name = texture.split(os.sep)[-3]
            if 'color' in dir_name.split('_'):
                colorSpace = 'sRGB'


            #conflictSpace = False

            # color spaces didn't exist in versions < 2016
            # if maya_version >= 2016:
            #     for node in nodes:
            #         nodeColorSpace = cmds.getAttr(node+'.colorSpace')
            #         if colorSpace != 'auto' and colorSpace != nodeColorSpace:
            #             conflictSpace=True
            #
            #         colorSpace = nodeColorSpace
            #
            #     if colorSpace == 'auto' and textureLine[2] != '':
            #         colorSpace = textureLine[2]
            #
            # if not texture:
            #     continue;
            # # stopCreation has been called
            # if not self.txManager.process:
            #     break
            #
            # # if a conflict is found, pop-up a dialog
            # if conflictSpace:
            #     msg = os.path.basename(texture)
            #     msg += '\n'
            #     msg += 'has conflicting Color Spaces.\n'
            #     msg += 'Use ('
            #     msg += colorSpace
            #     msg += ') ?'
            #
            #     result = cmds.confirmDialog(
            #         title='Conflicting Color Spaces',
            #         message=msg,
            #         button=['OK', 'Cancel'],
            #         defaultButton='OK',
            #         cancelButton='Cancel',
            #         dismissString='Cancel')
            #
            #     if result == 'Cancel':
            #         break


            # Process all the files that were found previously for this texture (eventually multiple tokens)
            for inputFile in textureLine[4]:

                txArguments = arg_options

                if cmEnable == True and colorSpace != render_colorspace:
                    txArguments += ' --colorconvert "'
                    txArguments += colorSpace
                    txArguments += '" "'
                    txArguments += render_colorspace
                    txArguments += '"'

                # need to invalidate the TX texture from the cache
                outputTx = os.path.splitext(inputFile)[0] + '.tx'
                AiTextureInvalidate(outputTx)

                textureList.append([inputFile, txArguments])

        print '\n\n === textureList = %s' % textureList
        self.txManager.filesToCreate = len(textureList)

        # Now I have a list of textures to be converted
        # let's give  this list to arnold
        for textureToConvert in textureList:
            AiMakeTx(textureToConvert[0], textureToConvert[1])

        status = POINTER(AtMakeTxStatus)()
        print 'status = %s' % status
        source_files = POINTER(AtPythonString)()

        print 'source_files = %s' % source_files
        num_submitted = c_uint()
        num_jobs_left = 1   # default to arbitrary value > 0

        self.createdErrors = 0
        self.filesCreated = 0

        while (num_jobs_left > 0):
            if not self.txManager.process:
                 # stopCreation has been called
                break

            num_jobs_left = AiMakeTxWaitJob(byref(status), byref(source_files), byref(num_submitted))

        if (num_submitted.value > len(textureList)):
            AiMsgFatal("There are more submitted textures than there are textures! "
                      "Queue should have been cleared!")

        for i in range(0, num_submitted.value):

            if (status[i] == AiTxUpdated):
                self.filesCreated += 1
                AiMsgInfo("[mtoa.tx] %d: %s was updated", i, source_files[i])
                print("[mtoa.tx] %d: %s was updated", i, source_files[i])
            elif (status[i] == AiTxError):
                self.createdErrors += 1
                AiMsgWarning("[mtoa.tx] %d: %s could not be updated", i, source_files[i])
                print("[mtoa.tx] %d: %s could not be updated", i, source_files[i])


            # need to invalidate the TX texture from the cache
            outputTx = os.path.splitext(source_files[i])[0] + '.tx'
            if outputTx[0] == '"':
                outputTx = outputTx[1:]

            AiTextureInvalidate(outputTx)

        #utils.executeDeferred(updateProgressMessage, self.txManager.window, self.filesCreated, self.txManager.filesToCreate, self.createdErrors)

        #ctrlPath = '|'.join([self.txManager.window, 'groupBox_2', 'pushButton_7']);
        #utils.executeDeferred(cmds.button, ctrlPath, edit=True, enable=False);

        self.txManager.process = True
        utils.executeDeferred(self.txManager.updateList)

        # an arnold scene was created above, let's delete it now
        if not arnoldUniverseActive:
            cmds.arnoldScene(mode="destroy")
        from shared.utils.file_utils import need_update
        import shutil
        for f in [item[0] for item in textureList]:
            basename = os.path.splitext(f)[0]
            print '-'*200
            tx_src = '%s.tx' % os.path.splitext(f)[0]
            #tx_dst = os.path.join(os.environ.get('PANASAS_TEXTURES_DIR'), os.path.basename(tx_src))

            tx_dst = tx_src.replace(os.environ.get('STORAGE_TEXTURES_DIR'), os.environ.get('PANASAS_TEXTURES_DIR'))
            #remove version folder:
            #tx_dst = re.sub(r'/v\d\d/', '/', tx_dst)
            # if tx_dst == tx_src:
            #     raise Exception('Inorect source location: %s' % tx_src)
            print 'SRC:  %s' % tx_src
            print 'DST:  %s' % tx_dst
            update = need_update(tx_src, tx_dst)
            print 'need_update: %s' % update
            # directories must exists - checked in daemon plugin!
            dir_dst = os.path.dirname(tx_dst)
            if not os.path.isdir(dir_dst):
                print ('"Panasas" textures directory is not found. Creating: %s' % dir_dst)
                os.makedirs(dir_dst)
                print ('"Panasas" textures directory was created:  %s' % dir_dst)

            if update:
                dst_dir = os.path.dirname(tx_dst)
                if not os.path.isdir(dst_dir):
                    print ('Creating: %s' % dst_dir)
                    os.makedirs(dst_dir)
                    print('directory was created:  %s' % dst_dir)
                shutil.copyfile(tx_src, tx_dst)
                print 'Updated: %s -> %s' % (tx_src, tx_dst)
            else:
                print 'Not updated: %s -> %s\n\n' % (tx_src, tx_dst)



def GetTxList(txItems, filesCount):

    texturesList = []
    colorSpaces = []
    nodes = []

    list = cmds.ls(type='file')
    for node in list:
        texture = ''
        # regarding tiling, porting the code from CFileTranslator
        tilingMode = int(float(cmds.getAttr(node+'.uvTilingMode')))
        if tilingMode == 0:
            texture = cmds.getAttr(node+'.fileTextureName')
        else:
            # in CfileTranslator we first check fileTextureNamePattern, then
            # if it's empty we check computedFileTextureNamePattern
            # not sure why...
            texture = cmds.getAttr(node+'.fileTextureNamePattern')
            if not texture:
                texture = cmds.getAttr(node+'.computedFileTextureNamePattern')
        if texture:
            texturesList.append(texture)
            colorSpace = cmds.getAttr(node+'.colorSpace')
            colorSpaces.append(colorSpace)
            nodes.append(node)

    list = cmds.ls(type='aiImage')
    for node in list:
        texture = cmds.getAttr(node+'.filename')
        if texture:
            texturesList.append(texture)
            colorSpace = cmds.getAttr(node+'.colorSpace')
            colorSpaces.append(colorSpace)
            nodes.append(node)

    list = cmds.ls(type='imagePlane')
    for node in list:
        texture = cmds.getAttr(node+'.imageName')
        if texture:
            texturesList.append(texture)
            colorSpace = cmds.getAttr(node+'.colorSpace')
            colorSpaces.append(colorSpace)
            nodes.append(node)

    textureSearchPaths = cmds.getAttr('defaultArnoldRenderOptions.texture_searchpath')
    searchPaths = []

    if platform.system().lower() == 'windows':
        searchPaths = textureSearchPaths.split(';')
    else:
        searchPaths = textureSearchPaths.split(':')

    for i in range(len(texturesList)):

        inputFiles = makeTx.expandFilename(texturesList[i])

        if len(inputFiles) == 0:
            # file not found, need to search in the Texture Search Paths
            for searchPath in searchPaths:
                if searchPath.endswith('/'):
                    currentSearchTexture = searchPath + texturesList[i]
                else:
                    currentSearchTexture = searchPath + '/'+texturesList[i]

                inputFiles = makeTx.expandFilename(currentSearchTexture)
                if len(inputFiles) > 0:
                    break

        filesCount[0] += len(inputFiles)

        txFlag = 0

        if len(inputFiles) == 0:
            # missing input file
            txFlag = -1
            filesCount[1] += 1
        else:
            ext = os.path.splitext(texturesList[i])[1]
            # A .tx texture
            if(ext == '.tx'):
                txFlag = 0
            else:
                # Not a .tx texture
                # loop over files since we need to make sure each expanded texture has its .tx version
                txFlag = 1
                for inputFile in inputFiles:
                    # note that inputFile is already expanded here
                    outputTx = os.path.splitext(inputFile)[0]+'.tx'
                    outputTxFiles = makeTx.expandFilename(outputTx)

                    if len(outputTxFiles) == 0:
                        # un-processed File
                        txFlag = 2
                        break

        nodesList = [nodes[i]]
        baseFilename = os.path.basename(texturesList[i])


        txItems.append([texturesList[i], txFlag, colorSpaces[i], nodesList, inputFiles, baseFilename])





class MtoATxManager(object):
    use=None;
    def __init__(self):
        MtoATxManager.use = self;
        path = os.path.dirname(os.path.abspath(__file__))
        self.uiFile = os.path.join(path,'txManager.ui');
        self.window = '';
        self.txItems = []   # arrays [texture_name, status, colorSpace, nodeList, inputFiles]
                            # where status is:
                            #   -1 (does not exists),
                            #    0 (.tx file),
                            #    1 (has a processed .tx file),
                            #    2 (does not have a processed .tx file)
        self.listElements = []
        self.selectedItems = []
        self.filesToCreate = 0

        self.filesCreated = 0
        self.createdErrors = 0
        self.deletedFiles = 0
        self.totalFiles = 0
        self.missingFiles = 0

        self.thread = []
        self.process = True
        self.showFullPaths = False
        self.lineIndex = {}

    def create(self):
        print 'UI skipped'
        return
        # if cmds.window(self.window, exists=True):
        #     cmds.deleteUI(self.window);
        # self.window = cmds.loadUI(uiFile=self.uiFile, verbose=False)
        #
        # cmds.showWindow(self.window);
        # try:
        #     initPos = cmds.windowPref( self.window, query=True, topLeftCorner=True )
        #     if initPos[0] < 0:
        #         initPos[0] = 0
        #     if initPos[1] < 0:
        #         initPos[1] = 0
        #     cmds.windowPref( self.window, edit=True, topLeftCorner=initPos )
        # except :
        #     pass
        #
        # ctrlPath = '|'.join([self.window, 'radioButton']);
        # cmds.radioButton(ctrlPath, edit=True, select=True);
        #
        # ctrlPath = '|'.join([self.window, 'groupBox_4']);
        # cmds.control(ctrlPath, edit=True, enable=False);
        #
        # ctrlPath = '|'.join([self.window, 'groupBox_2', 'pushButton_7']);
        # cmds.button(ctrlPath, edit=True, enable=False);
        #
        # ctrlPath = '|'.join([self.window, 'groupBox_2', 'lineEdit']);
        # cmds.textField(ctrlPath, edit=True, text="-v -u --unpremult --oiio");

    def displayList(self):
        #ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);

        #listSize = cmds.textScrollList(ctrlPath, query=True, numberOfItems=True);
        # for x in range(listSize,0,-1):
        #     cmds.textScrollList(ctrlPath, edit=True, removeIndexedItem=x);

        self.lineIndex = {}

        txIndex = 0

        for txItem in self.txItems:

            texturePrefix = ''

            if(txItem[1] == 0):
                texturePrefix = '[tx] '
            elif(txItem[1] == 1):
                texturePrefix = '(tx) '
            elif(txItem[1] == 2):
                texturePrefix = '       '
            elif(txItem[1] == -1):
                texturePrefix = '~~  '

            textureSuffix = ''
            maya_version = mutils.getMayaVersion()
            if maya_version >= 2016:
                textureSuffix =' ('+txItem[2]+')'


            if self.showFullPaths:
                textureLine = texturePrefix+txItem[0]+textureSuffix
                if textureLine not in self.lineIndex:
                    #cmds.textScrollList(ctrlPath, edit=True, append=[textureLine]);
                    self.lineIndex[textureLine] = txIndex

                else:
                    prevIndex = self.lineIndex[textureLine]
                    if prevIndex < len(self.txItems):
                        self.txItems[prevIndex][3].append(txItem[3][0])

            else:
                #partial paths
                textureLine = texturePrefix+txItem[5]+textureSuffix
                foundFullName = False

                while textureLine in self.lineIndex:
                    #basename already found, let's check the full names
                    prevIndex = self.lineIndex[textureLine]
                    if prevIndex < len(self.txItems):
                        if txItem[0] == self.txItems[prevIndex][0]:
                            # same fullname, just append the list of nodes
                            self.txItems[prevIndex][3].append(txItem[3][0])
                            foundFullName = True
                            break

                    textureLine = textureLine + ' '

                if not foundFullName:
                    # this fullname wasn't found yet, need to add it
                    #cmds.textScrollList(ctrlPath, edit=True, append=[textureLine]);
                    self.lineIndex[textureLine] = txIndex


            txIndex = txIndex+1


        #self.listElements = cmds.textScrollList(ctrlPath, query=True, ai=True);

        #ctrlPath = '|'.join([self.window, 'groupBox', 'label_5']);
        #cmds.text(ctrlPath, edit=True, label="Total Files: {0}".format(self.totalFiles));

        #ctrlPath = '|'.join([self.window, 'groupBox', 'label_6']);
        # if(self.missingFiles > 0):
        #     cmds.text(ctrlPath, edit=True, label="<font color=#FE6565>Missing Files: {0}</font>".format(self.missingFiles));
        # else:
        #     cmds.text(ctrlPath, edit=True, label="");

    # Update the Scroll List with the texture files in the scene and check its status
    def updateList(self):

        self.txItems = []
        filesCount = []
        #total files
        filesCount.append(0)
        #missing files
        filesCount.append(0)

        GetTxList(self.txItems, filesCount)
        self.totalFiles = filesCount[0]
        self.missingFiles = filesCount[1]

        self.displayList()


    def stopCreation(self, *args):
        self.process = False

    #Updates the Scroll List and also the process progress message
    #Only to be used when a refresh button is pressed, as it will remove any progress information shown
    def refreshList(self, *args):
        self.updateList()

        #Only update this text when button is pressed, not when called from createTx or deleteTx
        #updateProgressMessage(self.window, 0, 0, 0)
        #ctrlPath = '|'.join([self.window, 'groupBox_3', 'label_10']);
        #cmds.text(ctrlPath, edit=True, label="");

    # def selectAll(self, *args):
    #     self.updateList()
    #     if self.listElements:
    #         all_idx = [i+1 for i, texture in enumerate(self.listElements) if texture.startswith('       ') or texture.startswith('(tx) ')]
    #         ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);
    #         cmds.textScrollList(ctrlPath, edit=True, deselectAll=True);
    #         cmds.textScrollList(ctrlPath, edit=True, selectIndexedItem=all_idx);
    #
    #         self.selectedFilesFromList()

    # Select all textures that does not have a processed .tx file
    def selectNonTx(self, *args):
        self.updateList()
        if self.listElements:
            all_idx = [i+1 for i, texture in enumerate(self.listElements) if texture.startswith('       ')]
            ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);
            cmds.textScrollList(ctrlPath, edit=True, deselectAll=True);
            cmds.textScrollList(ctrlPath, edit=True, selectIndexedItem=all_idx);

            self.selectedFilesFromList()

    def selectChange(self, *args):
        self.selectedFilesFromList()

    def selectLine(self, *args):
        ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);

        selectedList = cmds.textScrollList(ctrlPath, query=True, si=True);

        lineText = selectedList[0];
        lineIndex = self.lineIndex[lineText]

        if lineIndex >= len(self.txItems):
            return

        selectedItem = self.txItems[lineIndex]
        nodes = selectedItem[3]

        cmds.select(clear=True)

        print (selectedItem[0] + '('+selectedItem[2]+')')
        print 'Used by file node(s) : '

        for node in nodes:
            if node:
                print ('  '+node)
                cmds.select(node, add=True)


    # Set the variables self.selectedItems, self.filesToCreate, self.filesCreated and self.createdErrors
    #  from the Scroll List selection
    def selectedFilesFromList(self):

        ctrlPath = '|'.join([self.window, 'groupBox', 'listWidget']);
        selectedLines = cmds.textScrollList(ctrlPath, query=True, si=True);
        selectedLinesIdx = cmds.textScrollList(ctrlPath, query=True, sii=True);

        self.filesToCreate = 0
        self.filesCreated = 0
        self.createdErrors = 0
        self.selectedItems = []

        if not selectedLines:
            #updateProgressMessage(self.window, 0, 0, 0)
            return

        list = cmds.textScrollList(ctrlPath, query=True, ai=True);
        lineIndex = 0

        for i in range(len(selectedLines)):
            lineText = selectedLines[i]

            #if python allows a better way to do this (find the index of this element), please get rid of this hash
            lineIndex = self.lineIndex[lineText]

            # all my information is in self.txItems[lineIndex]
            if lineIndex >= len(self.txItems):
                # shouldn't happen !
                continue

            self.selectedItems.append(self.txItems[lineIndex])
            texture = self.selectedItems[i][0]

            self.filesToCreate += len(self.selectedItems[i][4])

        #updateProgressMessage(self.window, self.filesCreated, self.filesToCreate, 0)
        ctrlPath = '|'.join([self.window, 'groupBox_3', 'label_10']);
        cmds.text(ctrlPath, edit=True, label="");

    # Set the variables self.selectedItems, self.filesToCreate, self.filesCreated and self.createdErrors
    #  from the Folder selected
    def selectedFilesFromFolder(self, folder):
        #ctrlPath = '|'.join([self.window, 'groupBox_4', 'lineEdit_2']);
        #folder = cmds.textField(ctrlPath, query=True, text=True);
        print 'selectedFilesFromFolder: folder = ', folder

        self.selectedItems = []
        self.filesToCreate = 0
        self.filesCreated = 0
        self.createdErrors = 0

        #ctrlPath = '|'.join([self.window, 'groupBox_4', 'checkBox']);
        #recursive = cmds.checkBox(ctrlPath, query=True, value=True);
        files = textures_parser(folder)
        maya_version = mutils.getMayaVersion()
        self.selectedItems = []
        # if os.path.isdir(folder):
        #     if recursive:
        #         for root, dirs, files in os.walk(folder):
        #             for texture in files:
        #                 if (isImage(texture)):
        #                     inputFile = os.path.join(folder, texture)
        #                     if maya_version >= 2016:
        #                         colorSpace = cmds.colorManagementFileRules(evaluate=inputFile)
        #                     else:
        #                         colorSpace = 'auto'
        #                     item = [os.path.join(root, texture), 0, colorSpace, '', [inputFile]]
        #                     item = [os.path.join(folder, texture), 0, 'sRGB', '', [inputFile]]
        #                     self.selectedItems.append(item)
        #                     self.filesToCreate += 1
        for f in files:
            item = [f, 0, 'sRGB', '', [f]]
            self.selectedItems.append(item)
            self.filesToCreate += 1
        #[[u'/prefs/toolkit/temp/crowds_bag_a_color.1001.tif', 0, 'sRGB', '', [u'/prefs/toolkit/temp/crowds_bag_a_color.1001.tif']]] SAMPLE
        print 'selectedItems: %s' % pformat(self.selectedItems)



    # def showFullPathChange(self, *args):
    #     self.showFullPaths = args[0]
    #     self.displayList()


    # Open a dialog to select a folder and update the information about it
    def selectFolder(self, *args):
        ctrlPath = '|'.join([self.window, 'groupBox_4', 'lineEdit_2']);
        folder = cmds.textField(ctrlPath, query=True, text=True);
        if not os.path.isdir(folder):
            folder = cmds.workspace(query=True, directory=True)
        ret = cmds.fileDialog2(cap='Select Folder',okc='Select',fm=2, startingDirectory=folder)
        if ret is not None and len(ret):
            ctrlPath = '|'.join([self.window, 'groupBox_4', 'lineEdit_2']);
            cmds.textField(ctrlPath, edit=True, text=ret[0]);
            self.selectedFilesFromFolder()


    # Delete the processed .tx files selected
    def deleteTx(self, *args):
        # ctrlPath = '|'.join([self.window, 'radioButton']);
        # selection = cmds.radioButton(ctrlPath, query=True, select=True);
        #
        # self.deletedFiles = 0
        # ctrlPath = '|'.join([self.window, 'groupBox_3', 'label_10']);
        #
        # if selection:
        #     self.selectedFilesFromList()
        # else:
        self.selectedFilesFromFolder()
        #
        # if not self.selectedItems:
        #     cmds.text(ctrlPath, edit=True, label="Deleted: {0}".format(self.deletedFiles));
        #     return

        for textureLine in self.selectedItems:
            texture = textureLine[0]
            if not texture:
                continue

            # loop over the previously listed files
            for inputFile in textureLine[4]:
                txFile = os.path.splitext(inputFile)[0]+".tx"
                if os.path.isfile(txFile):
                    AiTextureInvalidate(txFile)
                    os.remove(txFile)
                    self.deletedFiles += 1

            #cmds.text(ctrlPath, edit=True, label="Deleted: {0}".format(self.deletedFiles))
        self.updateList()

    # Create the processed .tx files in another thread to avoid locking the UI
    def createTx(self, *args):
        if not self.thread:
            self.thread = MakeTxThread(self)
            self.thread.start()



def UpdateAllTx(force):
    txItems = []
    filesCount = []
    filesCount.append(0)
    filesCount.append(0)

    # first we need to make sure the options & color manager node were converted to arnold
    arnoldUniverseActive = AiUniverseIsActive()

    if not arnoldUniverseActive:
        cmds.arnoldScene(mode='create')

    GetTxList(txItems, filesCount)
    totalFiles = filesCount[0]
    missingFiles = filesCount[1]

    print 'Updating TX textures :'
    filesCreated = 0
    createdErrors = 0
    arg_options = "-v --unpremult --oiio"
    if force == 0:
        arg_options = "-u " + arg_options

    maya_version = mutils.getMayaVersion()

    if maya.mel.eval("exists \"colorManagementPrefs\""):
    # only do this if command colorManagementPrefs exists
        render_colorspace = cmds.colorManagementPrefs(query=True, renderingSpaceName=True)
        cmEnable = cmds.colorManagementPrefs(query=True, cmEnabled=True)
    else:
        render_colorspace = 'linear'
        cmEnable = False

    textureList = []

    for textureLine in txItems:
        texture = textureLine[0]
        print '-filename ' + texture
        # we could use textureLine[2] for the colorSpace
        # but in case it hasn't been updated correctly
        # it's still better to ask maya again what is the color space
        nodes = textureLine[3]
        colorSpace = 'auto'
        conflictSpace = False

        # colorSpace didn't exist in maya 2015
        if maya_version >= 2016:
            for node in nodes:
                nodeColorSpace = cmds.getAttr(node+'.colorSpace')
                if colorSpace != 'auto' and colorSpace != nodeColorSpace:
                    conflictSpace=True

                colorSpace = nodeColorSpace

            if colorSpace == 'auto' and textureLine[2] != '':
                colorSpace = textureLine[2]


        if not texture:
            continue;
        if conflictSpace:
            print ' Error : Conflicting color spaces'

        # Process all the files that were found previously for this texture (eventually multiple tokens)
        for inputFile in textureLine[4]:
            # here inputFile is already expanded, and only corresponds to existing files

            if len(textureLine[4]) > 1:
                print '  -'+inputFile

            txArguments = arg_options

            if cmEnable == True and colorSpace != render_colorspace:
                txArguments += ' --colorconvert "'
                txArguments += colorSpace
                txArguments += '" "'
                txArguments += render_colorspace
                txArguments += '"'

            # need to invalidate the TX texture from the cache
            outputTx = os.path.splitext(inputFile)[0] + '.tx'
            AiTextureInvalidate(outputTx)

            textureList.append([inputFile, txArguments])


    for textureToConvert in textureList:
        AiMakeTx(textureToConvert[0], textureToConvert[1])

    status = POINTER(AtMakeTxStatus)()
    source_files = POINTER(AtPythonString)()
    num_submitted = c_uint()
    num_jobs_left = 1   # default to arbitrary value > 0

    createdErrors = 0
    filesCreated = 0

    while (num_jobs_left > 0):
        num_jobs_left = AiMakeTxWaitJob(byref(status), byref(source_files), byref(num_submitted))

    if (num_submitted.value > len(textureList)):
        AiMsgFatal("There are more submitted textures than there are textures! "
                  "Queue should have been cleared!")

    for i in range(0, num_submitted.value):

        if (status[i] == AiTxUpdated):
            filesCreated += 1
            AiMsgInfo("[mtoa.tx] %d: %s was updated", i, source_files[i])
        elif (status[i] == AiTxError):
            createdErrors += 1
            AiMsgError("[mtoa.tx] %d: %s could not be updated", i, source_files[i])

        # need to invalidate the TX texture from the cache
        outputTx = os.path.splitext(source_files[i])[0] + '.tx'
        if outputTx[0] == '"':
            outputTx = outputTx[1:]

        AiTextureInvalidate(outputTx)

    # an arnold scene was created above, let's delete it now
    if not arnoldUniverseActive:
        cmds.arnoldScene(mode='destroy')






