# todo rename/sort folders by priority

# import matplotlib
# matplotlib.use('Qt5Agg')

import sys
from shacomp.main import *
from shacomp import lists
import shacomp.helper as hlp

pathname = os.path.dirname(sys.argv[0])
sha_dir = r"pic-sha"
sha_path = hlp.normpath1(os.path.join(pathname, sha_dir))

# hlp.read_write(dir, base_file, in_pattern, outfile)
# hlp.read_write(dir=os.path.join(pathname, sha2), master="Pictures-20170311")

master = "20200222-185307"

do_sort = False
if do_sort:
    sha_files1 = [
        master + '.sha512'
        # 'dk8-source.sha512', 'dk8-copy.sha512'
        # 'dk8-2018-04-01-pic1.sha512', 'dk8-2018-04-01-pic-copy1.sha512',
        # 'dk1a.sha512', 'dk2a.sha512',
    ]
    for f in sha_files1:
        hlp.sort_sha(os.path.join(sha_path, f))

    exit(0)

# master = "0"
# base_dir = r"sample"

data_path = 'p:\\'

# remove_log_filename = os.path.join(sha_path, 'removed_log.txt')

junk_sha_filename = os.path.join(sha_path, '_junk_set_sha512.txt')
if os.path.isfile(junk_sha_filename):
    hlp.load_sha_set(sha_set=lists.sha_blacklist, filename=junk_sha_filename)

# global_dict = collections.defaultdict(list)
# key = sha; val = list of all filenames with that sha
# junk = files that should be deleted as shacomp_lists.junk
# read sorted(*.sha512) files, and adding them to the dict, starting from master file then alphabetically
# global_dict = read_write(dir_name=sha_path, master=master, save_uniques_list=False, read_junks=False, sha_blacklist={zero_sha})
global_dict = read_write(dir_name=sha_path, master=master, save_uniques_list=False, read_underscore_folders=False,
                         read_junks=False, sha_blacklist=lists.sha_blacklist)

# non_whitelist_ext_files =

# returns the keys of all files in the dict that have different ext per key, thus probably junk.
check_non_consistent_exts_keys = False
if check_non_consistent_exts_keys:
    non_consistent_exts_keys = do_all_dups_have_same_ext(global_dict, ext_whitelist=lists.ext_whitelist,
                                                         sha_blacklist=lists.sha_blacklist)
    print('list of sha with mismatch extensions: {}'.format(non_consistent_exts_keys))
    if non_consistent_exts_keys:
        print('solve this first')
        exit(1)

# are there any missing files? i.e. in dict but not on disk
# 2 logs will be created: 1. files with mismatch sha, 2. files that are missing
# if not verify_sha then only look for missing files
do_look_for_missing_and_mismatch = False
if do_look_for_missing_and_mismatch:
    look_for_missing_and_mismatch(global_dict, data_dir_name=data_path, log_path=sha_path, verify_sha=False)

# after removing all non_consistent_exts_keys by renaming/classifying as junk we'll delete all the junk files:
# 1. junk sha that we found (empty files, non-non_consistent-ext, others)
# 2. junk filename by template filenames
# add duplicates to the sha_filename list after verifying sha
# we'll keep a list of (sha,filename) tups of all files that we classified as junk and deleted them
sha_filename_to_delete_tup_list = []
prepare_delete_list = True
if prepare_delete_list:
    sha_to_delete_set = lists.sha_blacklist  # {zero_sha}
    delete_duplicates(d=global_dict, junk_sha_filename_tup_list=sha_filename_to_delete_tup_list,
                      delete_junk_filename_templates=True, sha_to_delete_set=sha_to_delete_set,
                      data_dir=data_path, verify_sha=True)
    hlp.save_sha_set(sha_to_delete_set, junk_sha_filename)

hlp.save_sha_tup_list(sha_filename_to_delete_tup_list, os.path.join(sha_path, '_deleted.sha512'))
actually_delete = False
do_delete = False
files_remove_log = 'deleted_files_log.txt'
if do_delete:
    delete_from_list(sha_filename_to_delete_tup_list=sha_filename_to_delete_tup_list, data_dir=data_path,
                     actually_delete=actually_delete, files_remove_log=files_remove_log)

hlp.dict_stats(global_dict, do_plot=False)

# delete_duplicates(dir_name=base_dir, d=global_dict)
# restore_duplicates(dir_name=base_dir, d=global_dict)
# os.system("pause")

print('finished!')
