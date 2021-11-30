#!/usr/bin/env python3

import sqlite3


def kmalloc_size(sz):
    bins = [8,16,32,64,96,128,192,256,512,1024,2048,4096,8192]
    for b in bins:
        if int(sz) < b:
            return 'kmalloc-%d' % b
    return 'unknown'


def find_structs(size, offsets: list):
    fields = [
        "struct.id",
        "struct.name",
        "struct.size",
        "struct.size_kmalloc",
        "struct.object_filepath",
        "struct.definition",
        "struct_members.name",
        "struct_members.type",
        "struct_members.general_type",
        "struct_members.size",
        "struct_members.offset"
    ]
    query = ("SELECT " + ', '.join(fields) + " FROM struct LEFT JOIN struct_members ON struct_members.struct_id=struct.id WHERE struct.size_kmalloc=? AND (struct_members.general_type='pointer' OR struct_members.general_type='function') AND ")

    args = [kmalloc_size(int(size))]
    first = True
    for offset in map(int, offsets):
        assert offset <= size, 'offset %d too large for chunk of size %d' % (offset, size)
        if not first:
            query += ' OR '
        query += '(struct_members.offset<=? AND (struct_members.offset+struct_members.size>=?))'
        args.append(offset)
        args.append(offset)
        if first:
            first = False
    query += ';'

    conn = sqlite3.connect('file:structdb.db?mode=ro', uri=True)
    c = conn.cursor()
    x = c.execute(query, args)
    structs = dict()
    for result in x.fetchall():
        result = dict(zip(fields, result))
        sid = result['struct.id']
        if sid not in structs:
            structs[sid] = {
                'name': result['struct.name'],
                'size': result['struct.size'],
                'size_kmalloc': result['struct.size_kmalloc'],
                'object_filepath': result['struct.object_filepath'],
                'definition': result['struct.definition'],
                'members': list()
            }

        structs[sid]['members'].append({
            'name': result['struct_members.name'],
            'type': result['struct_members.type'],
            'general_type': result['struct_members.general_type'],
            'size': result['struct_members.size'],
            'offset': result['struct_members.offset']
        })

    return structs


if __name__ == '__main__':
    import sys
    assert len(sys.argv) >= 3, '%s <chunksize> [offsets...]' % sys.argv[0]

    size = int(sys.argv[1])
    offsets = list(map(int, sys.argv[2:]))

    print('Searching for structs of size %d (%s) containing pointers at offsets %r' % (size, kmalloc_size(size), offsets))
    for struct in find_structs(size, offsets).values():
        print(f'{struct["size_kmalloc"]} ({struct["size"]} bytes)\t :: struct {struct["name"]}\t\t ({struct["object_filepath"]})')
        for member in struct['members']:
            print(f'\t.{member["name"]}\t@ offset {member["offset"]} size {member["size"]}')
        print()

