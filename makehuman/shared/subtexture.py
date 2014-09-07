#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

""" 
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Jonas Hauquier
                       Marc Flerackers
                       Thanasis Papoutsidakis

**Copyright(c):**      MakeHuman Team 2001-2014

**Licensing:**         AGPL3 (http://www.makehuman.org/doc/node/the_makehuman_application.html)

    This file is part of MakeHuman (www.makehuman.org).

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

**Coding Standards:**  See http://www.makehuman.org/node/165

Abstract
--------

Definitions for combining and manipulating subtextures
as multi-layered images.
"""

from image import Image


class Layer(Image):
    """
    A Layer is an Image that can be inserted in a
    LayeredImage to be processed as a layer of a
    greater image compilation.
    """
    def __init__(self, img, borders=(0, 0, 0, 0)):
        super(Layer, self).__init__(img)
        self.borders = borders


class LayeredImage(Image):
    """
    A LayeredImage is a container of multiple
    overlapping image layers.
    It is designed to inherit from and externally
    behave like an Image, while managing all its
    layers in the background.
    """

    def __init__(self, *args, **kwargs):
        self.layers = []
        for arg in args:
            if isinstance(arg, Layer):
                self.addLayer(arg)
            elif isinstance(arg, Image):
                self.addLayer(Layer(arg))
            elif isinstance(arg, tuple):
                self.addLayer(Layer(*arg))

    def addLayer(self, layer):
        self.layers.append(layer)

    # TODO Override and imitate Image's methods
    # so that they return the result calculated
    # by processing all layers. Use caching to
    # avoid calculation repetitions.

