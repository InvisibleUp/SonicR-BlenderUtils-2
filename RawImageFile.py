from PIL import Image, ImageFile
from collections import namedtuple

def _accept(prefix: bytes) -> bool:
    return True

# as of now, only supports 256x256 textures