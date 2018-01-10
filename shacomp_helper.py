import hashlib
import collections
import os


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


def save_tup_list(list, list_filename):
    text_file = open(list_filename, "w", -1, "utf-8-sig")
    count = len(list)
    for hash_val, filename in list:
        s = '{0} *{1}\n'.format(hash_val, filename) #hash *filename
        text_file.write(s)
    print("Writing: {0}: {1} lines".format(list_filename, count))
    text_file.close()


def print_hashes(dir_name):
    for root, dirs, files in os.walk(dir_name, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            hash_val = sha512_file(filename)
            print('{0} *{1}\n'.format(hash_val, filename))

       # for name in dirs:
       #    print(os.path.join(root, name))