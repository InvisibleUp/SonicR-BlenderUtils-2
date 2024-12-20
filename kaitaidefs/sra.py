# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Sra(KaitaiStruct):
    """Sonic R Character Animation."""
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.num_limbs = self._io.read_u4le()
        self.frames = []
        i = 0
        while not self._io.is_eof():
            self.frames.append(Sra.Frame(self._io, self, self._root))
            i += 1


    class Frame(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.limbs = []
            for i in range(self._root.num_limbs):
                self.limbs.append(Sra.Limb(self._io, self, self._root))



    class Limb(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.tx = self._io.read_s4le()
            self.ty = self._io.read_s4le()
            self.tz = self._io.read_s4le()
            self.rx = self._io.read_s4le()
            self.ry = self._io.read_s4le()
            self.rz = self._io.read_s4le()



