#!/usr/bin/env python3


def kmalloc_size(sz):
    bins = [8,16,32,64,96,128,192,256,512,1024,2048,4096,8192]
    for b in bins:
        if int(sz) < b:
            return 'kmalloc-%d' % b
    return 'unknown'
