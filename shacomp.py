import sys
import glob, re, fnmatch, os
import collections

def readfile( d, filename, siglen=0):
    with open(filename) as f:
        valid_lines=0
        total_lines=0
        if siglen==0:
            siglen=128
        delim=' *'
        invalid=[]
        for line in f:
            # line=line.rstrip('\n')
            line=line.strip()
            if (line==''):
                continue
            total_lines+=1
            [key,val]=line.split(delim, 1)
            if (len(key)!=siglen) or (len(val)==0):
                invalid.append(line)
            else:
                # d.setdefault(key,[])
                # d.append(val)
                d[key]=val
                valid_lines+=1
    print("{0}: valid: {1}/{2} entries:{3}".format(filename,valid_lines,total_lines,len(d)))

# def readoutfile( d, filename):
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
# def writefile(d, filename):
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

def read_write(dir=r'd:\shacomp', base_file=r'pictures.sha512'):
    # d = {}
    d = collections.defaultdict(list)
    #dir=os.getcwd()
    if dir!='':
        os.chdir(dir)
    if base_file!='':
        s = os.path.join(dir,base_file)
        if os.path.isfile(s):
            readfile(d, s)
    # print("{}: ",base_file,)
    #for filename in re.compile(fnmatch.translate(in_pattern), re.IGNORECASE):
    # for filename in sorted(glob.glob(in_pattern)):
    #     if filename==base_file:
    #         continue
    #     readfile(d, os.path.join(dir, filename))
    # writefile(d, os.path.join(dir, outfile))
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
read_write();

# os.system("pause")
