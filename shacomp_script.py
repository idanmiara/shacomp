# todo rename/sort folders by priority

import sys
import matplotlib
matplotlib.use('Qt5Agg')

from shacomp import *
import shacomp_lists

pathname = os.path.dirname(sys.argv[0])
sha_dir = r"pic-sha"
sha_path = normpath1(os.path.join(pathname, sha_dir))

# read_write(dir, base_file, in_pattern, outfile)
# read_write(dir=os.path.join(pathname, sha2), master="Pictures-20170311")

do_sort = False
if do_sort:
    sha_files1 = [
        'dk8-2018-04-01-pic1.sha512', 'dk8-2018-04-01-pic-copy1.sha512',
        'dk1a.sha512', 'dk2a.sha512',
    ]
    for f in sha_files1:
        sort_sha(os.path.join(sha_path, f))

    exit(0)

# master = "0"
# base_dir = r"sample"

master = "dk1a-sorted"
data_path = 'p:\\'

# remove_log_filename = os.path.join(sha_path, 'removed_log.txt')

junk_sha_filename = os.path.join(sha_path, '_junk_set_sha512.txt')
if os.path.isfile(junk_sha_filename):
    load_sha_set(sha_blacklist=shacomp_lists.sha_blacklist, junk_sha_filename=junk_sha_filename)

# global_dict = collections.defaultdict(list)
# key = sha; val = list of all filenames with that sha
# junk = files that should be deleted as shacomp_lists.junk
# read sorted(*.sha512) files, and adding them to the dict, starting from master file then alphabetically
# global_dict = read_write(dir_name=sha_path, master=master, save_uniques_list=False, read_junks=False, sha_blacklist={zero_sha})
global_dict = read_write(dir_name=sha_path, master=master, save_uniques_list=True, read_junks=True, sha_blacklist=shacomp_lists.sha_blacklist)

# returns the keys of all files in the dict that have different ext per key, thus probably junk.
nonconsistant_exts_keys = do_all_dups_have_same_ext(global_dict, ext_whitelist=shacomp_lists.ext_whitelist, sha_blacklist=shacomp_lists.sha_blacklist)
print('list of sha with mismatch extensions: {}'.format(nonconsistant_exts_keys))
if nonconsistant_exts_keys:
    print('solve this first')
    exit(1)

# after removing all nonconsistant_exts_keys by renaming/classifiying as junk we'll delete all the junk files:
# 1. junk sha that we found (empty files, non-consistant-ext, others)
# 2. junk filename by template filenames
# we'll keep a list of (sha,filename) tups of all files that we classified as junk and deleted them
do_generate_junk_sha = False
if do_generate_junk_sha:
    do_delete = False
    junk_sha_filename_tup_list = []
    sha_to_delete_set = shacomp_lists.sha_blacklist  # {zero_sha}
    add_junk_tup_list(global_dict, junk_sha_filename_tup_list=junk_sha_filename_tup_list, delete_junk_filename_templates=True, sha_to_delete_set=sha_to_delete_set)
    if do_delete:
        delete_junk(junk_sha_filename_tup_list=junk_sha_filename_tup_list, data_dir_name=data_path)
    save_sha_tup_list(junk_sha_filename_tup_list, os.path.join(sha_path, '_junk.sha512'))
    save_sha_set(sha_to_delete_set, junk_sha_filename)

# are there any missing files? i.e. in dict but not in disk
# 2 logs will be created: 1. files with mismatch sha, 2. files that are missing
# if not verify_sha then only look for missing files
do_look_for_missing_and_mismatch = False
if do_look_for_missing_and_mismatch:
    look_for_missing_and_mismatch(global_dict, data_dir_name=data_path, log_path=sha_path, verify_sha=False)

dict_stats(global_dict, do_plot=True)

# delete_duplicates(dir_name=base_dir, d=global_dict)
# restore_duplicates(dir_name=base_dir, d=global_dict)
# os.system("pause")

print('finished!')