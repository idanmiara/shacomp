import hashlib
import collections
import os
import sys

def sha512_file(file_name):
    sha512 = hashlib.sha512()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha512.update(chunk)
    return sha512.hexdigest()


# takes a windows or linux path (forward or backwards slashes) and returns a platform path
def normpath1(f):
    f = os.path.join(*f.split('\\'))  # transform windows path to linux path
    return os.path.normpath(f)  # transform linux path to platform path


def sum_default_dict(d):
    copies_per_hash = collections.Counter()  # for each key the value length
    copies_hist = collections.Counter()  # count the number of keys that have the same value length
    for key, value in d.items():
        length = len(value)  # number of entries for this key
        copies_per_hash[key] = length
        copies_hist[length] += 1
    return copies_per_hash, copies_hist


def dict_stats(d):
    # copies_hist - how many files (value) have (key) copies
    copies_per_hash, _ = sum_default_dict(d)
    total = sum(copies_per_hash.values())
    print("dict stats: unique entries:{}/{}".format(len(d), total))


# returns a list of tuples [ (key val)...]
def get_unique_tup_list_from_dict(d):
    l = []
    for key, value in d.items():
        l.append((key, value[0]))  # append only key and first val
    l.sort(key=lambda tup: tup[1])  # sorts in place
    return l


def save_list_to_file(lst, filename):
    with open(filename, mode='w', encoding="utf-8-sig") as f:
        for ele in lst:
            f.write(ele + '\n')


def save_sha_tup_list(tup_list, out_filename):
    with open(out_filename, "w", encoding="utf-8-sig") as f:
        count = len(tup_list)
        for hash_val, filename in tup_list:
            s = '{0} *{1}\n'.format(hash_val, filename) #hash *filename
            f.write(s)
        print("Writing: {0}: {1} lines".format(out_filename, count))


def save_sha_set(sha_set, out_filename):
    with open(out_filename, "w", encoding="utf-8-sig") as f:
        count = len(sha_set)
        for hash_val in sha_set:
            s = '{0}\n'.format(hash_val) #hash *filename
            f.write(s)
        print("Writing: {0}: {1} lines".format(out_filename, count))


def load_sha_set(sha_set, out_filename):
    with open(out_filename, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line == '':
                continue
            sha_set.add(line)
    print("sha set length".format, len(sha_set))


def print_hashes(dir_name, list_filename = None, max_count = None):
    if max_count is None:
        max_count = sys.maxsize
    else:
        print('processing {} files'.format(max_count))

    write_file = list_filename is not None
    if write_file:
        text_file = open(list_filename, "w", encoding="utf-8-sig")

    i = 0
    for root, dirs, files in os.walk(dir_name, topdown=False):
        for name in files:
            i = i+1
            filename = os.path.join(root, name)
            hash_val = sha512_file(filename)
            s = '{0} *{1}\n'.format(hash_val, filename)
            print('{}: {}'.format(i,s))
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
    save_sha_tup_list(tuple_list, filename2)

