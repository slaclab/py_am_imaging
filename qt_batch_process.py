# -*- coding: utf-8 -*-
"""
Qt Batch Process Movies

Written by: Andy Kiss
Started: 2017-05-16
Last updated: 2017-07-06
"""


# %% Import modules
import os
import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QFileDialog, QHBoxLayout, QVBoxLayout, QTextEdit, QProgressBar, QLabel, QGroupBox, QCheckBox, QGridLayout, QLineEdit)
from PyQt5 import QtCore

# Add custom modules
# mod_path = r'/home/andy/Programming/python/'
mod_path = r'C:\Users\Andy\Programming\python3\py_image_processing\\'
if (mod_path not in sys.path):
    sys.path.append(mod_path)
import txm_image
import image_handling


# %% Define the windows class
class Window(QWidget):
    def __init__(self):
        # Declare some variables
        self.root = ''
        self.ref = ''
        self.ls = []
        self.flag_mv = True
        self.flag_t0 = True
        self.flag_neg = True
        self.flag_out = True
        self.out_delta = 100
        self.flag_bin = True
        self.binning = 1

        super().__init__()
        self.setupUI()

    def setupUI(self):
        # Add a button to set the root directory
        self.buttonBrowse = QPushButton('Browse', self)
        self.buttonBrowse.resize(self.buttonBrowse.sizeHint())
        self.buttonBrowse.clicked.connect(self.getFolder)

        # Add a button to remove files
        self.buttonRemove = QPushButton('Remove', self)
        self.buttonRemove.resize(self.buttonRemove.sizeHint())
        self.buttonRemove.clicked.connect(self.rmFile)

        # Add a listbox to show the files in the root directory
        self.listFiles = QListWidget(self)

        # Add a button to load a reference
        self.buttonRef = QPushButton('Load Reference', self)
        self.buttonRef.resize(self.buttonRef.sizeHint())
        self.buttonRef.clicked.connect(self.getRef)

        # Add a textbox to show the reference file name
        self.textRef = QLineEdit('', self)

        # Add a group box for advanced options
        self.groupAdv = QGroupBox('Advanced options', self)

        # Add advanced options
        self.check_mv = QCheckBox('Write Moving Difference', self)
        self.check_mv.setChecked(True)
        self.check_t0 = QCheckBox('Write Static Difference', self)
        self.check_t0.setChecked(True)
        self.checkNegVal = QCheckBox('Allow negative values', self)
        self.checkNegVal.setChecked(True)

        self.labelRmOut = QLabel('Remove Outliers', self)
        self.textRmOut = QLineEdit('100', self)
        self.textRmOut.setAlignment(QtCore.Qt.AlignRight)
        self.textRmOut.resize(self.textRmOut.sizeHint())
        self.labelBinning = QLabel('Bin', self)
        self.textBinning = QLineEdit('1', self)
        self.textBinning.setAlignment(QtCore.Qt.AlignRight)

        layoutGrid = QGridLayout()
        layoutGrid.addWidget(self.check_mv, 0, 0)
        layoutGrid.addWidget(self.check_t0, 1, 0)
        layoutGrid.addWidget(self.checkNegVal, 2, 0)
        layoutGrid.addWidget(self.labelRmOut, 0, 1)
        layoutGrid.addWidget(self.labelBinning, 1, 1)
        layoutGrid.addWidget(self.textRmOut, 0, 2)
        layoutGrid.addWidget(self.textBinning, 1, 2)
        self.groupAdv.setLayout(layoutGrid)
        

        # Add a button to process the images
        self.buttonGo = QPushButton('Process Movies', self)
        self.buttonGo.clicked.connect(self.processMovies)

        # Add a label for the status bar
        self.labelProgress = QLabel(self)

        # Add a progress bar
        self.progress = QProgressBar(self)

        # Create the left side layout
        hbox_list = QHBoxLayout()
        hbox_list.addWidget(self.buttonBrowse)
        hbox_list.addWidget(self.buttonRemove)
        vbox_list = QVBoxLayout()
        vbox_list.addLayout(hbox_list)
        vbox_list.addWidget(self.listFiles)

        # Setup the right side
        vbox_right = QVBoxLayout()
        vbox_right.addWidget(self.buttonRef)
        vbox_right.addWidget(self.textRef)
        vbox_right.addWidget(self.groupAdv)
        vbox_right.addWidget(self.buttonGo)
        vbox_right.addWidget(self.labelProgress)
        vbox_right.addWidget(self.progress)

        # Set the final layout
        hbox = QHBoxLayout()
        hbox.addLayout(vbox_list)
        hbox.addLayout(vbox_right)
        self.setLayout(hbox)
        self.setWindowTitle('Qt Batch Process')
        self.show()

    def getFolder(self):
        self.root = QFileDialog.getExistingDirectory(self, 'Select root directory')
        # print(self.root)
        if (self.root == ''):
            return
        self.root = self.root + '/'
        self.findFiles()


    def getRef(self):
        (self.ref, _) = QFileDialog.getOpenFileName(self, 'Select reference file', filter='Images (*.tif)')
        # print(self.ref)
        if (self.ref == ''):
            return
        self.textRef.setText(self.ref)

    def findFiles(self):
        # Clear the list
        self.listFiles.clear()
        self.ls.clear()

        # Find the tif files
        self.ls = os.listdir(self.root)
        self.ls.sort()
        N = np.size(self.ls)
        ls_rm = []
        for i in range(N):
            if (self.ls[i].endswith('.tif')):
                continue
            else:
                ls_rm.append(self.ls[i])
        for i in range(np.size(ls_rm)):
            self.ls.remove(ls_rm[i])
        N = np.size(self.ls)

        # Remove any possible flat-fields
        
        # Add the files to the listbox
        self.listFiles.addItems(self.ls)

    def rmFile(self):
        row = self.listFiles.currentRow()
        ls_rm = self.listFiles.currentItem().text()
        self.listFiles.takeItem(row)
        self.ls.remove(ls_rm)

    def processMovies(self):
        # Get parameters
        self.flag_mv = self.check_mv.isChecked()
        self.flag_t0 = self.check_t0.isChecked()
        self.flag_neg = self.checkNegVal.isChecked()
        self.binning = np.int(self.textBinning.text())
        if (self.binning > 0):
            self.flag_bin = True
        else:
            self.flag_bin = False
        self.out_delta = np.int(self.textRmOut.text())
        if (self.out_delta > 0):
            self.flag_out = True
        else:
            self.flag_out = False
    
        # Check for files
        N_img = self.listFiles.count()
        if (N_img == 0):
            self.labelProgress.setText('Please select images to process.')
            return
        if (self.ref == ''):
            self.labelProgress.setText('Please select a reference file.')
            return
        
        # Flat-field
        print('Loading the flat field')
        self.progress.setValue(0)
        self.labelProgress.setText('Flat-field...')
        img_ff = self.process_ff(self.root, self.ref,
                                 flag_remove_outliers=self.flag_out, outlier_delta=self.out_delta,
                                 flag_binning=self.flag_bin, B=self.binning)

        # Movies
        for i in range(N_img):
            self.labelProgress.setText('Movie (%d/%d)...' % (i+1, N_img))
            self.labelProgress.repaint()
            self.progress.setValue(0)
            self.process_img(self.root, self.ls[i], img_ff, self.labelProgress.text(),
                             flag_remove_outliers=self.flag_out, outlier_delta=self.out_delta,
                             flag_binning=self.flag_bin, B=self.binning,
                             flag_remove_neg=self.flag_neg,
                             flag_mv=self.flag_mv, flag_t0=self.flag_t0)

        self.labelProgress.setText('Done')

    # Image processing functions
    def process_ff(self, root, fn,
                   flag_remove_outliers=True, outlier_delta=100, outlier_reg=3,
                   flag_binning=True, B=4, bin_method='average'):

        # Load the file
        self.labelProgress.setText('Flat-field...loading')
        self.labelProgress.repaint()
        ff, _ = txm_image.read_file(fn, verbose=False)
        ff = np.array(ff, dtype=np.float32)
        # print('%s loaded...' % (fn))
        self.progress.setValue(20)
    
        # Remove outliers
        N = ff.shape[0]        
        if (flag_remove_outliers):
            self.labelProgress.setText('Flat-field...removing outliers')
            self.labelProgress.repaint()
            for i in range(N):
                ff[i, :, :] = image_handling.remove_outliers_scipy(ff[i, :, :],
                                                                   delta=outlier_delta,
                                                                   radius=outlier_reg)
            # print('Outliers removed...')
        self.progress.setValue(40)
    
        # Binning
        if (flag_binning):
            self.labelProgress.setText('Flat-field...binning')
            self.labelProgress.repaint()
            # ff = image_handling.bin_image(ff, B=B, method=bin_method)
            ff = image_handling.bin_pixels(ff, bin_size=(B, B))
        self.progress.setValue(60)
    
        # Average stack
        self.labelProgress.setText('Flat-field...averaging stack')
        self.labelProgress.repaint()
        ff = image_handling.average_image_stack(ff)
        # print('Stack averaged...')
        self.progress.setValue(80)
    
        # Output average
        self.labelProgress.setText('Flat-field...writing file')
        self.labelProgress.repaint()
        ff_token = '_testing_avg'
        i = fn.rfind('.tif')
        fn_out = fn[0:i] + ff_token + fn[i:]
        txm_image.write_file(fn_out, ff, verbose=False)
        # print('File output')
        self.progress.setValue(100)

        # Return the ff image
        return ff

    def process_img(self, root, fn, ff, label_text,
                    flag_remove_outliers=True, outlier_delta=100, outlier_reg=3,
                    flag_binning=True, B=4, bin_method='average',
                    flag_remove_neg=False, N_t0=10,
                    flag_mv=True, flag_t0=True):

        # Make file/folder names
        out_dir_token = '_processing/'
        i = fn.rfind('.tif')
        outdir = fn[0:i] + out_dir_token
        if (not os.path.isdir(root + outdir)):
            os.mkdir(root + outdir)

        abs_token = '_abs'
        fn_abs = fn[0:i] + abs_token + fn[i:]

        mv_token = '_mv_diff'
        fn_mv = fn[0:i] + mv_token + fn[i:]

        t0_token = '_t0_diff'
        fn_t0 = fn[0:i] + t0_token + fn[i:]

        progStep = 100 / 7

        # Read the file
        self.labelProgress.setText(label_text + 'read file')
        self.labelProgress.repaint()
        (img, _) = txm_image.read_file(root+fn, verbose=False)
        img = np.array(img, dtype=np.float32)
        self.progress.setValue(1 * progStep)

        # Remove outliers
        if (flag_remove_outliers):
            self.labelProgress.setText(label_text + 'remove outliers')
            self.labelProgress.repaint()
            N = img.shape[0]
            if (flag_remove_outliers):
                for i in range(N):
                    img[i, :, :] = image_handling.remove_outliers_scipy(img[i, :, :],
                                                                        delta=outlier_delta,
                                                                        radius=outlier_reg)
        self.progress.setValue(2 * progStep)

        # Bin the projections
        if (flag_binning):
            self.labelProgress.setText(label_text + 'binning')
            self.labelProgress.repaint()
            # img = image_handling.bin_image(img, B=B, method=bin_method)
            img = image_handling.bin_pixels(img, bin_size=(B, B))
        self.progress.setValue(3 * progStep)

        # Add reference alignment

        # Apply reference correction
        self.labelProgress.setText(label_text + 'reference correction')
        self.labelProgress.repaint()
        for i in range(N):
            img[i, :, :] = image_handling.external_reference(img[i, :, :],
                                                             ff,
                                                             flag_remove_neg=flag_remove_neg)
        self.progress.setValue(4 * progStep)

        # Save the projections
        self.labelProgress.setText(label_text + 'saving projections')
        self.labelProgress.repaint()
        txm_image.write_file(root + outdir + fn_abs, img, verbose=False)
        self.progress.setValue(5 * progStep)

        # Create the moving difference movie
        if (flag_mv):
            self.labelProgress.setText(label_text + 'moving difference')
            self.labelProgress.repaint()
            img_mv_diff = img[1:, :, :] - img[0:-1, :, :]
            txm_image.write_file(root + outdir + fn_mv, img_mv_diff, verbose=False)
            self.progress.setValue(7 * progStep)
            del img_mv_diff

        # Create the static difference movie
        if (flag_t0):
            self.labelProgress.setText(label_text + 'static difference')
            self.labelProgress.repaint()
            img0 = image_handling.average_image_stack(img[0:N_t0, :, :])
            img_t0_diff = img - img0
            txm_image.write_file(root + outdir + fn_t0, img_t0_diff, verbose=False)
            del img_t0_diff

        # Final garbage collection
        self.progress.setValue(100)
        del img
        
        return
   

# %% Main function
if (__name__ == '__main__'):
    app = QApplication(sys.argv)
    # app.setStyle('windows')
    w = Window()
    sys.exit(app.exec_())

