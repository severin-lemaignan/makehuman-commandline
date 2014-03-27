#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Marc Flerackers, Jonas Hauquier, Thomas Larsson

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

Clothes library.
"""

import proxychooser

import gui3d
import gui
import log
import numpy as np


#
#   Clothes
#

class ClothesTaskView(proxychooser.ProxyChooserTaskView):

    def __init__(self, category):
        super(ClothesTaskView, self).__init__(category, 'clothes', multiProxy = True, tagFilter = True)

        #self.taggedClothes = {}

        self.originalHumanMask = self.human.meshData.getFaceMask().copy()
        self.faceHidingTggl = self.optionsBox.addWidget(FaceHideCheckbox("Hide faces under clothes"))
        @self.faceHidingTggl.mhEvent
        def onClicked(event):
            self.updateFaceMasks(self.faceHidingTggl.selected)
        @self.faceHidingTggl.mhEvent
        def onMouseEntered(event):
            self.visualizeFaceMasks(True)
        @self.faceHidingTggl.mhEvent
        def onMouseExited(event):
            self.visualizeFaceMasks(False)
        self.faceHidingTggl.setSelected(True)

        self.oldPxyMats = {}
        self.blockFaceMasking = False

    def createFileChooser(self):
        self.optionsBox = self.addLeftWidget(gui.GroupBox('Options'))
        super(ClothesTaskView, self).createFileChooser()

    def getObjectLayer(self):
        return 10

    def proxySelected(self, pxy, obj):
        uuid = pxy.getUuid()
        self.human.clothesProxies[uuid] = pxy
        self.updateFaceMasks(self.faceHidingTggl.selected)

    def proxyDeselected(self, pxy, obj, suppressSignal = False):
        uuid = pxy.uuid
        del self.human.clothesProxies[uuid]
        if not suppressSignal:
            self.updateFaceMasks(self.faceHidingTggl.selected)

    def resetSelection(self):
        super(ClothesTaskView, self).resetSelection()
        self.updateFaceMasks(self.faceHidingTggl.selected)

    def getClothesByRenderOrder(self):
        """
        Return UUIDs of clothes proxys sorted on proxy.z_depth render queue
        parameter (the order in which they will be rendered).
        """
        decoratedClothesList = [(pxy.z_depth, pxy.uuid) for pxy in self.getSelection()]
        decoratedClothesList.sort()
        return [uuid for (_, uuid) in decoratedClothesList]

    def updateFaceMasks(self, enableFaceHiding = True):
        """
        Apply facemask (deleteVerts) defined on clothes to body and lower layers
        of clothing. Uses order as defined in self.clothesList.
        """
        if self.blockFaceMasking:
            return

        log.debug("Clothes library: updating face masks (face hiding %s).", "enabled" if enableFaceHiding else "disabled")

        human = self.human
        if not enableFaceHiding:
            human.meshData.changeFaceMask(self.originalHumanMask)
            human.meshData.updateIndexBufferFaces()
            proxies = self.getSelection()
            if self.human.genitalsProxy:
                proxies.append(self.human.genitalsProxy)
            for pxy in proxies:
                obj = pxy.object
                faceMask = np.ones(obj.mesh.getFaceCount(), dtype=bool)
                obj.mesh.changeFaceMask(faceMask)
                obj.mesh.updateIndexBufferFaces()
            return

        vertsMask = np.ones(human.meshData.getVertexCount(), dtype=bool)
        log.debug("masked verts %s", np.count_nonzero(~vertsMask))

        stackedProxies = [human.clothesProxies[uuid] for uuid in reversed(self.getClothesByRenderOrder())]
        # Mask genitals too
        if self.human.genitalsProxy:
            stackedProxies.append( self.human.genitalsProxy )

        for pxy in stackedProxies:
            obj = pxy.object

            # Convert basemesh vertex mask to local mask for proxy vertices
            proxyVertMask = np.ones(len(pxy.ref_vIdxs), dtype=bool)
            for idx,hverts in enumerate(pxy.ref_vIdxs):
                # Body verts to which proxy vertex with idx is mapped
                if len(hverts) == 3:
                    (v1,v2,v3) = hverts
                    # Hide proxy vert if any of its referenced body verts are hidden (most agressive)
                    #proxyVertMask[idx] = vertsMask[v1] and vertsMask[v2] and vertsMask[v3]
                    # Alternative1: only hide if at least two referenced body verts are hidden (best result)
                    proxyVertMask[idx] = np.count_nonzero(vertsMask[[v1, v2, v3]]) > 1
                    # Alternative2: Only hide proxy vert if all of its referenced body verts are hidden (least agressive)
                    #proxyVertMask[idx] = vertsMask[v1] or vertsMask[v2] or vertsMask[v3]

            proxyKeepVerts = np.argwhere(proxyVertMask)[...,0]
            proxyFaceMask = obj.mesh.getFaceMaskForVertices(proxyKeepVerts)

            # Apply accumulated mask from previous clothes layers on this clothing piece
            obj.mesh.changeFaceMask(proxyFaceMask)
            obj.mesh.updateIndexBufferFaces()
            log.debug("%s faces masked for %s", np.count_nonzero(~proxyFaceMask), pxy.name)

            if pxy.deleteVerts != None and len(pxy.deleteVerts > 0):
                log.debug("Loaded %s deleted verts (%s faces) from %s", np.count_nonzero(pxy.deleteVerts), len(human.meshData.getFacesForVertices(np.argwhere(pxy.deleteVerts)[...,0])),pxy.name)

                # Modify accumulated (basemesh) verts mask
                verts = np.argwhere(pxy.deleteVerts)[...,0]
                vertsMask[verts] = False
            log.debug("masked verts %s", np.count_nonzero(~vertsMask))

        basemeshMask = human.meshData.getFaceMaskForVertices(np.argwhere(vertsMask)[...,0])
        human.meshData.changeFaceMask(np.logical_and(basemeshMask, self.originalHumanMask))
        human.meshData.updateIndexBufferFaces()

        # Transfer face mask to subdivided mesh if it is set
        if human.isSubdivided():
            human.updateSubdivisionMesh(rebuildIndexBuffer=True, progressCallback=gui3d.app.progress)

        log.debug("%s faces masked for basemesh", np.count_nonzero(~basemeshMask))


    def onShow(self, event):
        super(ClothesTaskView, self).onShow(event)
        if gui3d.app.settings.get('cameraAutoZoom', True):
            gui3d.app.setGlobalCamera()

    def onHide(self, event):
        super(ClothesTaskView, self).onHide(event)
        self.visualizeFaceMasks(False)

    def loadHandler(self, human, values):
        if values[0] == 'status':
            if values[1] == 'started':
                # Don't update face masks during loading (optimization)
                self.blockFaceMasking = True
            elif values[1] == 'finished':
                # When loading ends, update face masks
                self.blockFaceMasking = False
                self.updateFaceMasks(self.faceHidingTggl.selected)
            return

        if values[0] == 'clothesHideFaces':
            enabled = values[1].lower() in ['true', 'yes']
            self.faceHidingTggl.setChecked(enabled)
            return

        super(ClothesTaskView, self).loadHandler(human, values)

    def onHumanChanged(self, event):
        super(ClothesTaskView, self).onHumanChanged(event)
        if event.change == 'reset':
            self.faceHidingTggl.setSelected(True)
        elif event.change == 'proxy' and event.pxy == 'genitals' \
             and self.faceHidingTggl.selected:
            # Update face masks if genital proxy was changed
            self.updateFaceMasks(self.faceHidingTggl.selected)

    def saveHandler(self, human, file):
        super(ClothesTaskView, self).saveHandler(human, file)
        file.write('clothesHideFaces %s\n' % self.faceHidingTggl.selected)

    def registerLoadSaveHandlers(self):
        super(ClothesTaskView, self).registerLoadSaveHandlers()
        gui3d.app.addLoadHandler('clothesHideFaces', self.loadHandler)

    def visualizeFaceMasks(self, enabled):
        import material
        import getpath
        if enabled:
            self.oldPxyMats = dict()
            xray_mat = material.fromFile(getpath.getSysDataPath('materials/xray.mhmat'))
            for pxy in self.human.getProxies():
                self.oldPxyMats[pxy.uuid] = pxy.object.material.clone()
                pxy.object.material = xray_mat
        else:
            for pxy in self.human.getProxies():
                if pxy.uuid in self.oldPxyMats:
                    pxy.object.material = self.oldPxyMats[pxy.uuid]

class FaceHideCheckbox(gui.CheckBox):
    def enterEvent(self, event):
        self.callEvent("onMouseEntered", None)

    def leaveEvent(self, event):
        self.callEvent("onMouseExited", None)


# This method is called when the plugin is loaded into makehuman
# The app reference is passed so that a plugin can attach a new category, task, or other GUI elements

taskview = None

def load(app):
    global taskview

    category = app.getCategory('Geometries')
    taskview = ClothesTaskView(category)
    taskview.sortOrder = 0
    category.addTask(taskview)

    taskview.registerLoadSaveHandlers()

# This method is called when the plugin is unloaded from makehuman
# At the moment this is not used, but in the future it will remove the added GUI elements


def unload(app):
    taskview.onUnload()

