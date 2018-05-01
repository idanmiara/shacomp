# todo rename/sort folders by priority

import sys
from shacomp import *
from shacomp_plot import *

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

ext_whitelist = ['.jpg', '.avi', '.thm', '.mp4', '.png', '.bmp', '.mp3', '.mov', '.mts', '.gif', '.aac', '.mpg', '.txt', '.jpeg', '.pdf',
                 '.3gp', '.exe', '.doc', '.zip', '.ogg', '.xls', '.vob', '.wmv', '.tif', '.pps', '.ppt', '.rar']
# interchageable_ext = [('mp4', 'm4a')]
ext_whitelist2 = ['.m4a']  # mp4 audio file dedicated ext

zero_sha = 'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e'

# theose are deleted already
sha_blacklist = {zero_sha}
                 # 'bb5f0e4cad47bb8455bb274d2b9757267d8cc78112dde9600543de13d39bd035b73848aef03b591c3024b108faccc22ce76e1946dcbdd72f6233edb93fe2693d', #VIDEO_TS.mpg/vob
                 # 'fb1c1762bb9e2e1b70daa666f65ef88f81e480f18ffcfedf4c4ea0d9cd2edc57889edf981ce1a46e340cda57283298fc8d0169001921481b0f1f1f72f5991dd6'} #VENDOR.DOC/TXT

junk_sha_filename = os.path.join(sha_path, '_junk_set_sha512.txt')
if os.path.isfile(junk_sha_filename):
    load_sha_set(sha_blacklist, junk_sha_filename)

# global_dict = collections.defaultdict(list)
# key = sha; val = list of all filenames with that sha
# junk = files that should be deleted as: ["thumbs.db", "desktop.ini", "picasa.ini", ".picasa.ini", "picasa.ini1", ".picasa.ini1", ".nomedia"]
# read sorted(*.sha512) files, and adding them to the dict, starting from master file then alphabetically
# global_dict = read_write(dir_name=sha_path, master=master, save_uniques_list=False, read_junks=False, sha_blacklist={zero_sha})
global_dict = read_write(dir_name=sha_path, master=master, save_uniques_list=True, read_junks=True, sha_blacklist=sha_blacklist)

# returns the keys of all files in the dict that have different ext per key, thus probably junk.
nonconsistant_exts_keys = do_all_dups_have_same_ext(global_dict, ext_whitelist=ext_whitelist, sha_blacklist=sha_blacklist)
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
    sha_to_delete_set = sha_blacklist  # {zero_sha}
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

do_plot = True
if do_plot:
    # calc copies_per_hash, copies_hist and plot it
    _, copies_hist = sum_default_dict(global_dict)
    my_plot(copies_hist)

# delete_duplicates(dir_name=base_dir, d=global_dict)
# restore_duplicates(dir_name=base_dir, d=global_dict)
# os.system("pause")

print('finished!')