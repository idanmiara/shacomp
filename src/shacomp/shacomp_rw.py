# import sys
# import re, fnmatch, os
import collections
import glob
import os
import shutil
import time

from src import shacomp as hlp
from src.shacomp import lists, plot_dict

sha_kind = "sha512"


def is_junk_file(filename):
    filename = os.path.basename(filename).lower()
    return filename in lists.junk


# returns the keys of all files that exist
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
                if not lists.is_interchangeable_ext(ext0, ext):
                    diff_ext.append(key)
    return diff_ext


def read_file(
    filename, d, d_ext, unique_log=None, sig_len=0, read_junks=False, read_underscore_folders=False, sha_blacklist=set()
):
    tuple_list = hlp.load_sha_tuples(filename)

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
            if ((not read_junks) and is_junk_file(val)) or ((not read_underscore_folders) and val.startswith("_")):
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
    print(
        "{}... valid: {}(unique: {} + dups: {}) + invalid: {} + junk: {} + blacklisted_keys: {} = total: {} entries, ({})".format(
            filename,
            valid_count,
            new_unique_count,
            valid_count - new_unique_count,
            invalid_count,
            junk_count,
            blacklisted_keys,
            total_lines,
            verify_total == verify_total,
        )
    )
    print("ext list:")
    print(d_ext)
    plot_dict.dict_stats(d)


def read_write(
    dir_name,
    master,
    ext="." + sha_kind,
    save_uniques_list=True,
    read_underscore_folders=False,
    read_junks=False,
    sha_blacklist=set(),
):
    # d = {}
    # key = hash
    # value = list of files
    d = collections.defaultdict(list)
    d_ext = collections.Counter()
    # c = collections.Counter(value for values in d.itervalues() for value in values)
    # dir=os.getcwd()
    if dir_name != "":
        os.chdir(dir_name)

    base_file = master + ext
    filename = base_file
    # if a base file is provided, read it, otherwise continue to read in alphabetical order
    if filename != "":
        s = os.path.join(dir_name, filename)
        if os.path.isfile(s):
            print("0:")
            read_file(
                s,
                d,
                d_ext,
                read_junks=read_junks,
                read_underscore_folders=read_underscore_folders,
                sha_blacklist=sha_blacklist,
            )
            print()
            # s = os.path.join(dir,filename+"-uniques"+ext)
            # save_tup_list(unique_log, s)
        else:
            print("master not found: {}...".format(s))

    in_pattern = "*" + ext
    # for filename in re.compile(fnmatch.translate(in_pattern), re.IGNORECASE):

    sha_files_count = 1
    for filename in sorted(glob.glob(in_pattern)):
        if filename == base_file or ("unique" in filename) or (filename.startswith("_")):
            continue
        print("{}:".format(sha_files_count))
        s = os.path.join(dir_name, filename)
        unique_log = []
        read_file(
            s,
            d,
            d_ext,
            unique_log=unique_log,
            read_junks=read_junks,
            read_underscore_folders=read_underscore_folders,
            sha_blacklist=sha_blacklist,
        )
        if len(unique_log) > 0:
            s = os.path.join(dir_name, "_" + os.path.splitext(filename)[0] + "-uniques" + ext)
            hlp.save_sha_tup_list(unique_log, s)
        # write_file(d, os.path.join(dir, outfile))
        print("{} new unique files from file:{}, base file:{}".format(len(unique_log), filename, base_file))
        print()
        sha_files_count += 1

    print("\n---- finished loading {} sha files ---- \n".format(sha_files_count))

    if save_uniques_list:
        lst = hlp.get_unique_tup_list_from_dict(d)
        s = os.path.join(dir_name, "_uniques" + ext)
        hlp.save_sha_tup_list(lst, s)
    return d


def look_for_missing_and_mismatch(d, data_dir_name, log_path, verify_sha=False):
    print("searching for missing files from dir: {}...".format(data_dir_name))
    total = 0
    found = 0
    missing_list = []
    sha_err = []
    for key, files_list in d.items():
        for f in files_list:
            total += 1
            f = hlp.normpath1(f)
            filename = os.path.join(data_dir_name, f)
            curr_found = os.path.isfile(filename)
            if curr_found:
                found += 1
                if verify_sha:
                    sha_hex = hlp.sha512_file(filename)
                    sha_verified = key == sha_hex
                    if not sha_verified:
                        sha_err.append(filename)
            else:
                missing_list.append(filename)
                print(filename)

    time_str = time.strftime("%Y%m%d-%H%M%S")
    if sha_err:
        hlp.save_list_to_file(sha_err, os.path.join(log_path, "sha_err_" + time_str + ".txt"))
    if missing_list:
        hlp.save_list_to_file(missing_list, os.path.join(log_path, "missing_list_" + time_str + ".txt"))
    print("total:{} found:{} sha_err:{} missing:{} ".format(total, found, len(sha_err), len(missing_list)))


def delete_from_list(sha_filename_to_delete_tup_list, data_dir, actually_delete, remove_log_filename=None):
    if remove_log_filename:
        files_remove_log = open(remove_log_filename, "a+")
    print("delete from dir: {}".format(data_dir))
    missing_count = 0
    sha_err_filenames = []
    deleted_filenames = []
    for key, val in sha_filename_to_delete_tup_list.items():
        filename = os.path.join(data_dir, val)
        curr_found = os.path.isfile(filename)
        if curr_found:
            sha_hex = hlp.sha512_file(filename)
            sha_verified = key == sha_hex
            if sha_verified:
                deleted_filenames.append(filename)
                if actually_delete:
                    os.remove(filename)
                    if remove_log_filename:
                        files_remove_log.add(filename)
                        files_remove_log.write(remove_log_filename)
            else:
                sha_err_filenames.append(filename)
                print("err #{:5d}: {}".format(len(sha_err_filenames), filename))
        else:
            missing_count += 1
    if remove_log_filename:
        files_remove_log.close()
    print(
        "deleted files from junk file list = [missing: {}; sha_err: {}; deleted: {}]".format(
            missing_count, len(sha_err_filenames), len(deleted_filenames)
        )
    )


def delete_duplicates(
    data_dir,
    d,
    junk_sha_filename_tup_list,
    delete_junk_filename_templates=True,
    sha_to_delete_set=set(),
    delete_dups=True,
    verify_file_existance=True,
    verify_sha=True,
    verify_sha_allcopies=True,
    actually_delete=False,
    do_prints=False,
    save_lists_prefix=None,
):
    print("delete duplicates from dir: {}".format(data_dir))
    total = 0

    missing = []
    sha_err = []
    sha_ok = []
    firsts = []
    delete_by_dup = []
    delete_by_template = []
    delete_by_sha = []

    all_lists = [
        ("missing", missing),
        ("sha_err", sha_err),
        ("sha_ok", sha_ok),
        ("firsts", firsts),
        ("delete_by_dup", delete_by_dup),
        ("delete_by_template", delete_by_template),
        ("delete_by_sha", delete_by_sha),
    ]

    if not data_dir:
        verify_file_existance = False
    if not verify_file_existance:
        verify_sha = False
    if not verify_sha:
        verify_sha_allcopies = False

    for key, files_list in d.items():
        copy_found = False
        is_first = True
        for val in files_list:
            val = hlp.normpath1(val)
            total += 1
            delete_this_file = False
            kv = [key, val]

            if delete_junk_filename_templates and is_junk_file(val):
                delete_this_file = True
                # sha_to_delete_set.add(key)
                delete_by_template.append(kv)
            elif sha_to_delete_set and (key in sha_to_delete_set):
                delete_this_file = True
                delete_by_sha.append(kv)
            elif delete_dups:
                if verify_file_existance:
                    filename = os.path.join(data_dir, val)
                else:
                    filename = val
                curr_found = (not verify_file_existance) or os.path.isfile(filename)
                if curr_found:
                    if (is_first and verify_sha) or (not is_first and verify_sha_allcopies):
                        sha_verified = (not verify_sha) or (key == hlp.sha512_file(filename))
                    else:
                        sha_verified = True
                    if sha_verified:
                        sha_ok.append(kv)
                        if is_first:
                            firsts.append(kv)
                        is_first = False
                    else:
                        sha_err.append(kv)
                        if do_prints:
                            print("err #{:5d}: {}".format(len(sha_err), filename))
                else:
                    sha_verified = False
                    missing.append(filename)
                    if do_prints:
                        print("mis #{:5d}: {}".format(len(missing), filename))

                if copy_found:
                    # found a concrete duplicate
                    if sha_verified:
                        delete_this_file = True
                        delete_by_dup.append(kv)
                        if do_prints:
                            print("del #{:5d}: {}".format(len(delete_by_dup), filename))
                else:
                    copy_found = sha_verified
            if delete_this_file:
                junk_sha_filename_tup_list.append(kv)
                if actually_delete:
                    os.remove(filename)
    print("total junk files: by template: {} by sha: {}".format(len(delete_by_template), len(delete_by_sha)))
    print(
        "total: {} = [missing: {}; sha_err: {}; sha_ok: {} =(firsts: {}; delete_by_dup: {})]".format(
            total, len(missing), len(sha_err), len(sha_ok), len(firsts), len(delete_by_dup)
        )
    )
    if save_lists_prefix:
        for name, tup_list in all_lists:
            filename = os.path.join(save_lists_prefix, name)
            hlp.save_sha_tup_list(tup_list, filename)


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
            f = hlp.normpath1(f)
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

    print(
        "total: {} = [found: {}; firsts: {}; restored: {}; restored_failed: {}]".format(
            total, len(found), len(firsts), len(restored), len(restored_failed)
        )
    )


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
