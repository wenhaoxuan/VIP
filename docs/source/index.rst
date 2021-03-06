.. This file should at least contain the root `toctree` directive.

.. Welcome to ``VIP``'s documentation
.. ==============================

.. image::  _static/logo.jpg
   :align:  center
   :scale:  20 %
   :target: #

.. include:: readme.rst


Frequently asked questions
--------------------------
Check out this questions if you find problems when installing or running ``VIP``
for the first time.

.. toctree::
   :maxdepth: 2

   faq


Package structure
-----------------
On the links below you can find the subpackages structure and access the
docstrings (internal documentation) of each one of ``VIP``'s functions.

``VIP`` implements basic image processing functionalities e.g. image registration,
image rotation, pixel temporal and spatial subsampling. On top of that several
pre-processing functions are available such as re-centering and bad frame
detection.

For Angular differential imaging (ADI) data several point spread function
subtraction techniques are available, from a simple median subtraction to
different low-rank approximations. Principal Component Analysis (PCA) methods
are implemented in different flavours. Also PCA can process RDI and multiple
channel SDI (IFS) data. ``VIP`` contains a first version of the Local Low-rank plus
Sparse plus Gaussian-noise decomposition (LLSG, Gomez Gonzalez et al. 2016).

Functions for Signal-to-noise ratio (S/N) estimation and S/N map generation are
included.

Flux and position of point-like sources are estimated using the Negative Fake
Companion technique. ``VIP`` also implements algorithm throughput and contrast-curve
generation routines.

.. toctree::
   :maxdepth: 3

   vip


API
---

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

