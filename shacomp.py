import sys
import glob, re, fnmatch, os
import collections
import shutil

import numpy as np

from shacomp_helper import *


sha_kind = 'sha512'


def is_junk_file(filename):
    junk = ["thumbs.db", "desktop.ini", "picasa.ini", ".picasa.ini", "picasa.ini1", ".picasa.ini1"]
    return os.path.basename(filename).lower() in junk


def read_file(filename, d, d_ext, uniquelog=None, siglen=0):
    # with open(filename, encoding="utf-8-sig").read().decode("utf-8-sig") as f:
    with open(filename, mode='r', encoding="utf-8-sig") as f:
        print("{} ...".format(filename))
        valid_count = 0
        total_lines = 0
        junk_count = 0
        new_unique_count = 0
        if siglen == 0:
            siglen = 128
        delim = ' *'
        invalid = []
        for line in f:
            # line=line.rstrip('\n')
            line = line.strip()
            if line == '':
                continue
            total_lines += 1
            kv = line.split(delim, 1)
            if (len(kv) != 2) or (len(kv[0]) != siglen) or (len(kv[1]) == 0):
                invalid.append(line)
            else:
                key = kv[0].lower()
                val = kv[1]
                if is_junk_file(val):
                    junk_count += 1
                else:
                    # d.setdefault(key,[])
                    # d.append(val)
                    ext = os.path.splitext(val)[1]
                    d_ext[ext] += 1
                    valid_count += 1
                    if not val in d[key]:
                        d[key].append(val)
                        if len(d[key]) == 1:
                            new_unique_count += 1
                            if not (uniquelog is None):
                                uniquelog.append([key, val])
    # unique_count = len(d)
    invalid_count = len(invalid)
    verify_total = valid_count + invalid_count + junk_count
    print("valid: {}(unique: {} + dups: {}) + invalid: {} + junk: {} = total: {} entries, ({})".
          format(filename, valid_count, new_unique_count, valid_count - new_unique_count,
                 invalid_count, junk_count, total_lines, verify_total == verify_total))
    print('ext list:')
    print(d_ext)
    dict_stats(d)


# def read_out_file(d, filename):
#     with open(filename) as f:
#         total_lines=0
#         for line in f:
#             line=line.strip().rstrip('\n')
#             if line=='':
#                 continue
#             total_lines+=1
#             kv=re.split(r'\t+', line)
#             key = kv[0]
#             val = kv[1]
#             d[key] = val
#     print("{0}: base lines: {1}".format(filename,total_lines))
#
# def write_file(d, filename):
#     od = collections.OrderedDict(sorted(d.items()))
#     count = len(od)
#     if count>0:
#         text_file = open(filename, "w")
#         for k, v in od.iteritems():
#             s='{0}\t{1}\n'.format(k,v)
#             text_file.write(s)
#         print("Writing: {0}: {1} lines".format(filename,count))
#         text_file.close()
#     else:
#         print("No items found!")


def read_write(dir_name, master, ext='.' + sha_kind):
    # d = {}
    # key = hash
    # value = list of files
    d = collections.defaultdict(list)
    d_ext = collections.Counter()
    # c = collections.Counter(value for values in d.itervalues() for value in values)
    # dir=os.getcwd()
    if dir_name != '':
        os.chdir(dir_name)

    base_file = master + ext
    filename = base_file
    # if a base file is provided, read it, otherwise continue to read in alphabetical order
    if filename != '':
        s = os.path.join(dir_name, filename)
        if os.path.isfile(s):
            print("0:")
            read_file(s, d, d_ext)
            print()
            # s = os.path.join(dir,filename+"-uniques"+ext)
            # save_tup_list(unique_log, s)

    in_pattern = '*' + ext
    # for filename in re.compile(fnmatch.translate(in_pattern), re.IGNORECASE):

    sha_files_count = 1
    for filename in sorted(glob.glob(in_pattern)):
        if filename == base_file or ("unique" in filename) or ("ignore" in filename):
            continue
        print('{}:'.format(sha_files_count))
        s = os.path.join(dir_name, filename)
        unique_log = []
        read_file(s, d, d_ext, unique_log)
        if len(unique_log) > 0:
            s = os.path.join(dir_name, os.path.splitext(filename)[0] + "-uniques" + ext)
            save_tup_list(unique_log, s)
        # write_file(d, os.path.join(dir, outfile))
        print("{} new unique files from file:{}, base file:{}".format(len(unique_log), filename, base_file))
        print()
        sha_files_count += 1

    print("\n---- finished loading {} sha files ---- \n".format(sha_files_count))

    l = get_unique_tup_list_from_dict(d)
    s = os.path.join(dir_name, "uniques" + ext)
    save_tup_list(l, s)

    return d


def delete_duplicates(dir_name, d, verify_sha=True, verify_sha_allcopies=True):
    print('delete duplicates from dir: {}'.format(dir_name))
    total = 0
    missing = []
    sha_err = []
    sha_ok = []
    firsts = []
    deleted = []
    for key, value in d.items():
        copy_found = False
        is_first = True
        for f in value:
            f = normpath1(f)
            filename = os.path.join(dir_name, f)
            curr_found = os.path.isfile(filename)
            total += 1
            if curr_found:
                sha_hex = sha512_file(filename)
                sha_verified = key == sha_hex
                if sha_verified:
                    sha_ok.append(filename)
                    if is_first:
                        firsts.append(filename)
                    is_first = False
                else:
                    sha_err.append(filename)
                    print('err #{:5d}: {}'.format(len(sha_err), filename))
            else:
                missing.append(filename)
                print('mis #{:5d}: {}'.format(len(missing), filename))
                sha_verified = False

            if copy_found:
                # found a concrete duplicate
                if sha_verified:
                    os.remove(filename)
                    deleted.append(filename)
                    print('del #{:5d}: {}'.format(len(deleted), filename))
            else:
                copy_found = sha_verified

    print('total: {} = [missing: {}; sha_err: {}; sha_ok: {} =(firsts: {}; deleted: {})]'.
          format(total, len(missing), len(sha_err), len(sha_ok), len(firsts), len(deleted)))


def restore_duplicates(dir_name, d):
    total = 0
    found = []
    firsts = []  # unique copies of different files
    restored = []
    restored_failed = []
    for key, value in d.items():
        is_first = True
        this_source = None
        for f in value:
            f = normpath1(f)
            filename = os.path.join(dir_name, f)
            curr_found = os.path.isfile(filename)
            total += 1
            if curr_found:
                if is_first:
                    firsts.append(firsts)
                found.append(filename)
                if this_source is None:
                    this_source = filename
            else:
                if this_source is not None:
                    shutil.copyfile(this_source, filename)
                if os.path.isfile(filename):
                    restored.append(filename)
                else:
                    restored_failed.append(filename)
            is_first = False

    print('total: {} = [found: {}; firsts: {}; restored: {}; restored_failed: {}]'.
          format(total, len(found), len(firsts), len(restored), len(restored_failed)))
