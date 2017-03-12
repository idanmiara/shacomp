import sys
import glob, re, fnmatch, os
import collections
import shutil

import numpy as np
import matplotlib.pyplot as plt

def plot(c):
    # labels, values = zip(*Counter(['A','B','A','C','A','A']).items())
    labels, values = zip(*c.items())

    indexes = np.arange(len(labels))
    width = 1

    plt.bar(indexes, values, width)
    plt.xticks(indexes + width * 0.5, labels)
    plt.show()

def readfile( d, filename, siglen=0):
    # with open(filename, encoding="utf-8-sig").read().decode("utf-8-sig") as f:
    with open(filename, mode='r', encoding="utf-8-sig") as f:
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
            kv=line.split(delim, 1)
            if (len(kv)!=2) or (len(kv[0])!=siglen) or (len(kv[1])==0):
                invalid.append(line)
            else:
                # d.setdefault(key,[])
                # d.append(val)
                valid_lines+=1
                d[kv[0]].append(kv[1])
    print("{0}: valid: {1}/{2} unique entries:{3}".format(filename,valid_lines,total_lines,len(d)))
    printstats(d)

def printstats(d):
    c,hist = sumDefaultDict(d)
    total = sum(c.values())
    print("dict stats: unique entries:{}/{}".format(total,len(d)))
    plot(hist)
    return c

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

def sumDefaultDict(d):
    c = collections.Counter()
    hist = collections.Counter()
    for key, value in d.items():
        l = len(value)
        c[key]=l
        hist[l]+=1
    return c,hist

def read_write(dir=r'd:\projects\shacomp', master=r'pictures',ext='sha512'):
    # d = {}
    d = collections.defaultdict(list)
    # c = collections.Counter(value for values in d.itervalues() for value in values)
    #dir=os.getcwd()
    if dir!='':
        os.chdir(dir)
    base_file=master+'.'+ext
    in_pattern='*.'+ext
    if base_file!='':
        s = os.path.join(dir,base_file)
        if os.path.isfile(s):
            readfile(d, s)

    # for filename in re.compile(fnmatch.translate(in_pattern), re.IGNORECASE):
    for filename in sorted(glob.glob(in_pattern)):
        if filename==base_file:
            continue
        s=os.path.join(dir, filename)
        readfile(d, s)
    # writefile(d, os.path.join(dir, outfile))

def deldups(basedir, d):
    deleted = 0
    total=0
    totalfound=0
    firstsFound=0
    for key, value in d.items():
        copyfound = False
        isFirst = True
        for f in value:
            filename=os.path.join(basedir, f)
            currfound=os.path.isfile(filename)
            total+=1
            if currfound:
                totalfound+=1
            if copyfound:
                deleted+=1
                if currfound:
                    os.remove(filename)
                if isFirst:
                    firstsFound +=1
            else:
                copyfound=currfound
            isFirst = False

def undeldups(basedir, d):
    undeleted = 0
    undeletedFailed = []
    total=0
    totalfound=0
    firstsFound=0
    for key, value in d.items():
        isFirst = True
        thisSource = None
        for f in value:
            filename=os.path.join(basedir, f)
            currfound=os.path.isfile(filename)
            total+=1
            if currfound:
                if isFirst:
                    firstsFound+=1
                totalfound+=1
                if thisSource==None:
                    thisSource=filename
            else:
                if thisSource!=None:
                    shutil.copyfile(thisSource, filename)
                if os.path.isfile(filename):
                    undeleted+=1
                else:
                    undeletedFailed+=1
            isFirst = False

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
