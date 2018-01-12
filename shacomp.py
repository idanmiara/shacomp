# import sys
# import re, fnmatch, os
# import collections
# import numpy as np
import glob
import shutil
from shacomp_helper import *

import time

sha_kind = 'sha512'


def load_sha_tuples(filename, sort=True):
    # with open(filename, encoding="utf-8-sig").read().decode("utf-8-sig") as f:
    with open(filename, mode='r', encoding="utf-8-sig") as f:
        print("{} ...".format(filename))
        delimiter = ' *'
        total_lines = 0
        invalid = []
        tuple_list = []
        for line in f:
            # line=line.rstrip('\n')
            line = line.strip()
            if line == '':
                continue
            total_lines += 1
            kv = line.split(delimiter, 1)
            if len(kv) != 2:
                invalid.append(line)
            else:
                key = kv[0].lower()
                val = kv[1]
                tuple_list.append([key, val])
    if sort:
        tuple_list.sort(key=lambda tup: tup[1])
    return tuple_list


def sort_sha(filename):
    tuple_list = load_sha_tuples(filename)
    filename1 = os.path.splitext(filename)
    filename2 = filename1[0]+"-sorted"+filename1[1]
    save_tup_list(tuple_list, filename2)


def is_junk_file(filename):
    junk = ["thumbs.db", "desktop.ini", "picasa.ini", ".picasa.ini", "picasa.ini1", ".picasa.ini1", ".nomedia"]
    filename = os.path.basename(filename).lower()
    return filename in junk


def do_all_dups_have_same_ext(d, ext_whitelist=None, sha_blacklist=set()):
    diff_ext = []
    for key, files_list in d.items():
        if (len(files_list) <= 1) or (key in sha_blacklist):
            continue
        is_first = True
        ext0 = 0
        for f in files_list:
            ext = os.path.splitext(f)[1].lower()
            if ext_whitelist and (ext not in ext_whitelist):
                continue
            if is_first:
                is_first = False
                ext0 = ext
            else:
                if ext0 != ext:
                    diff_ext.append(key)
    return diff_ext


def read_file(filename, d, d_ext, unique_log=None, sig_len=0, read_junks=False, sha_blacklist=set()):
    tuple_list = load_sha_tuples(filename)

    valid_count = 0
    total_lines = 0
    junk_count = 0
    blacklisted_keys = 0
    new_unique_count = 0
    if sig_len == 0:
        sig_len = 128
    invalid = []
    for kv in tuple_list:
        if (len(kv) != 2) or (len(kv[0]) != sig_len) or (len(kv[1]) == 0):
            invalid.append(kv)
        else:
            key = kv[0].lower()
            val = kv[1]
            if (not read_junks) and is_junk_file(val):
                junk_count += 1
            elif key in sha_blacklist:
                blacklisted_keys += 1
            else:
                # d.setdefault(key,[])
                # d.append(val)
                ext = os.path.splitext(val)[1]
                d_ext[ext.lower()] += 1
                valid_count += 1
                if val not in d[key]:
                    d[key].append(val)
                    if len(d[key]) == 1:
                        new_unique_count += 1
                        if not (unique_log is None):
                            unique_log.append([key, val])
    # unique_count = len(d)
    invalid_count = len(invalid)
    verify_total = valid_count + invalid_count + junk_count + blacklisted_keys
    print("{}... valid: {}(unique: {} + dups: {}) + invalid: {} + junk: {} + blacklisted_keys: {} = total: {} entries, ({})".
          format(filename, valid_count, new_unique_count, valid_count - new_unique_count,
                 invalid_count, junk_count, blacklisted_keys, total_lines, verify_total == verify_total))
    print('ext list:')
    print(d_ext)
    dict_stats(d)


def read_write(dir_name, master, ext='.' + sha_kind, save_uniques_list = True, read_junks=False, sha_blacklist=set()):
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
            read_file(s, d, d_ext, read_junks=read_junks, sha_blacklist=sha_blacklist)
            print()
            # s = os.path.join(dir,filename+"-uniques"+ext)
            # save_tup_list(unique_log, s)
        else:
            print('master not found: {}...'.format(s))

    in_pattern = '*'+ext
    # for filename in re.compile(fnmatch.translate(in_pattern), re.IGNORECASE):

    sha_files_count = 1
    for filename in sorted(glob.glob(in_pattern)):
        if filename == base_file or ("unique" in filename) or ("ignore" in filename):
            continue
        print('{}:'.format(sha_files_count))
        s = os.path.join(dir_name, filename)
        unique_log = []
        read_file(s, d, d_ext, unique_log=unique_log, read_junks=read_junks, sha_blacklist=sha_blacklist)
        if len(unique_log) > 0:
            s = os.path.join(dir_name, os.path.splitext(filename)[0] + "-uniques" + ext)
            save_tup_list(unique_log, s)
        # write_file(d, os.path.join(dir, outfile))
        print("{} new unique files from file:{}, base file:{}".format(len(unique_log), filename, base_file))
        print()
        sha_files_count += 1

    print("\n---- finished loading {} sha files ---- \n".format(sha_files_count))

    if save_uniques_list:
        l = get_unique_tup_list_from_dict(d)
        s = os.path.join(dir_name, "uniques" + ext)
        save_tup_list(l, s)
    return d


def which_files_are_missing(d, data_dir_name, log_path, verify_sha=False):
    print('searching for missing files from dir: {}...'.format(data_dir_name))
    total = 0
    found = 0
    missing_list = []
    sha_err = []
    for key, files_list in d.items():
        for f in files_list:
            total += 1
            f = normpath1(f)
            filename = os.path.join(data_dir_name, f)
            curr_found = os.path.isfile(filename)
            if curr_found:
                found += 1
                if verify_sha:
                    sha_hex = sha512_file(filename)
                    sha_verified = key == sha_hex
                    if not sha_verified:
                        sha_err.append(filename)
            else:
                missing_list.append(filename)
                print(filename)

    time_str = time.strftime("%Y%m%d-%H%M%S")
    if sha_err:
        save_list_to_file(sha_err, os.path.join(log_path, 'sha_err_'+time_str+'.txt'))
    if missing_list:
        save_list_to_file(missing_list, os.path.join(log_path, 'missing_list_'+time_str+'.txt'))
    print('total:{} found:{} sha_err:{} missing:{} '.
          format(total, found, len(sha_err), len(missing_list)))


def delete_junk(d, data_dir_name, delete_junk_filenames=True, sha_to_delete=set()):
    print('delete junk dir: {}'.format(data_dir_name))
    total_deleted_junk = 0
    total_deleted_by_sha = 0
    missing_count = 0
    sha_err = []
    deleted = []
    junk_sha_set = set()
    for key, files_list in d.items():
        for f in files_list:
            f = normpath1(f)
            del_by_junk = delete_junk_filenames and is_junk_file(f)
            del_by_sha = sha_to_delete and (key in sha_to_delete)
            if del_by_junk or del_by_sha:
                filename = os.path.join(data_dir_name, f)
                curr_found = os.path.isfile(filename)
                if del_by_junk:
                    total_deleted_junk += 1
                else:
                    total_deleted_by_sha += 1
                junk_sha_set.add(key)
                if curr_found:
                    sha_hex = sha512_file(filename)
                    sha_verified = key == sha_hex
                    if sha_verified:
                        deleted.append(filename)
                        os.remove(filename)
                    else:
                        sha_err.append(filename)
                        print('err #{:5d}: {}'.format(len(sha_err), filename))
                else:
                    missing_count += 1

    print('to be deleted junk: {} to be deleted sha: {} = [missing: {}; sha_err: {}; deleted: {}]'.
          format(total_deleted_junk, total_deleted_by_sha, missing_count, len(sha_err), len(deleted)))

    return junk_sha_set


def delete_duplicates(dir_name, d, remove_log_filename, verify_sha=True, verify_sha_allcopies=True):
    print('delete duplicates from dir: {}'.format(dir_name))
    files_remove_log = open(remove_log_filename, "a+")
    total = 0
    missing = []
    sha_err = []
    sha_ok = []
    firsts = []
    deleted = []
    for key, files_list in d.items():
        copy_found = False
        is_first = True
        for f in files_list:
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
                    files_remove_log.write(filename)
                    os.remove(filename)
                    deleted.append(filename)
                    print('del #{:5d}: {}'.format(len(deleted), filename))
            else:
                copy_found = sha_verified
    files_remove_log.close()
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
