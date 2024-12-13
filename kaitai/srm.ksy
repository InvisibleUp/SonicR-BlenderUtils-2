meta:
  id: srm
  endian: le
doc: Sonic R Character Model
seq:
  - id: grps
    type: group
    repeat: eos
types:
  group:
    seq:
    - id: vtx_cnt
      doc: Number of vertices
      type: u4
    - id: vtxs
      doc: Vertices
      type: vertex
      repeat: expr
      repeat-expr: vtx_cnt
      if: vtx_cnt != 0xFFFFFFFF
    - id: tri_cnt
      doc: Number of triangles
      type: u4
      if: vtx_cnt != 0xFFFFFFFF
    - id: tris
      doc: Triangles
      type: tri
      repeat: expr
      repeat-expr: tri_cnt
      if: vtx_cnt != 0xFFFFFFFF
    - id: quad_cnt
      doc: Number of quads
      type: u4
      if: vtx_cnt != 0xFFFFFFFF
    - id: quads
      doc: Quads
      type: quad
      repeat: expr
      repeat-expr: quad_cnt
      if: vtx_cnt != 0xFFFFFFFF
  vertex:
    seq:
      - id: x
        type: s2
      - id: y
        type: s2
      - id: z
        type: s2
      - id: unk_a
        type: s2
      - id: unk_b
        type: s2
      - id: unk_c
        type: s2
      - id: unk_d
        type: s2
      - id: unk_e
        type: s2
  tri:
    seq:
      - id: vtx_a
        type: u2
      - id: vtx_b
        type: u2
      - id: vtx_c
        type: u2
      - id: ta_x
        type: u1
      - id: ta_y
        type: u1
      - id: tb_x
        type: u1
      - id: tb_y
        type: u1
      - id: tc_x
        type: u1
      - id: tc_y
        type: u1
      - id: unk
        type: u4
  quad:
    seq:
      - id: vtx_a
        type: u2
      - id: vtx_b
        type: u2
      - id: vtx_c
        type: u2
      - id: vtx_d
        type: u2
      - id: ta_x
        type: u1
      - id: ta_y
        type: u1
      - id: tb_x
        type: u1
      - id: tb_y
        type: u1
      - id: tc_x
        type: u1
      - id: tc_y
        type: u1
      - id: td_x
        type: u1
      - id: td_y
        type: u1
      - id: unk
        type: u4