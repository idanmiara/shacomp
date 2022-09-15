#!/usr/bin/env python
import sys
import os
import hashlib


def chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
    hashobj = hash()
    file_object = open(filename, 'rb')

    if first_chunk_only:
        hashobj.update(file_object.read(1024))
    else:
        for chunk in chunk_reader(file_object):
            hashobj.update(chunk)
    hashed = hashobj.digest()

    file_object.close()
    return hashed


def check_for_duplicates(paths, hash=hashlib.sha1, do_delete=False):
    hashes_by_size = {}
    hashes_on_1k = {}
    hashes_full = {}

    total_count = 0
    print('step 1: making hash by size...')
    for path in paths:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if total_count % 100 == 0:
                    print('step 1: {}'.format(total_count))
                full_path = os.path.join(dirpath, filename)
                try:
                    # if the target is a symlink (soft one), this will 
                    # dereference it - change the value to the actual target file
                    full_path = os.path.realpath(full_path)
                    file_size = os.path.getsize(full_path)
                except (OSError,):
                    # not accessible (permissions, etc) - pass on
                    continue
                total_count += 1
                duplicate = hashes_by_size.get(file_size)

                if duplicate:
                    hashes_by_size[file_size].append(full_path)
                else:
                    hashes_by_size[file_size] = []  # create the list for this file size
                    hashes_by_size[file_size].append(full_path)

    print(total_count)
    print('unique file sizes: {}'.format(len(hashes_by_size)))

    total_count2 = 0
    print('step 2: making hash by 1k...')
    # For all files with the same file size, get their hash on the 1st 1024 bytes
    for __, files in hashes_by_size.items():
        if len(files) < 2:
            total_count2 += 1
            if total_count2 % 100 == 0:
                print('step 2: {}'.format(total_count2))
            continue    # this file size is unique, no need to spend cpy cycles on it

        for filename in files:
            total_count2 += 1
            if total_count2 % 100 == 0:
                print('step 2: {}'.format(total_count2))
            try:
                small_hash = get_hash(filename, first_chunk_only=True)
            except (OSError,):
                # the file access might've changed till the exec point got here 
                continue

            duplicate = hashes_on_1k.get(small_hash)
            if duplicate:
                hashes_on_1k[small_hash].append(filename)
            else:
                hashes_on_1k[small_hash] = []          # create the list for this 1k hash
                hashes_on_1k[small_hash].append(filename)

    print(total_count2)
    print('unique hashes_on_1k: {}'.format(len(hashes_on_1k)))

    dup_count = 0
    dup_deleted = 0
    total_count3 = 0
    print('step 3: calc full hash and find dups...')
    # For all files with the hash on the 1st 1024 bytes, get their hash on the full file - collisions will be duplicates
    for __, files in hashes_on_1k.items():
        if len(files) < 2:
            total_count3 += 1
            if total_count3 % 100 == 0:
                print('step 3: {}'.format(total_count3))
            continue    # this hash of first 1k file bytes is unique, no need to spend cpy cycles on it

        for filename in files:
            total_count3 += 1
            if total_count3 % 100 == 0:
                print('step 3: {}'.format(total_count3))
            try:
                full_hash = get_hash(filename, first_chunk_only=False)
            except (OSError,):
                # the file access might've changed till the exec point got here 
                continue

            duplicate = hashes_full.get(full_hash)
            if duplicate:
                print("Duplicate found: %s and %s" % (filename, duplicate))
                dup_count += 1
                if do_delete:
                    try:
                        os.remove(filename)
                        dup_deleted += 1
                    except (OSError,):
                        # not accessible (permissions, etc) - pass on
                        continue

            else:
                hashes_full[full_hash] = filename

    print(total_count3)
    print('unique hashes_full: {}'.format(len(hashes_full)))
    print('Total dups: {}, deleted: {}'.format(dup_count, dup_deleted))

    return dup_count


if __name__ == '__main__':
    if sys.argv[1:]:
        check_for_duplicates(sys.argv[1:])
    else:
        print("Please pass the paths to check as parameters to the script")