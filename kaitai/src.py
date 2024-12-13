# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Src(KaitaiStruct):
    """Sonic R Collision Format."""
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.sec1_pos = self._io.read_u4le()
        self.sec2_pos = self._io.read_u4le()
        self.sec3_pos = self._io.read_u4le()
        self.sec4_pos = self._io.read_u4le()
        self.sec5_pos = self._io.read_u4le()
        self.sec6_pos = self._io.read_u4le()
        self.sec7_pos = self._io.read_u4le()
        self.sec8_pos = self._io.read_u4le()
        self.sec9_pos = self._io.read_u4le()
        self.sec10_pos = self._io.read_u4le()
        self.var1 = self._io.read_u4le()
        self.var2 = self._io.read_u4le()
        self.var3 = self._io.read_u4le()
        self.var4 = self._io.read_u4le()
        self.var5 = self._io.read_u4le()
        self.var6 = self._io.read_u4le()
        self.var7 = self._io.read_u4le()
        self.var8 = self._io.read_u4le()
        self.var9 = self._io.read_u4le()
        self.var10 = self._io.read_s4le()
        self.var11 = self._io.read_s4le()
        self.var12 = self._io.read_s4le()
        self.var13 = self._io.read_s4le()

    class Sec4T(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.unk1 = self._io.read_u2le()
            self.unk2 = self._io.read_u2le()
            self.unk3 = self._io.read_u2le()
            self.unk4 = self._io.read_u2le()
            self.unk5 = self._io.read_u2le()
            self.unk6 = self._io.read_u2le()
            self.unk7 = self._io.read_u2le()
            self.unk8 = self._io.read_u2le()


    class Sec2T(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.a = self._io.read_s1()
            self.b = self._io.read_s1()
            self.c = self._io.read_s1()
            self.d = self._io.read_s1()


    class Coord(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_s2le()
            self.y = self._io.read_s2le()
            self.z = self._io.read_s2le()


    class Sec3T(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u4le()
            self.x = self._io.read_s2le()
            self.z = self._io.read_s2le()


    class Sec9T(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.idx1 = self._io.read_u1()
            self.idx2 = self._io.read_u1()


    @property
    def sec4(self):
        """Something related to walls."""
        if hasattr(self, '_m_sec4'):
            return self._m_sec4

        _pos = self._io.pos()
        self._io.seek(self.sec4_pos)
        self._m_sec4 = []
        for i in range((self.sec5_pos - self.sec4_pos) // 16):
            self._m_sec4.append(Src.Sec4T(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_sec4', None)

    @property
    def sec2(self):
        """Normals for heightmap?."""
        if hasattr(self, '_m_sec2'):
            return self._m_sec2

        _pos = self._io.pos()
        self._io.seek(self.sec2_pos)
        self._m_sec2 = []
        for i in range((self.sec3_pos - self.sec2_pos) // 4):
            self._m_sec2.append(Src.Sec2T(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_sec2', None)

    @property
    def sec5(self):
        """Wall heightmap."""
        if hasattr(self, '_m_sec5'):
            return self._m_sec5

        _pos = self._io.pos()
        self._io.seek(self.sec5_pos)
        self._m_sec5 = []
        for i in range((self.sec6_pos - self.sec5_pos) // 6):
            self._m_sec5.append(Src.Coord(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_sec5', None)

    @property
    def sec1(self):
        """Floor heightmap."""
        if hasattr(self, '_m_sec1'):
            return self._m_sec1

        _pos = self._io.pos()
        self._io.seek(self.sec1_pos)
        self._m_sec1 = []
        for i in range((self.sec2_pos - self.sec1_pos) // 6):
            self._m_sec1.append(Src.Coord(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_sec1', None)

    @property
    def sec6(self):
        """Loop metadata."""
        if hasattr(self, '_m_sec6'):
            return self._m_sec6

        _pos = self._io.pos()
        self._io.seek(self.sec6_pos)
        self._m_sec6 = []
        for i in range((self.sec7_pos - self.sec6_pos) // 2):
            self._m_sec6.append(self._io.read_s2le())

        self._io.seek(_pos)
        return getattr(self, '_m_sec6', None)

    @property
    def sec8(self):
        """Lookup table 1 (seems to be 32x32)."""
        if hasattr(self, '_m_sec8'):
            return self._m_sec8

        _pos = self._io.pos()
        self._io.seek(self.sec8_pos)
        self._m_sec8 = []
        for i in range((self.sec9_pos - self.sec8_pos) // 2):
            self._m_sec8.append(self._io.read_u2le())

        self._io.seek(_pos)
        return getattr(self, '_m_sec8', None)

    @property
    def sec10(self):
        """Unknown."""
        if hasattr(self, '_m_sec10'):
            return self._m_sec10

        _pos = self._io.pos()
        self._io.seek(self.sec10_pos)
        self._m_sec10 = []
        i = 0
        while not self._io.is_eof():
            self._m_sec10.append(self._io.read_u2le())
            i += 1

        self._io.seek(_pos)
        return getattr(self, '_m_sec10', None)

    @property
    def sec3(self):
        """Some sort of 2D point map."""
        if hasattr(self, '_m_sec3'):
            return self._m_sec3

        _pos = self._io.pos()
        self._io.seek(self.sec3_pos)
        self._m_sec3 = []
        for i in range((self.sec4_pos - self.sec3_pos) // 8):
            self._m_sec3.append(Src.Sec3T(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_sec3', None)

    @property
    def sec7(self):
        """Loop point data (plus some other stuff?)."""
        if hasattr(self, '_m_sec7'):
            return self._m_sec7

        _pos = self._io.pos()
        self._io.seek(self.sec7_pos)
        self._m_sec7 = []
        for i in range((self.sec8_pos - self.sec7_pos) // 6):
            self._m_sec7.append(Src.Coord(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_sec7', None)

    @property
    def sec9(self):
        """Lookup table 2."""
        if hasattr(self, '_m_sec9'):
            return self._m_sec9

        _pos = self._io.pos()
        self._io.seek(self.sec9_pos)
        self._m_sec9 = []
        for i in range((self.sec10_pos - self.sec9_pos) // 8):
            self._m_sec9.append(Src.Sec9T(self._io, self, self._root))

        self._io.seek(_pos)
        return getattr(self, '_m_sec9', None)


