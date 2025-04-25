# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Srt(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.header_len = self._io.read_u4le()
        self.header = self._io.read_bytes((self.header_len * 128))
        self.num_trkparts = self._io.read_u4le()
        self.trkparts = []
        for i in range(self.num_trkparts):
            self.trkparts.append(Srt.Trkpart(self._io, self, self._root))

        self.num_decoparts = self._io.read_u4le()
        self.decoparts = []
        for i in range(self.num_decoparts):
            self.decoparts.append(Srt.Decopart(self._io, self, self._root))

        self.num_pathpoints = self._io.read_u4le()
        self.pathpoints = []
        for i in range(self.num_pathpoints):
            self.pathpoints.append(Srt.Coords(self._io, self, self._root))

        self.num_intropoints = self._io.read_u4le()
        self.intropoints = []
        for i in range(self.num_intropoints):
            self.intropoints.append(Srt.Coords(self._io, self, self._root))

        self.num_sec5 = self._io.read_u4le()
        self.sec5 = []
        for i in range(self.num_sec5):
            self.sec5.append(Srt.Coords(self._io, self, self._root))

        self.num_mainpoints = self._io.read_u4le()
        self.mainpoints = []
        for i in range(self.num_mainpoints):
            self.mainpoints.append(Srt.Coords(self._io, self, self._root))

        self.num_playerpos = self._io.read_u4le()
        self.playerpos = Srt.PlayerposT(self._io, self, self._root)
        self.num_replaypos = self._io.read_u4le()
        if self.num_replaypos < 65535:
            self.replaypos = []
            for i in range(self.num_replaypos):
                self.replaypos.append(Srt.Coords(self._io, self, self._root))


        self.num_sec9 = self._io.read_u4le()
        if self.num_sec9 < 65535:
            self.sec9 = []
            for i in range(((self.num_sec9 - 1) * 3)):
                self.sec9.append(self._io.read_u2le())



    class Trkvtx(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_s2le()
            self.y = self._io.read_s2le()
            self.z = self._io.read_s2le()
            self.r = self._io.read_u2le()
            self.g = self._io.read_u2le()
            self.b = self._io.read_u2le()


    class Trkpart(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_s4le()
            self.y = self._io.read_s4le()
            self.z = self._io.read_s4le()
            self.clip = self._io.read_u4le()
            self.num_vtxs = self._io.read_u4le()
            self.vtxs = []
            for i in range(self.num_vtxs):
                self.vtxs.append(Srt.Trkvtx(self._io, self, self._root))

            self.num_faces = self._io.read_u4le()
            self.faces = []
            for i in range(self.num_faces):
                self.faces.append(Srt.Trkface(self._io, self, self._root))

            self.objs = []
            i = 0
            while True:
                _ = Srt.Trkobj(self._io, self, self._root)
                self.objs.append(_)
                if _.objtype == -1:
                    break
                i += 1


    class Coords(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_s4le()
            self.y = self._io.read_s4le()
            self.z = self._io.read_s4le()


    class Decovtx(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_s2le()
            self.y = self._io.read_s2le()
            self.z = self._io.read_s2le()
            self.r = self._io.read_u1()
            self.g = self._io.read_u1()
            self.b = self._io.read_u1()
            self.unused = self._io.read_bytes(1)


    class Decopart(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.clip = self._io.read_bytes(16)
            self.x = self._io.read_s4le()
            self.y = self._io.read_s4le()
            self.z = self._io.read_s4le()
            self.unk = self._io.read_bytes(6)
            self.num_tris = self._io.read_u4le()
            self.tris = []
            for i in range(self.num_tris):
                self.tris.append(Srt.Decotri(self._io, self, self._root))

            self.num_quads = self._io.read_u4le()
            self.quads = []
            for i in range(self.num_quads):
                self.quads.append(Srt.Decoquad(self._io, self, self._root))

            self.num_vtxs = self._io.read_u4le()
            self.vtxs = []
            for i in range(self.num_vtxs):
                self.vtxs.append(Srt.Decovtx(self._io, self, self._root))



    class PlayerposT(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.p1_end = Srt.Coords(self._io, self, self._root)
            self.p2_end = Srt.Coords(self._io, self, self._root)
            self.p3_end = Srt.Coords(self._io, self, self._root)
            self.p4_end = Srt.Coords(self._io, self, self._root)
            self.p5_end = Srt.Coords(self._io, self, self._root)
            self.p1_start = Srt.Coords(self._io, self, self._root)
            self.p2_start = Srt.Coords(self._io, self, self._root)
            self.p3_start = Srt.Coords(self._io, self, self._root)
            self.p4_start = Srt.Coords(self._io, self, self._root)
            self.p5_start = Srt.Coords(self._io, self, self._root)
            self.tt_end = Srt.Coords(self._io, self, self._root)


    class Decotri(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.a = self._io.read_u2le()
            self.b = self._io.read_u2le()
            self.c = self._io.read_u2le()
            self.ta_x = self._io.read_u1()
            self.ta_y = self._io.read_u1()
            self.tb_x = self._io.read_u1()
            self.tb_y = self._io.read_u1()
            self.tc_x = self._io.read_u1()
            self.tc_y = self._io.read_u1()
            self.tpage = self._io.read_u4le()


    class Trkface(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.tpage = self._io.read_u2le()
            self.ta_x = self._io.read_u1()
            self.ta_y = self._io.read_u1()
            self.tb_x = self._io.read_u1()
            self.tb_y = self._io.read_u1()
            self.tc_x = self._io.read_u1()
            self.tc_y = self._io.read_u1()
            self.td_x = self._io.read_u1()
            self.td_y = self._io.read_u1()
            self.unused = self._io.read_bytes(2)


    class Trkobj(KaitaiStruct):
        """Almost always just rings."""
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.objtype = self._io.read_s4le()
            if self.objtype != -1:
                self.x = self._io.read_s4le()

            if self.objtype != -1:
                self.y = self._io.read_s4le()

            if self.objtype != -1:
                self.z = self._io.read_s4le()



    class Decoquad(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.a = self._io.read_u2le()
            self.b = self._io.read_u2le()
            self.c = self._io.read_u2le()
            self.d = self._io.read_u2le()
            self.ta_x = self._io.read_u1()
            self.ta_y = self._io.read_u1()
            self.tb_x = self._io.read_u1()
            self.tb_y = self._io.read_u1()
            self.tc_x = self._io.read_u1()
            self.tc_y = self._io.read_u1()
            self.td_x = self._io.read_u1()
            self.td_y = self._io.read_u1()
            self.tpage = self._io.read_u4le()



