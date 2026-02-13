import sqlite3


def test_apply_mesh_materials_and_part_attributes():
    from ..shared import db_patcher as dbp

    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()

    # create minimal tables
    cur.execute(
        'CREATE TABLE materials (material_id INTEGER PRIMARY KEY, name TEXT)')
    cur.execute(
        'CREATE TABLE meshes (mesh INTEGER PRIMARY KEY, material_id INTEGER)')
    cur.execute(
        'CREATE TABLE parts (mesh INTEGER, part INTEGER, attributes TEXT)')

    # ensure meshes rows exist so UPDATE can affect them
    cur.execute('INSERT INTO meshes (mesh, material_id) VALUES (1, NULL)')
    cur.execute('INSERT INTO meshes (mesh, material_id) VALUES (2, NULL)')

    # apply materials
    material_info = {1: 'mat_a', 2: 'mat_b'}
    dbp.apply_mesh_materials(cur, material_info)

    cur.execute('SELECT material_id, name FROM materials ORDER BY material_id')
    rows = cur.fetchall()
    assert rows == [(1, 'mat_a'), (2, 'mat_b')]

    # meshes table should have been updated
    cur.execute('SELECT mesh, material_id FROM meshes ORDER BY mesh')
    rows = cur.fetchall()
    assert rows == [(1, 1), (2, 2)]

    # apply part attributes
    part_attrs = {(1, 0): ['a', 'b'], (2, 1): ['x']}
    # ensure parts rows exist to be updated
    cur.execute('INSERT INTO parts (mesh, part, attributes) VALUES (1, 0, "")')
    cur.execute('INSERT INTO parts (mesh, part, attributes) VALUES (2, 1, "")')
    dbp.apply_part_attributes(cur, part_attrs)

    cur.execute('SELECT mesh, part, attributes FROM parts ORDER BY mesh, part')
    rows = cur.fetchall()
    assert rows == [(1, 0, 'a,b'), (2, 1, 'x')]
