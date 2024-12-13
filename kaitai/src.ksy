meta:
  id: src
  endian: le
doc: Sonic R Collision Format
seq:
  - id: sec1_pos
    type: u4
  - id: sec2_pos
    type: u4
  - id: sec3_pos
    type: u4
  - id: sec4_pos
    type: u4
  - id: sec5_pos
    type: u4
  - id: sec6_pos
    type: u4
  - id: sec7_pos
    type: u4
  - id: sec8_pos
    type: u4
  - id: sec9_pos
    type: u4
  - id: sec10_pos
    type: u4
  - id: var1
    type: u4
  - id: var2
    type: u4
  - id: var3
    type: u4
  - id: var4
    type: u4
  - id: var5
    type: u4
  - id: var6
    doc: Number of loop objects in level
    type: u4
  - id: var7
    type: u4
  - id: var8
    type: u4
  - id: var9
    doc: Number of items in section 9
    type: u4
  - id: var10
    doc: Course min X?
    type: s4
  - id: var11
    doc: Course min Z?
    type: s4
  - id: var12
    doc: Course max X?
    type: s4
  - id: var13
    doc: Course max Z?
    type: s4
types:
  coord:
    seq:
    - id: x
      type: s2
    - id: y
      type: s2
    - id: z
      type: s2
  sec2_t:
    seq:
    - id: a
      type: s1
    - id: b
      type: s1
    - id: c
      type: s1
    - id: d
      type: s1
  sec3_t:
    seq:
    - id: index
      type: u4
    - id: x
      type: s2
    - id: z
      type: s2
  sec4_t:
    seq:
    - id: unk1
      type: u2
    - id: unk2
      type: u2
    - id: unk3
      type: u2
    - id: unk4
      type: u2
    - id: unk5
      type: u2
    - id: unk6
      type: u2
    - id: unk7
      type: u2
    - id: unk8
      type: u2
  sec9_t:
    seq:
      - id: idx1
        type: u1
      - id: idx2
        type: u1
instances:
  sec1:
    doc: "Floor heightmap"
    pos: sec1_pos
    type: coord
    repeat: expr
    repeat-expr: (sec2_pos - sec1_pos) / 6
  sec2:
    doc: "Normals for heightmap?"
    pos: sec2_pos
    type: sec2_t
    repeat: expr
    repeat-expr: (sec3_pos - sec2_pos) / 4
  sec3:
    doc: "Some sort of 2D point map"
    pos: sec3_pos
    type: sec3_t
    repeat: expr
    repeat-expr: (sec4_pos - sec3_pos) / 8
  sec4:
    doc: "Something related to walls"
    pos: sec4_pos
    type: sec4_t
    repeat: expr
    repeat-expr: (sec5_pos - sec4_pos) / 16
  sec5:
    doc: "Wall heightmap"
    pos: sec5_pos
    type: coord
    repeat: expr
    repeat-expr: (sec6_pos - sec5_pos) / 6
  sec6:
    doc: "Loop metadata"
    pos: sec6_pos
    type: s2
    repeat: expr
    repeat-expr: (sec7_pos - sec6_pos) / 2
  sec7:
    doc: "Loop point data (plus some other stuff?)"
    pos: sec7_pos
    type: coord
    repeat: expr
    repeat-expr: (sec8_pos - sec7_pos) / 6
  sec8:
    doc: "Lookup table 1 (seems to be 32x32)"
    pos: sec8_pos
    type: u2
    repeat: expr
    repeat-expr: (sec9_pos - sec8_pos) / 2
  sec9:
    doc: "Lookup table 2"
    pos: sec9_pos
    type: sec9_t
    repeat: expr
    repeat-expr: (sec10_pos - sec9_pos) / 8
  sec10:
    doc: "Unknown"
    pos: sec10_pos
    type: u2
    repeat: eos
    
    