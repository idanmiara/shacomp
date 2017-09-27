import sys
import glob, re, fnmatch, os
import collections
import shutil

import numpy as np
# import matplotlib.pyplot as plt

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

def plot(c):
    # labels, values = zip(*Counter(['A','B','A','C','A','A']).items())
    labels, values = zip(*c.items())

    indexes = np.arange(len(labels))
    width = 1

    plt.bar(indexes, values, width)
    plt.xticks(indexes + width * 0.5, labels)
    plt.show()

def isJunkFile(filename):
    junk = ["thumbs.db","desktop.ini", "picasa.ini", ".picasa.ini", "picasa.ini1", ".picasa.ini1"]
    return (os.path.basename(filename).lower() in junk)

def readfile( d, filename, siglen=0, uniquelog = None):
    # with open(filename, encoding="utf-8-sig").read().decode("utf-8-sig") as f:
    with open(filename, mode='r', encoding="utf-8-sig") as f:
        valid_lines=0
        total_lines=0
        junk_lines=0
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
                key = kv[0]
                val = kv[1]
                if isJunkFile(val):
                    junk_lines+=1
                else:
                    # d.setdefault(key,[])
                    # d.append(val)
                    valid_lines+=1
                    if not val in d[key]:
                        d[key].append(val)
                        if uniquelog:
                            uniquelog.append([key, val])
    print("{}: valid: {}/{}, junk:{} unique entries:{}".format(filename,valid_lines,total_lines,junk_lines,len(d)))
    printstats(d)

def printstats(d):
    c,hist = sumDefaultDict(d)
    total = sum(c.values())
    print("dict stats: unique entries:{}/{}".format(total,len(d)))
    plot(hist)
    return c

# returns a list of tuples [ (key val)...]
def getUniqueTupListFromDict(d):
    l = []
    for key, value in d.items():
        l.append((key,value[0])) #append only key and first val
    l.sort(key=lambda tup: tup[1])  # sorts in place
    return l

def saveTupList(l, filename):
    text_file = open(filename, "w", -1, "utf-8-sig")
    count=len(l)
    for k, v in l:
        s='{0} *{1}\n'.format(k,v)
        text_file.write(s)
    print("Writing: {0}: {1} lines".format(filename,count))
    text_file.close()

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
    c = collections.Counter() # for each key the value length
    hist = collections.Counter() # count the number of keys that have the same value length
    for key, value in d.items():
        l = len(value) #number of entries for this key
        c[key]=l
        hist[l]+=1
    return c,hist

def read_write(dir, master, ext='sha512'):
    # d = {}
    # key = hash
    # value = list of files
    d = collections.defaultdict(list)
    # c = collections.Counter(value for values in d.itervalues() for value in values)
    #dir=os.getcwd()
    if dir!='':
        os.chdir(dir)

    base_file=master+'.'+ext
    if base_file!='':
        s = os.path.join(dir,base_file)
        if os.path.isfile(s):
            readfile(d, s)

    in_pattern='*.'+ext
    # for filename in re.compile(fnmatch.translate(in_pattern), re.IGNORECASE):

    for filename in sorted(glob.glob(in_pattern)):
        if filename==base_file:
            continue
        s=os.path.join(dir, filename)
        uniquelog = []
        readfile(d, s, uniquelog)
        s = os.path.join(dir,filename+"-uniques.sha512")
        saveTupList(uniquelog, s)
    # writefile(d, os.path.join(dir, outfile))

    l=getUniqueTupListFromDict(d)
    s = os.path.join(dir,"uniques.sha512")
    saveTupList(l, s)

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
read_write(dir=r"d:\git\shacomp\sha\1", master="Pictures-20170311");

# os.system("pause")
