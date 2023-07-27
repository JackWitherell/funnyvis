import json
import numpy as np
from OpenGL.GL import *

class GLTFScene:
    def __init__(self, filename):
        self.loadNewGltf(filename)

    def loadNewGltf(self, filename):
        def parseNode(node, gltfdata):
            tempnode = node
            if ("matrix" in tempnode):
                tempnode.update({"matrix": np.array(tempnode["matrix"]).reshape(4,4)})
            if ("children" in node):
                children = []
                for child in node["children"]:
                    children.append(parseNode(gltfdata["nodes"][child], gltfdata))
                tempnode.update({"nodes": children})
                del tempnode["children"]
            elif ("camera" in node):
                pass
                # todo camera
            elif ("mesh" in node):
                tempnode.update({"mesh": gltfdata["meshes"][node["mesh"]]})
            return tempnode

        scenes = []
        accessors = []
        with open(filename) as modelfile:
            gltfdata = json.load(modelfile)
            for scene in gltfdata["scenes"]:
                if("nodes" in scene):
                    nodes=[]
                    for node in scene["nodes"]:
                        tempnode = gltfdata["nodes"][node]
                        nodes.append(parseNode(tempnode, gltfdata))
                    scenes.append(nodes)
            for accessor in gltfdata["accessors"]:
                accessor.update({"bufferView": gltfdata["bufferViews"][accessor["bufferView"]]})
                accessors.append(accessor)
        self.scenes = scenes
        self.accessors = accessors
        self.buffers = gltfdata["buffers"]
        self.materials = gltfdata["materials"]
    
    def getNode(self, scene, index):
        return self.scenes[scene][index]
    
    def meshesFromNode(rootnode):
        meshlist = []
        if ("matrix" in rootnode):
            rootmatrix = rootnode["matrix"]
        else:
            rootmatrix = None
        def delve(node, mat):
            if "nodes" in node:
                for tempnode in node["nodes"]:
                    if (not(mat is None)):
                        delve(tempnode, np.matmul(mat, tempnode["matrix"]))
                    else:
                        delve(tempnode, None)
            elif "mesh" in node:
                meshinfo = {"mesh": node["mesh"]}
                if (not(mat is None)):
                    meshinfo.update({"matrix": mat})
                meshlist.append(meshinfo)
        delve(rootnode, rootmatrix)
        return meshlist
    
    def meshtoVAO(self, meshPart, shader):
        positionAccessorId = meshPart["attributes"]["POSITION"]
        positionAccessor = self.accessors[positionAccessorId]

        vao = glGenVertexArrays(2)
        glBindVertexArray(vao[0])
        vbo = glGenBuffers(2)
        glBindBuffer(positionAccessor["bufferView"]["target"], vbo[0])

        position = glGetAttribLocation(shader, 'position')
        glEnableVertexAttribArray(position)

        initialpos = 0
        if "byteOffset" in positionAccessor["bufferView"]:
            initialpos = positionAccessor["bufferView"]["byteOffset"]

        index = position
        size = 3
        type = positionAccessor["componentType"]
        normalized = False
        if(not ("byteStride" in positionAccessor["bufferView"])):
            stride = 0
        else:
            stride = positionAccessor["bufferView"]["byteStride"]
        pointer = GLvoidp(initialpos)
        glVertexAttribPointer(index, size, type, normalized, stride, pointer)

        if (not "f32" in self.buffers[positionAccessor["bufferView"]["buffer"]]):
            buffer = np.fromfile(self.buffers[positionAccessor["bufferView"]["buffer"]]["uri"], dtype=np.float32)
            self.buffers[positionAccessor["bufferView"]["buffer"]].update({"f32": buffer})
        
        target = positionAccessor["bufferView"]["target"]
        data = self.buffers[positionAccessor["bufferView"]["buffer"]]["f32"]
        usage = GL_STATIC_DRAW
        glBufferData(target, data, usage)
        
        if "NORMAL" in meshPart["attributes"]:
            normalAccessorId = meshPart["attributes"]["NORMAL"]
            normalAccessor = self.accessors[normalAccessorId]
            glBindVertexArray(vao[0])
            normal = glGetAttribLocation(shader, 'normal')
            glEnableVertexAttribArray(normal)
            initialpos = 0
            if "byteOffset" in normalAccessor["bufferView"]:
                initialpos = normalAccessor["bufferView"]["byteOffset"]
            if "byteOffset" in normalAccessor:
                initialpos += normalAccessor["byteOffset"]

            if(not ("byteStride" in normalAccessor["bufferView"])):
                stride = 0
            else:
                stride = normalAccessor["bufferView"]["byteStride"]
            glVertexAttribPointer(normal, 3, normalAccessor["componentType"], False, stride, GLvoidp(initialpos))
            glBufferData(normalAccessor["bufferView"]["target"],  self.buffers[normalAccessor["bufferView"]["buffer"]]["f32"], GL_STATIC_DRAW)

        glBindVertexArray(0)
        #glDisableVertexAttribArray(position)
        #glDisableVertexAttribArray(normal)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return vao
    
    def getIndices(self, meshPart):
        indicesAccessorId = meshPart["indices"]
        indicesAccessor = self.accessors[indicesAccessorId]
        if(indicesAccessor["componentType"] not in [5123, 5125]):
            raise Exception("indices aren't in uint format!")
        elif (indicesAccessor["componentType"] == 5123):
            bytespec = 2
            dtype = "ushort"
            if (not dtype in self.buffers[indicesAccessor["bufferView"]["buffer"]]):
                buffer = np.fromfile(self.buffers[indicesAccessor["bufferView"]["buffer"]]["uri"], dtype=np.ushort)
                self.buffers[indicesAccessor["bufferView"]["buffer"]].update({dtype: buffer})
        elif (indicesAccessor["componentType"] == 5125):
            bytespec = 4
            dtype = "uint"
            if (not dtype in self.buffers[indicesAccessor["bufferView"]["buffer"]]):
                buffer = np.fromfile(self.buffers[indicesAccessor["bufferView"]["buffer"]]["uri"], dtype=np.uint32)
                self.buffers[indicesAccessor["bufferView"]["buffer"]].update({dtype: buffer})
        fromidx = int(indicesAccessor["bufferView"]["byteOffset"]/bytespec)
        toidx = int((indicesAccessor["bufferView"]["byteOffset"]/bytespec)+indicesAccessor["count"])
        indices = self.buffers[indicesAccessor["bufferView"]["buffer"]][dtype][fromidx:toidx]
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices)*bytespec, indices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        return vbo
