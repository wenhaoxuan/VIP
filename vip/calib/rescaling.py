#! /usr/bin/env python

"""
Module with frame resampling/rescaling functions.
"""
__author__ = 'C. Gomez @ ULg, V. Christiaens @ ULg'
__all__ = ['frame_px_resampling',
           'cube_px_resampling',
           'frame_rescaling',
           'cube_rescaling',
           'check_scal_vector']

import cv2
import numpy as np
from scipy.ndimage.interpolation import geometric_transform
from ..var import frame_center



def frame_px_resampling(array, scale, interpolation='bicubic', scale_y=None,
                        scale_x=None):
    """ Resamples the pixels of a frame wrt to the center, changing the size
    of the frame. If 'scale' < 1 then the frame is downsampled and if 
    'scale' > 1 then its pixels are upsampled. Uses opencv for maximum speed. 
    Several modes of interpolation are available. 
    
    Parameters
    ----------
    array : array_like 
        Input frame, 2d array.
    scale : float
        Scale factor for upsampling or downsampling the frame.
    interpolation : {'bicubic', 'bilinear', 'nearneig'}, optional
        'nneighbor' stands for nearest-neighbor interpolation,
        'bilinear' stands for bilinear interpolation,
        'bicubic' for interpolation over 4x4 pixel neighborhood.
        The 'bicubic' is the default. The 'nearneig' is the fastest method and
        the 'bicubic' the slowest of the three. The 'nearneig' is the poorer
        option for interpolation of noisy astronomical images. 
        Even with 'bicubic' interpolation, opencv library is several orders of
        magnitude faster than python similar functions (e.g. ndimage).
    scale_y : float
        Scale factor for upsampling or downsampling the frame along y. If 
        provided, it takes priority on scale parameter.
    scale_x : float
        Scale factor for upsampling or downsampling the frame along x. If 
        provided, it takes priority on scale parameter.
        
    Returns
    -------
    array_resc : array_like 
        Output resampled frame.
    """
    if not array.ndim == 2:
        raise TypeError('Input array is not a frame or 2d array.')

    if scale_y is None: scale_y = scale
    if scale_x is None: scale_x = scale
    
    if interpolation == 'bilinear':
        intp = cv2.INTER_LINEAR
    elif interpolation == 'bicubic':
        intp= cv2.INTER_CUBIC
    elif interpolation == 'nearneig':
        intp = cv2.INTER_NEAREST
    else:
        raise TypeError('Interpolation method not recognized.')
    
    array_resc = cv2.resize(array.astype(np.float32), (0,0), fx=scale_x, 
                            fy=scale_y, interpolation=intp)
    return array_resc



def cube_px_resampling(array, scale, interpolation='bicubic', scale_y=None,
                       scale_x=None):
    """ Wrapper of frame_px_resample() for resampling the frames of a cube with
    a single scale. Useful when we need to upsample (upsacaling) or downsample 
    (pixel binning) a set of frames, e.g. an ADI cube. 
    
    Parameters
    ----------
    array : array_like 
        Input frame, 2d array.
    scale : float
        Scale factor for upsampling or downsampling the frames in the cube.
    interpolation : {'bicubic', 'bilinear', 'nearneig'}, optional
        'nneighbor' stands for nearest-neighbor interpolation,
        'bilinear' stands for bilinear interpolation,
        'bicubic' for interpolation over 4x4 pixel neighborhood.
        The 'bicubic' is the default. The 'nearneig' is the fastest method and
        the 'bicubic' the slowest of the three. The 'nearneig' is the poorer
        option for interpolation of noisy astronomical images. 
        Even with 'bicubic' interpolation, opencv library is several orders of
        magnitude faster than python similar functions (e.g. ndimage).
    scale_y : float
        Scale factor for upsampling or downsampling the frame along y. If 
        provided, it takes priority on scale parameter.
    scale_x : float
        Scale factor for upsampling or downsampling the frame along x. If 
        provided, it takes priority on scale parameter.
        
    Returns
    -------
    array_resc : array_like 
        Output cube with resampled frames.

    Notes
    -----
    Be aware that the interpolation used for the pixel rescaling can create
    negative values at the transition from a background composed mostly of zeros
    to a positive valued patch (e.g. an injected PSF template).

    """
    if not array.ndim==3:
        raise TypeError('Input array is not a cube or 3d array.')
    
    if scale_y is None: scale_y = scale
    if scale_x is None: scale_x = scale

    array_resc = np.zeros((array.shape[0], int(round(array.shape[1]*scale_y)), 
                           int(round(array.shape[2]*scale_x))))
    for i in range(array.shape[0]):
        array_resc[i] = frame_px_resampling(array[i], scale=scale, 
                                            interpolation=interpolation,
                                            scale_y=scale_y, scale_x=scale_x)
        array_resc[i] /= scale**2

    return array_resc



def frame_rescaling(array, ref_y=None, ref_x=None, scale=1.0, 
                    method='geometric_transform', scale_y=None, scale_x=None):
    """
    Function to rescale a frame by a factor 'scale', wrt a reference point 
    ref_pt which by default is the center of the frame (typically the exact 
    location of the star). However, it keeps the same dimensions. It uses spline 
    interpolation of order 3 to find the new values in the output array.
    
    Parameters
    ----------
    array : array_like 
        Input frame, 2d array.
    ref_y, ref_x : float, optional
        Coordinates X,Y  of the point with respect to which the rotation will be
        performed. By default the rotation is done with respect to the center 
        of the frame; central pixel if frame has odd size.
    scale : float
        Scaling factor. If > 1, it will upsample the input array equally along y
        and x by this factor.      
    method: string, {'geometric_transform','cv2.warp_affine'}, optional
        String determining which library to apply to rescale. 
        Both options use a spline of order 3 for interpolation.
        Opencv is a few order of magnitudes faster than ndimage.
    scale_y : float
        Scaling factor only for y axis. If provided, it takes priority on scale
        parameter.
    scale_x : float
        Scaling factor only for x axis. If provided, it takes priority on scale
        parameter.

    Returns
    -------
    array_out : array_like
        Resulting frame.
    """
    def _scale_func(output_coords,ref_y=0,ref_x=0, scaling=1.0, scaling_y=None,
                    scaling_x=None):    
        """
        For each coordinate point in a new scaled image (output_coords), 
        coordinates in the image before the scaling are returned. 
        This scaling function is used within geometric_transform (in 
        frame_rescaling), 
        which, for each point in the output image, will compute the (spline)
        interpolated value at the corresponding frame coordinates before the 
        scaling.
        """
        if scaling_y is None:
            scaling_y = scaling
        if scaling_x is None:
            scaling_x = scaling
        return (ref_y+((output_coords[0]-ref_y)/scaling_y), 
                ref_x+((output_coords[1]-ref_x)/scaling_x))

    array_out = np.zeros_like(array)
    
    if not ref_y and not ref_x:  ref_y, ref_x = frame_center(array)

    if method == 'geometric_transform':
        geometric_transform(array, _scale_func, output_shape=array.shape, 
                            output = array_out, 
                            extra_keywords={'ref_y':ref_y,'ref_x':ref_x,
                                            'scaling':scale,'scaling_y':scale_y,
                                            'scaling_x':scale_x})

    elif method == 'cv2.warp_affine':
        if scale_y is None: scale_y = scale
        if scale_x is None: scale_x = scale
        M = np.array([[scale_x,0,(1.-scale_x)*ref_x],
                      [0,scale_y,(1.-scale_y)*ref_y]])
        array_out = cv2.warpAffine(array.astype(np.float32), M, 
                                   (array.shape[1], array.shape[0]), 
                                   flags=cv2.INTER_CUBIC)

    else:
        msg="Pick a valid method: 'geometric_transform' or 'cv2.warp_affine'"
        raise ValueError(msg)

    return array_out

    
    
def cube_rescaling(array, scaling_list, ref_y=None, ref_x=None, 
                   method='cv2.warp_affine',scaling_y=None, scaling_x=None):
    """ 
    Function to rescale a cube, frame by frame, by a factor 'scale', with 
    respect to position (cy,cx). It calls frame_rescaling function.
    
    Parameters
    ----------
    array : array_like 
        Input 3d array, cube.
    scaling_list : 1D-array
        Scale corresponding to each frame in the cube.
    ref_y, ref_x : float, optional
        Coordinates X,Y  of the point with respect to which the rescaling will be
        performed. By default the rescaling is done with respect to the center 
        of the frames; central pixel if the frames have odd size.
    method: {'cv2.warp_affine', 'geometric_transform'}, optional
        String determining which library to apply to rescale. 
        Both options use a spline of order 3 for interpolation.
        Opencv is a few order of magnitudes faster than ndimage.
    scaling_y : 1D-array or list
        Scaling factor only for y axis. If provided, it takes priority on 
        scaling_list.
    scaling_x : 1D-array or list
        Scaling factor only for x axis. If provided, it takes priority on 
        scaling_list.
        
    Returns
    -------
    array_sc : array_like
        Resulting cube with rescaled frames.
    array_out : array_like
        Median combined image of the rescaled cube.
    """
    if not array.ndim == 3:
        raise TypeError('Input array is not a cube or 3d array.')
    array_sc = np.zeros_like(array)
    if scaling_y is None: scaling_y = [None]*array.shape[0]
    if scaling_x is None: scaling_x = [None]*array.shape[0]
    
    if not ref_y and not ref_x:  ref_y, ref_x = frame_center(array[0])
    
    for i in xrange(array.shape[0]): 
        array_sc[i] = frame_rescaling(array[i], ref_y=ref_y, ref_x=ref_x, 
                                      scale=scaling_list[i], method=method,
                                      scale_y=scaling_y[i], 
                                      scale_x=scaling_x[i])
            
    array_out = np.median(array_sc, axis=0)              
    return array_sc, array_out


def check_scal_vector(scal_vec):
    """
    Function to check if the scaling list has the right format to avoid any bug
    in the pca algorithm, in the case of ifs data.
    Indeed, all scaling factors should be >= 1 (i.e. the scaling should be done
    to match the longest wavelength of the cube)

    Parameter:
    ----------
    scal_vec: array_like, 1d OR list

    Returns:
    --------
    scal_vec: array_like, 1d 
        Vector containing the scaling factors (after correction to comply with
        the condition >= 1)

    """
    correct = False

    if isinstance(scal_vec, list):
        scal_list = scal_vec.copy()
        nz = len(scal_list)
        scal_vec = np.zeros(nz)
        for ii in range(nz):
            scal_vec[ii] = scal_list[ii]
        correct = True
    elif isinstance(scal_vec,np.ndarray):
        nz = scal_vec.shape[0]
    else:
        raise TypeError('scal_vec is neither a list or an np.ndarray')

    scal_min = np.amin(scal_vec)

    if scal_min < 1:
        correct = True

    if correct:
        for ii in range(nz):
            scal_vec[ii] = scal_vec[ii]/scal_min

    return scal_vec

