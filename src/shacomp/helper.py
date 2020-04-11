import collections
import glob
import hashlib
import os
import sys
import time

from src.shacomp.timer import Timer

# from natsort import natsorted
# import natsort as ns


def sha512_file(file_name):
    sha512 = hashlib.sha512()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha512.update(chunk)
    return sha512.hexdigest()


# takes a windows or linux path (forward or backwards slashes) and returns a platform path
def normpath1(f):
    f = os.path.join(*f.split("\\"))  # transform windows path to linux path
    return os.path.normpath(f)  # transform linux path to platform path


def sum_default_dict(d):
    copies_per_hash = collections.Counter()  # for each key the value length
    copies_hist = collections.Counter()  # count the number of keys that have the same value length
    ext_hist = collections.Counter()  # count the number of keys per ext
    for key, files_list in d.items():
        length = len(files_list)  # number of entries for this key
        copies_per_hash[key] = length
        copies_hist[length] += 1
        for f in files_list:
            ext = os.path.split(f)[1]
            ext_hist[ext] += 1
    return copies_per_hash, copies_hist, ext_hist


# returns a list of tuples [ (key val)...]
def get_unique_tup_list_from_dict(d):
    lst = []
    for key, value in d.items():
        lst.append((key, value[0]))  # append only key and first val
    lst.sort(key=lambda tup: tup[1].lower())  # sorts in place
    # ns.natsorted(lst, key=lambda tup: tup[1], alg=ns.PATH)
    return lst


def save_list_to_file(lst, filename):
    with open(filename, mode="w", encoding="utf-8-sig") as f:
        for ele in lst:
            f.write(ele + "\n")


def save_sha_tup_list(tup_list, out_filename):
    with open(out_filename, "w", encoding="utf-8-sig") as f:
        count = len(tup_list)
        for hash_val, filename in tup_list:
            s = "{0} *{1}\n".format(hash_val, filename)  # hash *filename
            f.write(s)
        print("Writing: {0}: {1} lines".format(out_filename, count))


def save_sha_set(sha_set, filename):
    with open(filename, "w", encoding="utf-8-sig") as f:
        count = len(sha_set)
        for hash_val in sha_set:
            s = "{0}\n".format(hash_val)  # hash *filename
            f.write(s)
        print("Writing: {0}: {1} lines".format(filename, count))


def load_sha_set(sha_set, filename):
    with open(filename, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line == "":
                continue
            sha_set.add(line)
    print("sha set length".format, len(sha_set))


def print_hashes(dir_name, list_filename=None, max_count=None):
    if max_count is None:
        max_count = sys.maxsize
    else:
        print("processing {} files".format(max_count))

    write_file = list_filename is not None
    if write_file:
        text_file = open(list_filename, "w", encoding="utf-8-sig")

    i = 0
    for root, dirs, files in os.walk(dir_name, topdown=False):
        for name in files:
            i = i + 1
            filename = os.path.join(root, name)
            hash_val = sha512_file(filename)
            s = "{0} *{1}\n".format(hash_val, filename)
            print("{}: {}".format(i, s))
            if write_file:
                text_file.write(s)
            if i >= max_count:
                break
        if i >= max_count:
            break
    if write_file:
        text_file.close()


def load_sha_tuples(filename, sort=True):
    # with open(filename, encoding="utf-8-sig").read().decode("utf-8-sig") as f:
    with open(filename, mode="r", encoding="utf-8-sig") as f:
        print("{} ...".format(filename))
        delimiter = " *"
        total_lines = 0
        invalid = []
        tuple_list = []
        for line in f:
            # line=line.rstrip('\n')
            line = line.strip()
            if line == "":
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
        tuple_list.sort(key=lambda tup: tup[1].lower())
        # ns.natsorted(tuple_list, key=lambda tup: tup[1], alg=ns.PATH)

    return tuple_list


def sort_sha(filename):
    tuple_list = load_sha_tuples(filename)
    filename1 = os.path.splitext(filename)
    filename2 = filename1[0] + "-sorted" + filename1[1]
    save_sha_tup_list(tuple_list, filename2)


def make_signatures(path, base_path, output_root, use_cache=True):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    output_filename = os.path.join(output_root, timestr + ".sha512")

    fail_filename = os.path.join(output_root, timestr + "_failed.txt")
    not_file_filename = os.path.join(output_root, timestr + "_not_file.txt")

    print(path)
    reverse_dict = {}

    if use_cache:
        for filename in sorted(glob.glob(os.path.join(output_root, r"**\*.sha512"), recursive=True)):
            if os.path.isfile(filename):
                tuple_list = load_sha_tuples(filename)
                for k, v in tuple_list:
                    reverse_dict[v] = k

    sha_output_file = open(output_filename, "w", encoding="utf-8-sig")
    failed_file = None
    not_files_file = None
    good_count = 0
    failed_count = 0
    not_files_count = 0
    with Timer():
        print("start reading files to sha...")
        for filename in sorted(glob.glob(path, recursive=True)):
            if os.path.isdir(filename):
                continue
            rel_filename = os.path.relpath(filename, base_path)
            if not os.path.isfile(filename):
                not_files_count += 1
                if not_files_file is None:
                    print("not files: {0}: {1} lines".format(rel_filename, not_files_count))
                    not_files_file = open(not_file_filename, "w")
                    not_files_file.flush()
                not_files_file.write(rel_filename)
                continue
            try:
                if good_count == 0:
                    print("read first file...")
                good_count += 1
                if rel_filename in reverse_dict:
                    hash_val = reverse_dict[rel_filename]
                else:
                    hash_val = sha512_file(filename)
                s = "{0} *{1}\n".format(hash_val, rel_filename)
                sha_output_file.write(s)
                if good_count % 100 == 0:
                    print("Writing: {0}: {1} lines".format(rel_filename, good_count))
                    sha_output_file.flush()
            except IOError:
                failed_count += 1
                if failed_file is None:
                    print("failed: {0}: {1} lines".format(rel_filename, failed_count))
                    failed_file = open(fail_filename, "w")
                    failed_file.flush()
                failed_file.write(rel_filename)

    print("done! count: {0}: filed: {1} not_files_count: {2}".format(good_count, failed_count, not_files_count))

    sha_output_file.close()
    if failed_file is not None:
        failed_file.close()
    if not_files_file is not None:
        not_files_file.close()
