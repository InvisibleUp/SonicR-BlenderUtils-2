# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Srm(KaitaiStruct):
    """Sonic R Character Model."""
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.grps = []
        i = 0
        while not self._io.is_eof():
            self.grps.append(Srm.Group(self._io, self, self._root))
            i += 1


    class Group(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.num_vtxs = self._io.read_u4le()
            if self.num_vtxs != 4294967295:
                self.vtxs = []
                for i in range(self.num_vtxs):
                    self.vtxs.append(Srm.Vertex(self._io, self, self._root))


            if self.num_vtxs != 4294967295:
                self.num_tris = self._io.read_u4le()

            if self.num_vtxs != 4294967295:
                self.tris = []
                for i in range(self.num_tris):
                    self.tris.append(Srm.Tri(self._io, self, self._root))


            if self.num_vtxs != 4294967295:
                self.num_quads = self._io.read_u4le()

            if self.num_vtxs != 4294967295:
                self.quads = []
                for i in range(self.num_quads):
                    self.quads.append(Srm.Quad(self._io, self, self._root))




    class Vertex(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_s2le()
            self.y = self._io.read_s2le()
            self.z = self._io.read_s2le()
            self.unk_a = self._io.read_s2le()
            self.unk_b = self._io.read_s2le()
            self.unk_c = self._io.read_s2le()
            self.unk_d = self._io.read_s2le()
            self.unk_e = self._io.read_s2le()


    class Tri(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.vtx_a = self._io.read_u2le()
            self.vtx_b = self._io.read_u2le()
            self.vtx_c = self._io.read_u2le()
            self.ta_x = self._io.read_u1()
            self.ta_y = self._io.read_u1()
            self.tb_x = self._io.read_u1()
            self.tb_y = self._io.read_u1()
            self.tc_x = self._io.read_u1()
            self.tc_y = self._io.read_u1()
            self.unk = self._io.read_u4le()


    class Quad(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.vtx_a = self._io.read_u2le()
            self.vtx_b = self._io.read_u2le()
            self.vtx_c = self._io.read_u2le()
            self.vtx_d = self._io.read_u2le()
            self.ta_x = self._io.read_u1()
            self.ta_y = self._io.read_u1()
            self.tb_x = self._io.read_u1()
            self.tb_y = self._io.read_u1()
            self.tc_x = self._io.read_u1()
            self.tc_y = self._io.read_u1()
            self.td_x = self._io.read_u1()
            self.td_y = self._io.read_u1()
            self.unk = self._io.read_u4le()



