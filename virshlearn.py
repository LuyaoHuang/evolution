#!/usr/bin/env python
import os
import sys
import random
import lxml
import lxml.etree
import subprocess
import re
import math
import trees

FILE1 = '/root/virsh.xml'

class virshcmdinfo:
    def __init__(self, string):
        self.subcmd = catchcmdname(string)
        self.optvaluelist = []
        self.optlist = []
        self.getoptvaluelist()
        self.optvalueinfos = {}
        self.optinfos = []
        self.parseoptions(string)
        self.cleancmdline = 'virsh %s' % self.subcmd
        for n in self.optvalueinfos:
            self.cleancmdline += ' %s' % self.optvalueinfos[n]

        for n in self.optinfos:
            self.cleancmdline += ' %s' % n

    def getoptvaluelist(self):
        out = subprocess.check_output(["virsh", self.subcmd, "--help"])
        find = 0
        for i in out.splitlines():
            if "OPTIONS" in i:
                find = 1
                continue

            if find == 1:
                isplit = i.split()
                if len(isplit) < 1:
                    continue

                if "<" in isplit[1] and ">" in isplit[1]:
                    if "[" in isplit[0]:
                        self.optvaluelist.append(isplit[0][1:-1])
                    else:
                        self.optvaluelist.append(isplit[0])

                else:
                    if "[" in isplit[0]:
                        self.optlist.append(isplit[0][1:-1])
                    else:
                        self.optlist.append(isplit[0])

    def parseoptions(self, string):
        strs = string.split()
        find = 0
        tmpoption = ""
        for i in strs:
            if i == self.subcmd:
                find = 1
                continue

            if find == 1:
                if tmpoption != "":
                    self.optvalueinfos[str(tmpoption)] = i
                    tmpoption = ""
                    continue

                if i in self.optvaluelist:
                    tmpoption = i
                    continue
                elif i in self.optlist:
                    self.optinfos.append(i)
                    continue

                else:
                    for n in self.optvaluelist:
                        if n not in self.optvalueinfos.keys():
                            if i not in self.optvalueinfos.values():
                                self.optvalueinfos[str(n)] = i

    def gencleancmdline(self, keys):
        ret = 'virsh %s' % self.subcmd
        for n in self.optvalueinfos:
            find = 0
            for k in keys:
                if n == k[0]:
                    ret += ' %s' % k[1]
                    find = 1 
                    break

            if find != 1:
                ret += ' %s' % self.optvalueinfos[n]

        for n in self.optinfos:
            ret += ' %s' % n
        
        return ret

def loadvirshcmd():
    fp = open(FILE1)
    tree = lxml.etree.parse(fp)
    set = tree.xpath("/virsh")[0].getchildren()
    ret = {}

    for i in set:
        opt  = []
        for j in i.getchildren():
            opt.append(j.tag)
            ret[str(i.tag)] = opt

    return ret


def getmaninfo():
    return subprocess.check_output(["man", "virsh"])

def parsemaninfo(maninfo, virshcmd):
    cmdname = ''
    words = ''
    rets={}
    for line in maninfo.splitlines():
        if re.match('^       (\S+)\s+.*', line):
            try:
                virshcmd[str(line.split()[0])]
            except KeyError:
                if cmdname != '':
                    words += line
                continue

            if cmdname != '':
                rets[str(cmdname)] = words
                cmdname = line.split()[0]
                words = line
                continue
            else:
                cmdname = line.split()[0]
                words = line
                continue

        if re.match('^(\S+)\s+.*', line) and cmdname != '':
            rets[str(cmdname)] = words
            words = ''
            cmdname = ''
            continue

        if cmdname != '':
            words += line

    return rets

def gendata(cmdinfo, cmdname,virshcmd):
    ret = {}
    number = len(cmdinfo.split())

    """ TODO """
    for i in cmdname.split('-'):
        try:
            ret[str(i)] = ret[str(i)] + 100/number
        except KeyError:
            ret[str(i)] = 100/number
        number = number + 100/number


    for i in cmdinfo.split():
        if i in ['is','are','to','be','on','at','were','was',]:
            number = number - 1
            continue

        try:
            ret[str(i)] = ret[str(i)] + 1
        except KeyError:
            ret[str(i)] = 1

        try:
            virshcmd[i]
            ret[str(i)] = ret[str(i)] + 10
            number = number + 10
        except KeyError:
            continue

    for n in ret.items():
        ret[n[0]] = float(n[1])/number

    return ret

def math_a(data):
    ret = float(0)
    for i in data.items():
        if type(i[1]) is str:
            print i
        else:
            ret += i[1]**2

    return math.sqrt(ret)

def math_b(dt, lent, di, leni):
    count = float(0)
    for n in dt.items():
        try:
            y = di[n[0]]
        except KeyError:
            continue

        x = n[1]

        count += x*y

    return count/(lent*leni)

def sort_by_value(d):
    items=d.items()
    backitems=[[v[1],v[0]] for v in items]
    backitems.sort()
    return [ backitems[i][1] for i in range(0,len(backitems))] 

def getsmilacommand(info, targetcmd):
    rets={}
    try:
        cmdinfo = info[str(targetcmd)]
    except KeyError:
        return -1

    virshcmd = loadvirshcmd()
    dt = gendata(cmdinfo, targetcmd,virshcmd)
    lent = math_a(dt)

    for i in info.items():
        if i[0] == targetcmd:
            continue

        di = gendata(i[1],i[0],virshcmd)
        leni = math_a(di)

        ret = math_b(dt, lent, di, leni)
        rets[i[0]] =ret

    for i in sort_by_value(rets):
        print("%s %s" %(i, rets[i]))

    return rets

def virshtestdata():
    mydatas=[['TODO']]
    return mydatas

def finddiff(srcstr, tarstr):
    rets = []
    srcset = set(srcstr.split())
    tarset = set(tarstr.split())
    diff = (srcset | tarset) - srcset
    while 1:
        try:
            rets.append(diff.pop())
        except KeyError:
            return rets

def finddiffline(srcstrs, tarstrs):
    rets = []
    srcset = set(srcstrs.splitlines())
    srcset = set(srcstrs.splitlines())
    diff = (srcset | tarset) - srcset
    while 1:
        try:
            rets.append(diff.pop())
        except KeyError:
            return rets

def catchcmdname(cmdline):
    find = 0
    if "virsh" in cmdline:
        for i in cmdline.split():
            if i == "virsh":
                find = 1
                continue

            if find == 1:
                return i

def genpossiblelabel(traindatas, diff, tarcmd, memory):
    rets = []
    for data in traindatas:
        cmdinfo = virshcmdinfo(data[0])
        if not cmdinfo:
            continue

        """ not check itself """
        if cmdinfo.subcmd == tarcmd:
            continue

        """ need check failed cmd? """
        keys = []
        strings = []
        if data[2] == 0:
            for i in diff:
                if i[0] != "options":
                    if i[1] in cmdinfo.optvalueinfos.values():
                        for key in cmdinfo.optvalueinfos.keys():
                            if cmdinfo.optvalueinfos[key] == i[1]:
                                keys.append([i[0], key])

                    if i[1] in data[1].split():
                        strings.append(i[0])
                else:
                    if i[1] in data[1].split():
                        strings.append(i[1])

        """ need check no strings ? """
        if len(strings) > 0:
            labelp = "if "
            for i in strings:
                labelp += "%s " % i 
            labelp += "in %s output ?" % cmdinfo.gencleancmdline([[i[1], '$%s' % i[1][2:]] for i in keys])
            rets.append([[strings, cmdinfo ,keys],labelp])


        """ TODO: need more """

    """try to gen label with memory """
    for data in memory:
        """ won't use the memory always """
        if len(rets) > 0:
            break

        cmdinfo = virshcmdinfo(data[0])
        if not cmdinfo:
            continue

        """ not check itself """
        if cmdinfo.subcmd == tarcmd:
            continue

        """ need check failed cmd? """
        keys = []
        strings = []
        if data[2] == 0:
            for i in diff:
                if i[0] != "options":
                    if i[1] in cmdinfo.optvalueinfos.values():
                        for key in cmdinfo.optvalueinfos.keys():
                            if cmdinfo.optvalueinfos[key] == i[1]:
                                keys.append([i[0], key])

                    if i[1] in data[1].split():
                        strings.append(i[0])
                else:
                    if i[1] in data[1].split():
                        strings.append(i[1])

        """ need check no strings ? """
        if len(strings) > 0:
            labelp = "if "
            for i in strings:
                labelp += "%s " % i 
            labelp += "in %s output ?" % cmdinfo.gencleancmdline([[i[1], '$%s' % i[1][2:]] for i in keys])
            rets.append([[strings, cmdinfo ,keys],labelp])


        """ TODO: need more """

    return rets

def genpossiblelabels(traindatas, tarcmd, memory):
    sucdata = []
    faildata = []
    diffs = []
    rets = []
    for data in memory:
        if tarcmd in data[0]:
            if data[2] == 0:
                sucdata.append(data)
            else:
                faildata.append(data)

    for data in traindatas:
        if tarcmd in data[0]:
            if data[2] == 0:
                sucdata.append(data)
            else:
                faildata.append(data)
            memory.append(data)

    for datasuc in sucdata:
        diff = []
        succmdinfo = virshcmdinfo(datasuc[0])
        for opt in succmdinfo.optinfos:
            diff.append(['options', opt])
        for key in succmdinfo.optvalueinfos:
            diff.append([key, succmdinfo.optvalueinfos[key]])

        diffs.append(diff)

    for diff in diffs:
        label = genpossiblelabel(traindatas, diff, tarcmd, memory)
        rets.extend(label)

    return rets

def gendataset(traindatas, labels, tarcmd):
    dataset = []
    tarcmdinfo = ''
    saveresult = -1
    for data in traindatas:
        if tarcmd in data[0]:
            if data[2] == 0:
                saveresult = 0
            else:
                saveresult = 1
            tarcmdinfo = virshcmdinfo(data[0])
            continue

    print labels
    for label in labels:
        find = 0
        for data in traindatas:
            tmpcmdinfo = virshcmdinfo(data[0])
            if len(label[0][2]) > 0:
                tmplist = []
                for string in label[0][2]:
                    if string[0] in tarcmdinfo.optvalueinfos.keys():
                        tmplist.append([string[1], tarcmdinfo.optvalueinfos[string[0]]])

                tmpstr = label[0][1].gencleancmdline(tmplist)

            else:
                tmpstr = label[0][1].cleancmdline

            if tmpstr == tmpcmdinfo.cleancmdline:
                for i in label[0][0]:
                    if tarcmdinfo.optvalueinfos[i] not in data[1]:
                        dataset.append(0)
                        find = 1
                        break
                if find != 1:
                    dataset.append(1)
                    find = 1

            if find == 1:
                break

        if find != 1:
            dataset.append(2)

    if saveresult != -1:
        if saveresult == 0:
            dataset.append('success')
        else:
            dataset.append('fail')
        return dataset

def getprintlabel(labels):
    rets=[]
    for label in labels:
        rets.append(label[1])

    return rets

def removeduplabel(labels):
    newlabels = []
    labelps = {}
    for label in labels:
        if label[1] not in labelps.keys():
            labelps[label[1]] = 1
            newlabels.append(label)

    return newlabels

def trylearn(traindatas,tarcmd):
    datasets = []
    labels = []
    memory = []
    for traindata in traindatas:
        labels.extend(genpossiblelabels(traindata, tarcmd, memory))

    print labels
    labels = removeduplabel(labels)
    print labels

    for traindata in traindatas:
        dataset = gendataset(traindata, labels, tarcmd)
        datasets.append(dataset)
    labelsforpr = getprintlabel(labels)
    return datasets, labelsforpr

def managelearn(traindatas, tarcmd):
    pass

def gendata(cmd):
    try:
        out = subprocess.check_output(cmd.split())
        retnum = 0
    except subprocess.CalledProcessError as detail:
        out = detail
        retnum = 1

    return [cmd,out,retnum]

def justexample():

    cmds1 = ['virsh list --all',
            'virsh domiflist test4-clone',
            'virsh domifstat test4-clone vnet1',
            'virsh net-list --all',
            ]
    cmds2 = ['virsh list --all',
            'virsh start test4-clone2',
            'virsh net-list --all',
            'virsh domifstat test4-clone2 vnet2',
            'virsh domiflist test4-clone2',
            'virsh dominfo rhel7.0']

    cmds3 = ['virsh list --all',
            'virsh start test4',
            'virsh net-list --all',
            'virsh domifstat test4 vnet1',
            'virsh domiflist test4',
            'virsh dominfo test4_123']
    cmds4 = ['virsh dumpxml test4',
            'virsh domiflist test4as',
            'virsh list --all',
            'virsh domifstat test4as vnet0',
            'virsh net-list --all',
            'virsh dominfo test4']
    cmds5 = ['virsh dumpxml test4',
            'virsh start testasdd --paused',
            'virsh domifstat test4 vnet0',
            'virsh domiflist test4',
            'virsh net-list --all',
            'virsh domblklist test4',
            'virsh dominfo test3']
    traindatas = []
    traindata = []

    for i in cmds1:
        traindata.append(gendata(i))
    traindatas.append(traindata)
    traindata = []
    for i in cmds2:
        traindata.append(gendata(i))
    traindatas.append(traindata)
    traindata = []
    for i in cmds3:
        traindata.append(gendata(i))
    traindatas.append(traindata)
    traindata = []
    for i in cmds4:
        traindata.append(gendata(i))
    traindatas.append(traindata)
    traindata = []
    for i in cmds5:
        traindata.append(gendata(i))
    traindatas.append(traindata)
    traindata = []

    dataset, label = trylearn(traindatas, "domifstat")
    print dataset
    print label
    mytree = trees.createtree(dataset,label)
    print mytree
    if isinstance(mytree, str):
        os.exit(1)
    trees.createplot(mytree)
