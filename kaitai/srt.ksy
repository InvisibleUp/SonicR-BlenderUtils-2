meta:
  id: srt
  endian: le
seq:
  - id: header_len
    type: u4
  - id: header
    doc: unused
    size: header_len * 128
    
  - id: trkpart_cnt
    type: u4
  - id: trkparts
    type: trkpart
    repeat: expr
    repeat-expr: trkpart_cnt
    
  - id: decopart_cnt
    type: u4
  - id: decoparts
    type: decopart
    repeat: expr
    repeat-expr: decopart_cnt
    
  - id: pathpoint_cnt
    type: u4
  - id: pathpoints
    doc: Paths for all routes
    type: coords
    repeat: expr
    repeat-expr: pathpoint_cnt
    
  - id: intropoint_cnt
    type: u4
  - id: intropoints
    doc: Path the intro camera takes. Not position data.
    type: coords
    repeat: expr
    repeat-expr: intropoint_cnt
    
  - id: sec5_cnt
    type: u4
  - id: sec5
    doc: Section 5 (unknown)
    type: coords
    repeat: expr
    repeat-expr: sec5_cnt
  
  - id: mainpoint_cnt
    type: u4
  - id: mainpoints
    doc: Path across the "main route" of the track
    type: coords
    repeat: expr
    repeat-expr: mainpoint_cnt
    
  - id: playerpos_cnt
    type: u4
  - id: playerpos
    doc: Player start/end locations.
    type: playerpos_t
    
  - id: replaypos_cnt
    type: u4
  - id: replaypos
    doc: Replay camera positions
    type: coords
    repeat: expr
    repeat-expr: replaypos_cnt
    
  - id: sec9_cnt
    type: u4
  - id: sec9
    doc: Section 9 (unknown)
    type: u2
    repeat: expr
    repeat-expr: (sec9_cnt-1)*3
    
types:
  trkpart:
    seq:
    - id: x
      type: s4
    - id: y
      type: s4
    - id: z
      type: s4
    - id: clip
      type: u4
    - id: vtx_cnt
      type: u4
    - id: vtxs
      type: trkvtx
      repeat: expr
      repeat-expr: vtx_cnt
    - id: face_cnt
      type: u4
    - id: faces
      type: trkface
      repeat: expr
      repeat-expr: face_cnt
    - id: objs
      type: trkobj
      repeat: until
      repeat-until: _.objtype == -1
  trkvtx:
    seq:
    - id: x
      type: s2
    - id: y
      type: s2
    - id: z
      type: s2
    - id: r
      type: u2
    - id: g
      type: u2
    - id: b
      type: u2
  trkface:
    seq:
    - id: tpage
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
    - id: unused
      size: 2
  trkobj:
    doc: Almost always just rings
    seq:
    - id: objtype
      type: s4
    - id: x
      type: s4
      if: objtype != -1
    - id: y
      type: s4
      if: objtype != -1
    - id: z
      type: s4
      if: objtype != -1
  decopart:
    seq:
    - id: clip
      size: 16
    - id: x
      type: s4
    - id: y
      type: s4
    - id: z
      type: s4
    - id: unk
      size: 6
    - id: tri_cnt
      type: u4
    - id: tris
      type: decotri
      repeat: expr
      repeat-expr: tri_cnt
    - id: quad_cnt
      type: u4
    - id: quads
      type: decoquad
      repeat: expr
      repeat-expr: quad_cnt
    - id: vtx_cnt
      type: u4
    - id: vtxs
      type: decovtx
      repeat: expr
      repeat-expr: vtx_cnt
  decotri:
    seq:
    - id: a
      type: u2
    - id: b
      type: u2
    - id: c
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
    - id: tpage
      type: u4
  decoquad:
    seq:
    - id: a
      type: u2
    - id: b
      type: u2
    - id: c
      type: u2
    - id: d
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
    - id: tpage
      type: u4
  decovtx:
    seq:
    - id: x
      type: s2
    - id: y
      type: s2
    - id: z
      type: s2
    - id: r
      type: u1
    - id: g
      type: u1
    - id: b
      type: u1
    - id: unused
      size: 1
  coords:
    seq:
      - id: x
        type: s4
      - id: y
        type: s4
      - id: z
        type: s4
  playerpos_t:
    seq:
      - id: p1_end
        type: coords
      - id: p2_end
        type: coords
      - id: p3_end
        type: coords
      - id: p4_end
        type: coords
      - id: p5_end
        type: coords
      - id: p1_start
        type: coords
      - id: p2_start
        type: coords
      - id: p3_start
        type: coords
      - id: p4_start
        type: coords
      - id: p5_start
        type: coords
      - id: tt_end
        type: coords