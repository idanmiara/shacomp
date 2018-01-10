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
pathname = os.path.dirname(sys.argv[0])
base_dir = os.path.join(pathname,r"sample")

global_dict = read_write(dir_name=base_dir, master="0")

do_plot = True
if do_plot:
    _, copies_hist = sum_default_dict(global_dict)
    plot(copies_hist)

# delete_duplicates(dir_name=base_dir, d=global_dict)
# restore_duplicates(dir_name=base_dir, d=global_dict)
# os.system("pause")
