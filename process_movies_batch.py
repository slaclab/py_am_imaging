# -*- coding: utf-8 -*-
"""
A script to process all the files in a given folder

Written by: Andy Kiss
Created: 2017-05-15
Last modified: 2017-05-15

"""


# %% Import modules
import numpy as np
import os
import time
from skimage.feature import register_translation
from skimage.transform import warp, SimilarityTransform

import sys
mod_path = r'C:\Users\andykiss\Documents\programming\python\\'
if (mod_path not in sys.path):
    sys.path.append(mod_path)
import txm_image
import image_handling


# %% Settings
# Paths and filenames
root = r'R:\b_txmuser\AndyKiss\CAAM\2017Apr\20170420\sample7\\'
flag_auto_find = False
flag_overwrite = True
out_token = '_processing\\'
fn_img = r'1626_10x_1kHz_sample7_region6.tif'
fn_ff = r'1648_10x_2kHz_sample7_region6_ref.tif'
N = 1

# Reference corrction settings
flag_remove_outliers = True
outlier_delta = 100
outlier_reg = 3

# Binning settings
flag_binning = False
B = 1
bin_method = 'sum'

# Region of interest for aligning the reference to the projections
flag_align_ref = True
flag_auto_align = True
shift = (0, 0)  # Manually assign the shift
ROI = (200, 600, 500, 1300)  # ROI = (minRow, maxRow, minCol, maxCol)
ROI_up = 10  # upscaling for alignment

# Remove negative values from reference correction
flag_remove_ff_neg = False

# Number of frames to average for t0 difference movie
N_t0 = 30


# %% Find the files for processing
# Get starting time
t0 = time.time()

# Find the tiff files
if (flag_auto_find):
    ls = os.listdir(root)
    ls.sort()
    N = np.size(ls)
    ls_rm = []
    for i in range(N):
        if (ls[i].endswith('.tif')):
            continue
        else:
            ls_rm.append(ls[i])
    for i in range(np.size(ls_rm)):
        ls.remove(ls_rm[i])
    N = np.size(ls)

    # Find the flat-field tiff
    fn_ff_token = '_ref'
    ls_rm.clear()
    for i in range(N):
        if (ls[i].find(fn_ff_token) != -1):
            fn_ff = ls[i]
            ls_rm.append(fn_ff)
    for i in range(np.size(ls_rm)):
        ls.remove(ls_rm[i])
    N = np.size(ls)

    # Check for overwriting
    # out_token = '_processing\\'
    if (not flag_overwrite):
        ls_dir = os.listdir(root)
        ls_rm.clear()
        for i in range(N):
            for j in range(np.size(ls_dir)):
                dir_name = ls[i][0:-4] + out_token[0:-1]
                if (ls_dir[j].find(dir_name) != -1):
                    ls_rm.append(ls[i])
        for i in range(np.size(ls_rm)):
            ls.remove(ls_rm[i])
else:
    ls = []
    ls.append(fn_img)

N = np.size(ls)


# %% Welcome
print('\nWelcome!')
print('%s\n' % (time.ctime()))
print('Starting to process the files in:\n%s\n' % (root))

print('%d files found.' % (N))


# %% Make the reference correction
# Read in the reference image stack
print('Processing flat-fields...')
print('Loading flat-fields... ', end='')
(ff, _) = txm_image.read_file(root+fn_ff, verbose=False)
ff = np.array(ff, dtype=np.float32)
print('done')

# Remove outliers
N = ff.shape[0]
if (flag_remove_outliers):
    for i in range(N):
        print('\rRemoving outliers (%04d/%04d)... ' % (i+1, N), end='')
        ff[i, :, :] = image_handling.remove_outliers_scipy(ff[i, :, :],
                                                           delta=outlier_delta,
                                                           radius=outlier_reg)
    print('done')

# Bin the flat fields
if (flag_binning):
    for i in range(N):
        print('\rBinning flat-fields... ' % (i+1, N), end='')
        ff = image_handling.bin_image(ff, B=B, method=bin_method)
        print('done')

# Average stack
print('Averaging flat-fields... ', end='')
I0 = image_handling.average_image_stack(ff)
print('done')

# Output average
ff_token = '_avg'
print('Saving flat-field... ', end='')
i = fn_ff.rfind('.tif')
out_ff = root + fn_ff[0:i] + ff_token + fn_ff[i:]
txm_image.write_file(out_ff, I0, verbose=False)
print('done')

# Garbage collection
del ff


# %% Start the loop to go through the files in the folder
N = np.size(ls)
for i in range(N):
    fn_img = ls[i]
    print('\nProcessing %s... ' % (fn_img))

    # Fairly repeatable values
    i = fn_img.rfind('.tif')
    outdir = fn_img[0:i] + out_token

    ff_token = '_avg'
    i = fn_ff.rfind('.tif')
    out_ff = root + outdir + fn_ff[0:i] + ff_token + fn_ff[i:]

    align_token = '_aligned'
    i = out_ff.rfind('.tif')
    out_ff_align = out_ff[0:i] + align_token + out_ff[i:]

    abs_token = '_abs'
    i = fn_img.rfind('.tif')
    out_abs = root + outdir + fn_img[0:i] + abs_token + fn_img[i:]

    mv_token = '_mv_diff'
    out_mv_diff = root + outdir + fn_img[0:i] + mv_token + fn_img[i:]

    t0_token = '_t0_diff'
    out_t0_diff = root + outdir + fn_img[0:i] + t0_token + fn_img[i:]

    # Check for output directory, outdir
    if (not os.path.isdir(root + outdir)):
        os.mkdir(root + outdir)

    # Apply the reference correction to the images
    # Read in the movie
    print('Loading projections... ', end='')
    (img, _) = txm_image.read_file(root+fn_img, verbose=False)
    img = np.array(img, dtype=np.float32)
    print('done')

    # Remove outliers
    N = img.shape[0]
    if (flag_remove_outliers):
        for i in range(N):
            print('\rRemoving outliers (%04d/%04d)... ' % (i+1, N), end='')
            img[i, :, :] = image_handling.remove_outliers_scipy(img[i, :, :],
                                                                delta=outlier_delta,
                                                                radius=outlier_reg)
    print('done')

    # Bin the projections
    if (flag_binning):
        for i in range(N):
            print('\rBinning projections... ' % (i+1, N), end='')
            img = image_handling.bin_image(img, B=B, method=bin_method)
            print('done')

    # Align the reference to the projections
    if (flag_align_ref):
        print('Aligning reference to projections...')
        # if (shift[0] == 0 and shift[1] == 0):
        if (flag_auto_align):
            I0_ROI = I0[ROI[0]:ROI[1], ROI[2]:ROI[3]]
            I_ROI = img[0, ROI[0]:ROI[1], ROI[2]:ROI[3]]
            (shift, err, _) = register_translation(I_ROI, I0_ROI,
                                                   upsample_factor=ROI_up)
            shift = -1 * shift
        tform = SimilarityTransform(translation=shift)
        I0_reg = warp(np.float64(I0), tform)
        I0_reg = np.float32(I0_reg)
        print('\tdelx = %4.2f\tdely = %4.2f' % (shift[0], shift[1]))
        print('Saving aligned reference... ', end='')
        txm_image.write_file(out_ff_align, I0_reg, verbose=False)
        print('done')
    else:
        I0_reg = I0

    # Apply reference correction
    for i in range(N):
        print('\rApplying flat-field correction (%04d/%04d)... ' % (i+1, N),
              end='')
        img[i, :, :] = image_handling.external_reference(img[i, :, :], I0_reg, flag_remove_neg=flag_remove_ff_neg)
    print('done')

    # Output movie
    print('Saving projections... ', end='')
    txm_image.write_file(out_abs, img, verbose=False)
    print('done')

    # Create the moving difference movie
    # Create the moving difference movie
    print('Calculating the moving difference movie... ', end='')
    img_mv_diff = img[1:, :, :] - img[0:-1, :, :]
    print('done')

    # Save the movie
    print('Saving the moving difference movie... ', end='')
    txm_image.write_file(out_mv_diff, img_mv_diff, verbose=False)
    print('done')

    # Garbage collection
    del img_mv_diff

    # Create the t0 difference movie
    # Average the first frames for a t0 reference
    img_t0 = image_handling.average_image_stack(img[0:N_t0, :, :])

    # Find the difference from t0
    print('Calculating the t0 difference movie... ', end='')
    img_t0_diff = img - img_t0
    print('done')

    # Save the movie
    print('Saving the t0 difference movie... ', end='')
    txm_image.write_file(out_t0_diff, img_t0_diff, verbose=False)
    print('done')

    # Garbage collection
    del img_t0, img_t0_diff


# %% Done
# Garbage collection
del img, I0, I0_reg

# Get finish time
t1 = time.time()
delt = t1 - t0

print('\n%s' % (time.ctime()))
if (delt < 60):
    print('Elapsed time: %f s' % (delt))
elif (delt < 3600):
    print('Elapsed time: %f m' % (delt / 60))
else:
    print('Elapsed time: %f h' % (delt / 3600))
print('Done!\n')
