#!/usr/bin/env python3

import sqlite3
import re
import util

###

conn = sqlite3.connect('structdb.db') 
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS struct;')
c.execute('DROP TABLE IF EXISTS struct_members;')
c.execute('CREATE TABLE struct (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, object_filepath TEXT NOT NULL, size_kmalloc TEXT, size INTEGER, members INTEGER, definition TEXT);')
c.execute('CREATE TABLE struct_members (id INTEGER PRIMARY KEY AUTOINCREMENT, struct_id INTEGER NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL, general_type TEXT NOT NULL, size INTEGER, offset INTEGER);')
conn.commit()


###

fd = open('structs.txt')

structs = list()

cur_struct = None
cur_object = None
build = ''
while og_line := fd.readline():
    line = og_line.strip()
    if not line:
        build += og_line
        continue
    
    if not cur_struct:
        struct_defs = re.findall(r'struct (.*) {', line)
        if struct_defs:
            # [path to object, struct name, [total size, number of members], string definition of struct, members]
            cur_struct = [cur_object, struct_defs[0], [None, None], '', []]
            build = og_line
        elif line.startswith('NOW PARSING '):
            cur_object = line[len('NOW PARSING '):].strip()
        continue

    if line.startswith('};') or line.startswith('} __attribute__((__aligned__('):
        build += og_line
        cur_struct[3] = build
        sd = [0, 0] if not cur_struct[2][1] else cur_struct[2]
        c.execute('INSERT INTO struct VALUES (NULL, ?, ?, ?, ?, ?, ?);', [cur_struct[1], cur_struct[0], util.kmalloc_size(int(sd[0])), int(sd[0]), int(sd[1]), cur_struct[3]])
        
        rowid = c.lastrowid
        for m in cur_struct[4]:
            dtype = m[1] + m[3] + m[4]
            c.execute('INSERT INTO struct_members VALUES (NULL, ?, ?, ?, ?, ?, ?);', [rowid, m[2], dtype, m[0], int(m[6]), int(m[5])])
        
        conn.commit()
        structs.append(cur_struct)
        cur_struct = None
        continue

    size_defs = re.findall(r'/\* size: (\d+), cachelines: \d+, members: (\d+) \*/', line)
    if size_defs:
        cur_struct[2] = size_defs[0]
        build += og_line
        continue

    build += og_line

    if line.startswith('/*'):
        continue

    matches = re.findall(r'(.*?) +([\w:]+)\s*(\[\d*\])?(\s*__attribute__\(\(__aligned__\(\d+\)\)\))?; +/\*.*(\d+) +(\d+).*\*/', line)
    if matches:
        dtype = 'pointer' if matches[0][0].strip().endswith('*') else 'data'
        cur_struct[4].append([dtype] + list(matches[0]))
        continue

    matches = re.findall(r'(.*?) *\(\*(\w+)\)\((.*)\);.*/\*.*(\d+).*(\d+).*\*/', line)
    if matches:
        matches = matches[0]
        cur_struct[4].append(['function', matches[1] + ' ' + '(' + matches[3] + ')', matches[2], '', '', matches[3], matches[4]])
        continue

    #print(line)

fd.close()
