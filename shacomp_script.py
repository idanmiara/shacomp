import sys
from shacomp import *
from shacomp_plot import *

#
# if len(sys.argv) >= 2:
#     dir = sys.argv[1]
# else:
#     dir = r''
#
# if len(sys.argv) >= 3:
#     base_file = sys.argv[2]
# else:
#     base_file = 'base.txt'
#
# if len(sys.argv) >= 4:
#     in_pattern = sys.argv[3]
# else:
#     in_pattern = '*.NEW'
#
# if len(sys.argv) >= 5:
#     outfile = sys.argv[4]
# else:
#     outfile = 'NEW_PRICE_LIST.txt'

# read_write(dir, base_file, in_pattern, outfile)
# read_write(dir=r"d:\git\shacomp\sha2", master="Pictures-20170311")
# sort_sha(r'd:\git\shacomp\pic-sha\dk1a.sha512')
# sort_sha(r'd:\git\shacomp\pic-sha\dk2a.sha512')
# sort_sha(r'd:\git\shacomp\pic-sha\Pictures-20170311.sha512')

# master = "0"
# base_dir = r"sample"

master = "dk1a-sorted"
base_dir = r"pic-sha"
data_path = 'p:\\'

pathname = os.path.dirname(sys.argv[0])
base_path = normpath1(os.path.join(pathname, base_dir))
# remove_log_filename = os.path.join(base_path, 'removed_log.txt')

ext_whitelist = ['.jpg', '.avi', '.thm', '.mp4', '.png', '.bmp', '.mp3', '.mov', '.mts', '.gif', '.aac', '.mpg', '.txt', '.jpeg', '.pdf',
                 '.3gp', '.exe', '.doc', '.zip', '.ogg', '.xls', '.vob', '.wmv', '.tif', '.pps', '.ppt', '.rar']
# interchageable_ext = [('mp4', 'm4a')]
ext_whitelist2 = ['.m4a']  # mp4 audio file dedicated ext

zero_sha = 'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e'
sha_blacklist = {zero_sha,
                 'bb5f0e4cad47bb8455bb274d2b9757267d8cc78112dde9600543de13d39bd035b73848aef03b591c3024b108faccc22ce76e1946dcbdd72f6233edb93fe2693d',
                 'fb1c1762bb9e2e1b70daa666f65ef88f81e480f18ffcfedf4c4ea0d9cd2edc57889edf981ce1a46e340cda57283298fc8d0169001921481b0f1f1f72f5991dd6'}


# global_dict = collections.defaultdict(list)
# key = sha; val = list of all filenames with that sha
# global_dict = read_write(dir_name=base_path, master=master, save_uniques_list=False, read_junks=False, sha_blacklist={zero_sha})
global_dict = read_write(dir_name=base_path, master=master, save_uniques_list=False, read_junks=True)

# nonconsistant_exts = do_all_dups_have_same_ext(global_dict, ext_whitelist=ext_whitelist, sha_blacklist=sha_blacklist)
# print('list of sha with mismatch extensions: {}'.format(nonconsistant_exts))
# if not nonconsistant_exts:
#     junk_sha_set = delete_junk(global_dict, data_dir_name=data_path, delete_junk_filenames=True, sha_to_delete={zero_sha})
# save_list_to_file(junk_sha_set, os.path.join(base_path,'junk_sha512'))

# which_files_are_missing(global_dict, data_dir_name=data_path, log_path=base_path, verify_sha=False)

do_plot = False
if do_plot:
    _, copies_hist = sum_default_dict(global_dict)
    my_plot(copies_hist)

# delete_duplicates(dir_name=base_dir, d=global_dict)
# restore_duplicates(dir_name=base_dir, d=global_dict)
# os.system("pause")

print('finished!')