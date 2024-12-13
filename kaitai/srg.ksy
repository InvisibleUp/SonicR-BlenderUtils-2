meta:
  id: srg
  file-extension: grd
  endian: le
doc: Sonic R Character Vertex Colors
seq:
  - id: colors
    doc: Colors
    type: color
    repeat: eos
types:
  color:
    seq:
      - id: r
        type: u1
      - id: g
        type: u1
      - id: b
        type: u1

