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
import string
from copy import deepcopy

FILE1 = '/root/virsh.xml'

#INFOCMD = ['cpu-stats','domdisplay','domfsinfo','domhostname','domid','domjobinfo',
#           'domname','domuuid','dumpxml','iothreadinfo','migrate-getspeed','schedinfo',
#           'vcpucount','vcpuinfo','vncdisplay','domblkerror','domblkinfo','domblklist',
#           'domblkstat','domcontrol','domif-getlink','domifaddr','domiflist','domifstat',
#           'dominfo','dommemstat','domstate','domstats','list']

# vol cmd need impletment
INFOCMD = ['list', 'snapshot-list', 'net-list', 'nwfilter-list', 'iface-list', 'nodedev-list', 'secret-list', 'pool-list', 'dumpxml', 'net-dumpxml', 'secret-dumpxml', 'pool-dumpxml', ]

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

        self.optcmdline = self.genoptcmdline([])

    def getoptvaluelist(self):
        try:
            out = subprocess.check_output(["virsh", self.subcmd, "--help"])
        except subprocess.CalledProcessError as detail:
            raise

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

    def genoptcmdline(self, keys):
        ret = 'virsh %s' % self.subcmd
        for n in self.optvalueinfos:
            find = 0
            for k in keys:
                if n == k[0]:
                    ret += ' %s %s' % (k[0], k[1])
                    find = 1 
                    break

            if find != 1:
                ret += ' %s %s' % (n ,self.optvalueinfos[n])

        for n in self.optinfos:
            ret += ' %s' % n
        
        return ret

    def cmdequal(self, tarcmdline):
        tmpcmd = virshcmdinfo(tarcmdline)

        if self.subcmd != tmpcmd.subcmd:
            return False
        if self.optvalueinfos != tmpcmd.optvalueinfos:
            return False
        if self.optinfos != tmpcmd.optinfos:
            return False

        return True

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

def findinfo(tarstr, strings):
    if tarstr in strings.split():
        return True
    else:
        return False

class virtEnv:
    def __init__(self, infocmd=INFOCMD):
        self.infocmd = infocmd
        self.datas = self._gencurrentenv()
        self.olddatas = None

    def _gencurrentenv(self):
        def _subfunc(opt, cmd, cb, index):
            tmpdict2 = {}
            tmpstr = subprocess.check_output(cb.split())
            members = [i.split()[index] for i in tmpstr.splitlines()]
            for i in members:
                tmpdict2[i] = subprocess.check_output(["virsh", "-q", cmd, opt, i])

            tmpdict[cmd] = tmpdict2

        tmpdict = {}
        for cmd in self.infocmd:
            cmdinfo = virshcmdinfo("virsh %s" % cmd)
            if "--domain" in cmdinfo.optvaluelist:
                _subfunc("--domain", cmd, "virsh -q list --all", 1)
                continue
            if "--network" in cmdinfo.optvaluelist:
                _subfunc("--network", cmd, "virsh -q net-list --all", 0)
                continue
            if "--secret" in cmdinfo.optvaluelist:
                _subfunc("--secret", cmd, "virsh -q secret-list", 0)
                continue
            if "--pool" in cmdinfo.optvaluelist:
                _subfunc("--pool", cmd, "virsh -q pool-list --all", 0)
                continue
            if "--nwfilter" in cmdinfo.optvaluelist:
                _subfunc("--nwfilter", cmd, "virsh -q nwfilter-list", 0)
                continue
#           if "--vol" in cmdinfo.optvaluelist:
#               _subfunc("--vol", cmd, "virsh -q vol-list --all", 0)
#               continue

            if "--all" in cmdinfo.optlist:
                tmpdict[cmd] = subprocess.check_output(["virsh", "-q", cmd, "--all"])
            else:
                tmpdict[cmd] = subprocess.check_output(["virsh", "-q", cmd])

        return tmpdict

    def updateData(self):
        olddatas = self.datas
        newdatas = self._gencurrentenv()
        diff = {"new":{},"old":{}}

        if olddatas == newdatas:
            return diff

        for i in newdatas.keys():
            tmpnewdiff = []
            tmpolddiff = []
            if i not in olddatas.keys():
                diff["new"][i] = newdatas[i]
                continue
            if newdatas[i] == olddatas[i]:
                continue
            if isinstance(newdatas[i], str):
                newlines = newdatas[i].splitlines()
                oldlines = olddatas[i].splitlines()
                for lines in newlines:
                    if lines not in oldlines:
                        tmpnewdiff.append(lines) 
                    else:
                        oldlines.remove(lines)

                for lines in oldlines:
                    tmpolddiff.append(lines)

                diff["new"][i] = tmpnewdiff
                diff["old"][i] = tmpolddiff
                continue
            elif isinstance(newdatas[i], dict):
                diff["new"][i] = {}
                diff["old"][i] = {}
                for sec in newdatas[i].keys():
                    if sec not in olddatas[i].keys():
                        diff["new"][i][sec] = newdatas[i][sec]
                        continue
                    if newdatas[i][sec] == olddatas[i][sec]:
                        continue
                    if not isinstance(newdatas[i][sec], str):
                        raise

                    newlines = newdatas[i][sec].splitlines()
                    oldlines = olddatas[i][sec].splitlines()
                    for lines in newlines:
                        if lines not in oldlines:
                            tmpnewdiff.append(lines) 
                        else:
                            oldlines.remove(lines)

                    for lines in oldlines:
                        tmpolddiff.append(lines)

                    diff["new"][i][sec] = tmpnewdiff
                    diff["old"][i][sec] = tmpolddiff
                    continue

        self.datas = newdatas
        self.olddatas = olddatas
        return diff

    def searchdata(self, target, source=None, path=None):
        ret = []

        if source is None:
            source = self.datas

        if path is None:
            path = ''

        if isinstance(source, dict):
            for i in source.keys():
                tmppath = '%s/%s' % (path, i)
                tmpret = self.searchdata(target, source=source[i], path=tmppath)
                if not tmpret:
                    continue
                elif isinstance(tmpret, list):
                    ret.extend(tmpret)
                elif isinstance(tmpret, str):
                    ret.append(tmpret)
        elif isinstance(source, str):
            if target == source:
                return path
            if target in source.split():
                return path
            try:
                xml = lxml.etree.fromstring(source)
                tmpret = []
                searchinxml(xml, target, ret=tmpret)
                for i in tmpret:
                    tmpstr = "%s/Xpath(%s)" % (path, i)
                    ret.append(tmpstr)

            except lxml.etree.XMLSyntaxError:
                return ret

        return ret

    def getdatabypath(self, path):
        if "Xpath" in path:
            tmppath = path[:path.find("Xpath")-1]
            pathlist = tmppath.split("/")
            pathlist.append(path[path.find("Xpath"):])
        else:
            pathlist = path.split("/")

        tmppath = self.datas
        try:
            for i in pathlist:
                if i is '':
                    continue
                if "Xpath" in i:
                    xpath = i[6:-1]
                    xml = lxml.etree.fromstring(tmppath)
                    tmpret = []
                    for n in xml.xpath(xpath):
                        if isinstance(n, str):
                            tmpret.append(n)
                    return tmpret

                if isinstance(tmppath, str):
                    print "invalid path %s" % path
                    return
                tmppath = tmppath[i]
        except KeyError:
            print "invalid path %s" % path
            return

        return [tmppath]

def searchinxml(xml, target, xpath='', ret=[]):
    if not isinstance(xml, lxml.etree._Element):
        print "invalid xml"
        return False

    if "{" in xml.tag:
        return True

    tmpxpath = "%s/%s/text()" % (xpath, xml.tag)
    if target in xml.xpath(tmpxpath):
        ret.append(tmpxpath)

    for i in xml.items():
        if i[1] == target:
            tmpxpath = "%s/%s/@%s" % (xpath, xml.tag, i[0])
            ret.append(tmpxpath)

    for i in xml.getchildren():
        tmpxpath = "%s/%s" % (xpath, xml.tag)
        if not searchinxml(i, target, xpath=tmpxpath, ret=ret):
            return False

    return True

#______________Logical part__________________________

class logicalExp:
    def __init__(self, name, paradict):
        self.name = name
        self.paradict = paradict

    def __call__(self, paradict=None, exdict=None):
        if paradict == None:
            paradict = deepcopy(self.paradict)

        for i in paradict.keys():
            if isinstance(paradict[i], logicalExp):
                paradict[i] = paradict[i](exdict=exdict)

        return self.subfunc(paradict, exdict=exdict)

    def __str__(self):
        first = True
        ret = "%s(" % self.name
        for i in self.paradict.keys():
            if not first:
                ret += ", "
            if self.paradict[i] != "":
                ret += str(self.paradict[i])
            else:
                ret += str(i)
            first = False

        ret += ")"
        return ret

    def customprint(self, avoidenv=False):
        first = True
        ret = "%s(" % self.name
        for i in self.paradict.keys():
            if not first:
                ret += ", "
            if self.paradict[i] != "":
                if isinstance(self.paradict[i], logicalExp):
                    ret += self.paradict[i].customprint(avoidenv=avoidenv)
                elif avoidenv and isinstance(self.paradict[i], virtEnv):
                    ret += 'virtEnv'
                else:
                    ret +=str(self.paradict[i])
            else:
                ret += str(i)
            first = False

        ret += ")"
        return ret

    def replace(self, replacedict, env=None):
        for source in replacedict.keys():
            for d,x in self.paradict.items():
                if isinstance(x, str):
                    if "/" in x:
                        tmpx = x.replace("/", " ")
                    else:
                        tmpx = x
                    if "'" in tmpx:
                        tmpx = tmpx.replace("'", " ")
                    if source in tmpx.split():
                        self.paradict[d] = x.replace(source, replacedict[source])

                if isinstance(x, logicalExp):
                    x.replace(replacedict, env=env)

                """ TODO: use a more general env """
                if isinstance(x, virtEnv):
                    if env != None:
                        self.paradict[d] = env

    def subfunc(self, paradict, exdict=None):
        raise NotImplementedError

    def genrandom(self, paradict=None, env=None):
        if paradict == None:
            paradict = deepcopy(self.paradict)

        for i in paradict.keys():
            if isinstance(paradict[i], logicalExp):
                paradict[i] = paradict[i].genrandom()

            elif isinstance(paradict[i], virtEnv) and env != None:
                paradict[i] = env

        return self.genposval(paradict)

    def genposval(self, paradict):
        raise NotImplementedError

    def compare(self, targetle):
        s = self.customprint(True)
        t = targetle.customprint(True)

        if s != t:
            return False
        else:
            return True

class LEin(logicalExp):
    def __init__(self, paradict=None):
        if paradict != None:
            logicalExp.__init__(self, "In", paradict)
        else:
            logicalExp.__init__(self, "In", {"target": '', "source": ''})

    def subfunc(self, paradict, exdict=None):
        if "target" not in paradict.keys():
            return False
        if "source" not in paradict.keys():
            return False

        if isinstance(paradict["source"], str):
            if paradict["target"] in paradict["source"].split():
                return True
            else:
                return False
        elif isinstance(paradict["source"], list):
            for i in paradict["source"]:
                if paradict["target"] in i.split():
                    return True

            return False
        else:
            return False

    def genposval(self, paradict):
        if "target" not in paradict.keys():
            return
        if "source" not in paradict.keys():
            return

        if "$X" not in paradict["target"]:
            return

        if isinstance(paradict["source"], str):
            return random.choice(paradict["source"].split())
        elif isinstance(paradict["source"], list):
            return random.choice(random.choice(paradict["source"].split()))
        else:
            raise TypeError, 'only support list and str type'

class LEinrow(logicalExp):
    def __init__(self, paradict=None):
        if paradict != None:
            logicalExp.__init__(self, "InRow", paradict)
        else:
            logicalExp.__init__(self, "InRow", {"target": '', "source": '', "row": ''})

    def subfunc(self, paradict, exdict=None):
        if "target" not in paradict.keys():
            return False
        if "source" not in paradict.keys():
            return False
        if "row" not in paradict.keys():
            return False

        if paradict["target"] in paradict["source"].splitlines()[int(paradict["row"])]:
            return True
        else:
            return False

    def genposval(self, paradict):
        if "target" not in paradict.keys():
            return
        if "source" not in paradict.keys():
            return
        if "row" not in paradict.keys():
            return

        if "$X" not in paradict["target"]:
            return

        if isinstance(paradict["source"], str):
            return random.choice(paradict["source"].splitlines()[int(paradict["row"])])
        else:
            raise TypeError, 'only support str type'

class LEincolumn(logicalExp):
    def __init__(self, paradict=None):
        if paradict != None:
            logicalExp.__init__(self, "InColumn", paradict)
        else:
            logicalExp.__init__(self, "InColumn", {"target": '', "source": '', "column": ''})

    def subfunc(self, paradict, exdict=None):
        if "target" not in paradict.keys():
            return False
        if "source" not in paradict.keys():
            return False
        if "column" not in paradict.keys():
            return False

        if isinstance(paradict["source"], str):
            if paradict["target"] in [i.split()[int(paradict["column"])] for i in paradict["source"].splitlines()]:
                return True
            else:
                return False
        elif isinstance(paradict["source"], list):
            for n in paradict["source"]:
                try:
                    if paradict["target"] in [i.split()[int(paradict["column"])] for i in n.splitlines()]:
                        return True
                except IndexError:
                    continue

            return False
        else:
            raise TypeError, 'only support str,list type'

    def genposval(self, paradict):
        if "target" not in paradict.keys():
            return
        if "source" not in paradict.keys():
            return
        if "column" not in paradict.keys():
            return

        if "$X" not in paradict["target"]:
            return

        if isinstance(paradict["source"], str):
            return random.choice([i.split()[int(paradict["column"])] for i in paradict["source"].splitlines()])
        else:
            raise TypeError, 'only support str type'

class LEinpath(logicalExp):
    def __init__(self, paradict=None):
        if paradict != None:
            logicalExp.__init__(self, "InPath", paradict)
        else:
            logicalExp.__init__(self, "InPath", {"target": '', "source": '', "row": '', "column": ''})

    def subfunc(self, paradict, exdict=None):
        if "target" not in paradict.keys():
            return False
        if "source" not in paradict.keys():
            return False
        if "row" not in paradict.keys():
            return False
        if "column" not in paradict.keys():
            return False

        if isinstance(paradict["source"], str):
            if "$Y" == paradict['row']:
                if exdict != {} and exdict != None:
                    paradict['row'] = exdict['$Y']
                elif exdict == {}:
                    for n in range(len(paradict["source"].splitlines())):
                        if paradict["target"] == paradict["source"].splitlines()[n].split()[int(paradict["column"])]:
                            exdict['$Y'] = n
                            return True
                    return False
                else:
                    raise ValueError, '$Y in paradict but no exdict'

            if paradict["target"] == paradict["source"].splitlines()[int(paradict["row"])].split()[int(paradict["column"])]:
                return True
            else:
                return False
        elif isinstance(paradict["source"], list):
            for n in paradict["source"]:
                if "$Y" == paradict['row']:
                    if exdict != {} and exdict != None:
                        paradict['row'] = exdict['$Y']
                    elif exdict == {}:
                        for m in range(len(n.splitlines())):
                            if paradict["target"] == n.splitlines()[m].split()[int(paradict["column"])]:
                                exdict['$Y'] = m
                                return True

                        continue
                    else:
                        raise ValueError, '$Y in paradict but no exdict'

                if paradict["target"] == n.splitlines()[int(paradict["row"])].split()[int(paradict["column"])]:
                    return True

            return False
        else:
            raise TypeError, 'only support str,list type'

    def genposval(self, paradict):
        if "target" not in paradict.keys():
            return
        if "source" not in paradict.keys():
            return
        if "column" not in paradict.keys():
            return
        if "row" not in paradict.keys():
            return

        if "$X" not in paradict["target"]:
            return
        if "$Y" not in paradict["row"]:
            return paradict["source"].splitlines()[int(paradict["row"])].split()[int(paradict["column"])]

        if isinstance(paradict["source"], str):
            ranrow = random.choice(paradict["source"].splitlines())
            return ranrow.split()[int(paradict["column"])]
        elif isinstance(paradict["source"], list):
            ranrow = random.choice(random.choice(paradict["source"].splitlines()))
            return ranrow.split()[int(paradict["column"])]
        else:
            raise TypeError, 'only support str,list type'

class LEfromenv(logicalExp):
    def __init__(self, paradict=None):
        if paradict != None:
            logicalExp.__init__(self, "fromEnv", paradict)
        else:
            logicalExp.__init__(self, "fromEnv", {"env": '', "path": ''})

    def subfunc(self, paradict, exdict=None):
        if "env" not in paradict.keys():
            return False
        if "path" not in paradict.keys():
            return False

        ret = paradict["env"].getdatabypath(paradict["path"])
        return ret

    def genposval(self, paradict):
        if "env" not in paradict.keys():
            return
        if "path" not in paradict.keys():
            return

        if "$X" in paradict["path"]:
            raise ValueError, "not support $X in path now"

        ret = paradict["env"].getdatabypath(paradict["path"])
        if ret == None or ret == []:
            return
        else:
            return random.choice(ret)

class LEcmd(logicalExp):
    def __init__(self, paradict=None):
        if paradict != None:
            logicalExp.__init__(self, "cmd", paradict)
        else:
            logicalExp.__init__(self, "cmd", {"cmd": '', "ret": '', "output": ''})

    def subfunc(self, paradict, exdict=None):
        if "cmd" not in paradict.keys():
            return False
        if "ret" not in paradict.keys():
            return False
        if "output" not in paradict.keys():
            return False

        try:
            out = subprocess.check_output(paradict["cmd"].split(), stderr=subprocess.STDOUT)
            ret = 0
        except subprocess.CalledProcessError as detail:
            out = detail.output
            ret = 1

        if ret == int(paradict["ret"]) and out == paradict["output"]:
            return True
        else:
            return False

    def genposval(self, paradict):
        if "cmd" not in paradict.keys():
            return

        retcmd = ''
        for n in self.paradict['cmd'].split():
            if '$X' in n:
                retcmd += genstring()
            else:
                retcmd += n
            retcmd += ' '

        return retcmd

class LEnegation(logicalExp):
    def __init__(self, paradict=None):
        if paradict != None:
            logicalExp.__init__(self, "negation", paradict)
        else:
            logicalExp.__init__(self, "negation", {"target": ''})

    def subfunc(self, paradict, exdict=None):
        if "target" not in paradict.keys():
            return False

        if paradict["target"] == False:
            return True
        else:
            return False

    def genposval(self, paradict):
        if "target" not in paradict.keys():
            return

        return genstring()
#____________________________________________________

class hypothesis:
    def __init__(self, leset=None, result=None, cmd=None, env=None):
        if leset is None:
            self.leset = []
        else:
            self.leset = leset
        self.result = result
        self.cmd = cmd
        self.env = env

    def append(self, le):
        self.leset.append(le)

    def tmpmergepara(self):
        def _parse(data, opt, target):
            count = 0
            for i in data.keys():
                if isinstance(data[i], str):
                    """ fixme: just a work around """
                    if '/' in data[i]:
                        if opt in data[i].split('/'):
                            data[i] = data[i].replace(opt, target)
                        continue
                    elif opt in data[i]:
                        data[i] = data[i].replace(opt, target)
                        count += 1

                if isinstance(data[i], logicalExp):
                    count += _parse(data[i].paradict, opt, target)

            return count

        index = 1
        cmd = self.result.paradict["cmd"]

        if "virsh" in cmd.split()[0]:
            virshinfo = virshcmdinfo(cmd)
            opts = virshinfo.optvalueinfos.values()
        else:
            opts = cmd.split()

        for opt in opts:
            count = 0
            for i in self.leset:
                count += _parse(i.paradict, opt, "$X%d" % index)

            if count != 0 or self.leset == []:
                _parse(self.result.paradict, opt, "$X%d" % index)
                index += 1

        """TODO: move to a split func"""
        """ drop some similar le """
        remove = []
        for n in self.leset:
            base = n.customprint(True)
            if n in remove:
                continue
            for m in self.leset:
                target = m.customprint(True)
                if m in remove:
                    continue
                val = lookslike(base, target)
                if val == 1 or val < 0.6:
                    continue
                if base.count('$Y') > 0 or target.count('$Y') > 0:
                    continue
                if base.count('$X') > target.count('$X'):
                    remove.append(m)
                    continue
                elif base.count('$X') < target.count('$X'):
                    remove.append(n)
                    break

        for i in remove:
            self.leset.remove(i)

    def mergehypothesis(hypothesises):
        for i in hypothesises:
            for n in hypothesises.remove(i):
                pass

    def printhypothesis(self):
        print "hypothesis:"
        for n in self.leset:
            print n

        print self.result

    def checkhypothesis(self, env, data):
        """ return 0 for sucess, 1 for fail and 2 for not satisfy """
        ret = []
        cmd = self.result.paradict["cmd"]
        stolen = {}
        if not cmdmatch(cmd, data[0], stolen):
            return 2

        tmpleset = deepcopy(self.leset)
        exdict = {}
        for i in tmpleset:
            i.replace(stolen, env=env)
            if not i(exdict=exdict):
                return 2

        result = deepcopy(self.result)
        result.replace(stolen, env=env)

        if result.paradict["ret"] != data[1]:
            print "return number not except"
            return 1
        if len(data[2]) > 20 and result.paradict["ret"] == 0:
            """TODO: find a way to check if it is right"""
            print "looks like a getinfo type cmd"
            return 0
        if result.paradict["output"] != data[2]:
            print "output not except"
            return 1

        print 'good!'
        return 0

    def foundposcmd(self, env):
        def _deepcheck(source, target):
            if isinstance(source, logicalExp):
                for n in source.paradict.values():
                    if _deepcheck(n, target):
                        return True
                return False
            elif isinstance(source, str):
                if target in source:
                    return True
                else:
                    return False

            elif isinstance(source, virtEnv):
                return False
            elif isinstance(source, int):
                return False
            else:
                raise TypeError,'only support logicalExp and str'

        if not isinstance(self.result, logicalExp):
            raise ValueError, 'wrong result'

        l1 = []
        retcmd = self.result.paradict['cmd']
        for n in retcmd.split():
            if "$X" in n:
                l1.append(n)

        replacedict = {}
        tmpleset = deepcopy(self.leset)

        if tmpleset == []:
            return self.result.genrandom(env=env)

        while(l1 != []):
            for n in tmpleset:
                found = ''
                for i in l1:
                    if _deepcheck(n, i):
                        if found == '':
                            found = i
                        else:
                            found = ''
                            break

                if found == '':
                    continue

                try:
                    if found not in replacedict.keys():
                        replacedict[found] = n.genrandom(env=env)
                except TypeError:
                    """ just gen a random string """
                    replacedict[found] = genstring()
                except ValueError:
                    continue

                l1.remove(found)
                break

            for i in tmpleset:
                i.replace(replacedict, env=env)

        for n in replacedict.keys():
            retcmd = retcmd.replace(n, replacedict[n])

        return retcmd

def genstring():
#    fd = open('/dev/urandom')
#    ret = fd.read(4)
#    fd.close()
#    return ret
    return ''.join(random.choice(string.letters) for i in range(4))

def cmdmatch(source, target, ret):
    srclist = source.split()
    tgtlist = target.split()
    if len(srclist) != len(tgtlist):
        return False

    for i in range(len(srclist)):
        if "$X" in srclist[i] or "$X" in tgtlist[i]:
            if "$X" in srclist[i]:
                ret[srclist[i]] = tgtlist[i]
                continue
            if "$X" in tgtlist[i]:
                ret[tgtlist[i]] = srclist[i]
                continue
        if srclist[i] != tgtlist[i]:
            return False

    return True

def lookslike(source, target):
    if len(source.split()) < 10 or len(target.split()) < 10:
        n = 0
        tmplist = []
        while(n < len(source)):
            tmplist.append(source[n:n+2])
            tmplist.append(source[n+1:n+3])
            n += 2
        sets = set(tmplist)
        n = 0
        tmplist = []
        while(n < len(target)):
            tmplist.append(target[n:n+2])
            tmplist.append(target[n+1:n+3])
            n += 2
        sett = set(tmplist)

    else:
        sets = set(source.split())
        sett = set(target.split())

    return float(len(sets & sett))/len(sets | sett)

def classify(strings, sign=None):
    try:
        if lxml.etree.fromstring(strings):
            print 'not support xml now'
            return
    except:
        pass

    """ should be output of cmd """
    if strings.splitlines() == 1:
        print 'so less info'
        return

    ret = {}
    if sign == None:
        sign = random.choice(strings.splitlines())
    else:
        for i in strings.splitlines():
            if sign in i:
                sign = i
                break

    pool = strings.splitlines()

    for n in pool:
        diff = 0
        if n == '':
            continue

        if len(n.split()) > len(sign.split()):
            diff += len(n.split()) - len(sign.split())
            lenth = len(sign.split())
        elif len(n.split()) < len(sign.split()):
            diff += len(sign.split()) - len(n.split())
            lenth = len(n.split())
        else:
            lenth = len(n.split())

        for i in range(lenth):
            if n.split()[i] != sign.split()[i]:
                diff += 1

        if diff not in ret.keys():
            ret[diff] = [n]
        else:
            ret[diff].append(n)

    return ret

def hypcheckvalid(hypothesises, hyp):
    for n in hypothesises:
        stolen = {}
        tmpleset = deepcopy(n.leset)
        found = 0
        for le in hyp.leset:
            for i in tmpleset:
                if le.compare(i):
                    found += 1
                    break

        if found == len(hyp.leset):
            return n

    return

def revisedhypothesis(hyp, hypothesises, data, env):
    def subfunc(le, leresult, cmdline, env=None):
        stolen = {}
        if not cmdmatch(leresult.paradict["cmd"], cmdline, stolen):
            raise ValueError, 'invalid hypothesis'
        
        tmple = deepcopy(le)

        if env == None:
            tmple.replace(stolen)
        else:
            tmple.replace(stolen, env)

        if not tmple(tmple.paradict):
            raise ValueError, 'invalid hypothesis'

        if isinstance(tmple.paradict["source"], list):
            if len(tmple.paradict["source"]) > 1:
                raise ValueError, 'not support list now'

            strings = tmple.paradict["source"][0]
        else:
            strings = tmple.paradict["source"]

        target = tmple.paradict["target"]

        return strings, target

    """ 1: search in hypothesises find close hypothesis """
    for n in hypothesises:
        result = n.result
        stolen = {}
        if lookslike(result.paradict['output'], data[2]) < 0.4:
            continue

        if not cmdmatch(result.paradict["cmd"], data[0], stolen):
            continue

        tmpleset = deepcopy(n.leset)
        tmphyp = hypothesis(cmd=data, env=deepcopy(env))
        for i in tmpleset:
            i.replace(stolen, env=env)
            if i():
                tmphyp.append(i)

        if tmphyp.leset == []:
            continue

        LEcmdtmp = LEcmd({'cmd': data[0], 'ret': data[1], 'output': data[2]})
        tmphyp.result = LEcmdtmp
        tmphyp.tmpmergepara()
        hypothesises.remove(n)
        tmphyp.printhypothesis()
        conflicthyp = hypcheckvalid(hypothesises, tmphyp)
        if not conflicthyp:
            hypothesises.append(tmphyp)
            return True
        else:
            hypothesises.append(n)

    """ 2: try harder, refactor old hypothesis """
    for le in hyp.leset:
        """ refactor the le """
        if le.name not in  ['In', 'InColumn']:
            """ TODO """
            continue

        csrc,ctgt = subfunc(le, hyp.result, hyp.cmd[0])
        src,tgt = subfunc(le, hyp.result, data[0], env)

        """ TODO: use a ML model to classify """
        try:
            if lxml.etree.fromstring(csrc):
                print 'not support xml now'
                return
        except:
            pass

        for n in range(len(csrc.splitlines())):
            for c in range(len(csrc.splitlines()[n].split())):
                if ctgt == csrc.splitlines()[n].split()[c]:
                    ccolumn = c
                    crow = n
                    break

        for n in range(len(src.splitlines())):
            for c in range(len(src.splitlines()[n].split())):
                if tgt == src.splitlines()[n].split()[c]:
                    column = c
                    row = n
                    break

        """ not correct here, why chose column ? """
        if ccolumn != column:
            cnewle = LEincolumn({"target": le.paradict['target'], "source": le.paradict['source'], "column": ccolumn})
            newle = LEincolumn({"target": le.paradict['target'], "source": le.paradict['source'], "column": column})
            hyp.leset.remove(le)
            newhyp = deepcopy(hyp)
            hyp.leset.append(cnewle)

            newhyp.leset.append(newle)
            stolen = {}
            cmdmatch(newhyp.result.paradict["cmd"], data[0], stolen)
            for i in newhyp.leset:
                i.replace(stolen, env=env)
            newhyp.result = LEcmd({'cmd': data[0], 'ret': data[1], 'output': data[2]})
            newhyp.tmpmergepara()
            print " ============= create a new hyp ============= "
            newhyp.printhypothesis()
            print " ============ refactor a old hyp ============ "
            hyp.printhypothesis()
            print " ============================================ "
            hypothesises.append(newhyp)
            return True
        else:
            """ try to split it """
            ctmplist = [i.split()[column] for i in csrc.splitlines()]
            tmplist = [i.split()[column] for i in src.splitlines()]
            info = {}
            cinfo = {}
            for n in ctmplist:
                if n in cinfo.keys():
                    cinfo[n] += 1
                else:
                    cinfo[n] = 1

            for n in tmplist:
                if n in info.keys():
                    info[n] += 1
                else:
                    info[n] = 1

            if info[tgt] == cinfo[ctgt]:
                """ need try harder and harder... """
                """ search more info (Why?) """
                print src.splitlines()[row].split()
                for n in range(len(src.splitlines()[row].split())):
                    if n == column:
                        continue
                    tgt2 = src.splitlines()[row].split()[n]
                    ctgt2 = csrc.splitlines()[crow].split()[n]
                    if tgt2 == ctgt2:
                        continue

                    ctmplist2 = [i.split()[n] for i in csrc.splitlines()]
                    tmplist2 = [i.split()[n] for i in src.splitlines()]
                    info2 = {}
                    cinfo2 = {}
                    for m in ctmplist2:
                        if m in cinfo2.keys():
                            cinfo2[m] += 1
                        else:
                            cinfo2[m] = 1

                    for m in tmplist2:
                        if m in info2.keys():
                            info2[m] += 1
                        else:
                            info2[m] = 1

                    if info2[tgt2] > cinfo2[ctgt2]:
                        newle = LEinpath({"target": le.paradict['target'], "source": le.paradict['source'], "column": column, "row": '$Y'})
                        newle2 = LEinpath({"target": tgt2, "source": le.paradict['source'], "column": n, "row": '$Y'})
                        cnewle2 = LEnegation({'target': newle2})
                    else:
                        newle = LEinpath({"target": le.paradict['target'], "source": le.paradict['source'], "column": column, "row": '$Y'})
                        cnewle2 = LEinpath({"target": ctgt2, "source": le.paradict['source'], "column": n, "row": '$Y'})
                        newle2 = LEnegation({'target': cnewle2})

                    hyp.leset.remove(le)
                    newhyp = deepcopy(hyp)
                    hyp.leset.append(newle)
                    hyp.leset.append(cnewle2)
                    newhyp.leset.append(newle)
                    newhyp.leset.append(newle2)
                    stolen = {}
                    cmdmatch(newhyp.result.paradict["cmd"], data[0], stolen)
                    for i in newhyp.leset:
                        i.replace(stolen, env=env)
                    newhyp.result = LEcmd({'cmd': data[0], 'ret': data[1], 'output': data[2]})
                    newhyp.tmpmergepara()
                    print " ============= create a new hyp ============= "
                    newhyp.printhypothesis()
                    print " ============ refactor a old hyp ============ "
                    hyp.printhypothesis()
                    print " ============================================ "
                    hypothesises.append(newhyp)
                    return True

                continue

            if info[tgt] > cinfo[ctgt]:
                newle = LEincolumn({"target": le.paradict['target'], "source": le.paradict['source'], "column": column})
                newle2 = LEin({'target': le.paradict['target'], 'source': tgt})
                cnewle2 = LEnegation({'target': newle2})
            else:
                newle = LEincolumn({"target": le.paradict['target'], "source": le.paradict['source'], "column": column})
                cnewle2 = LEin({'target': le.paradict['target'], 'source': ctgt})
                newle2 = LEnegation({'target': cnewle2})

            hyp.leset.remove(le)
            newhyp = deepcopy(hyp)
            hyp.leset.append(newle)
            hyp.leset.append(cnewle2)
            newhyp.leset.append(newle)
            newhyp.leset.append(newle2)
            stolen = {}
            cmdmatch(newhyp.result.paradict["cmd"], data[0], stolen)
            for i in newhyp.leset:
                i.replace(stolen, env=env)
            newhyp.result = LEcmd({'cmd': data[0], 'ret': data[1], 'output': data[2]})
            newhyp.tmpmergepara()
            if newle2.name == 'In':
                """ work around """
                newle2.paradict['source'] = tgt
            if cnewle2.name == 'In':
                """ work around """
                cnewle2.paradict['source'] = ctgt
            print " ============= create a new hyp ============= "
            newhyp.printhypothesis()
            print " ============ refactor a old hyp ============ "
            hyp.printhypothesis()
            print " ============================================ "
            hypothesises.append(newhyp)
            return True

    print 'fail to revise hypothesis'
    return False

def genhypothesisV2(env, cmd, hypothesises):
    """ TODO: split sub cmd and options """
    mainprocess = cmd.split()[0]
    subcmd = cmd.split()[1]

    if mainprocess not in hypothesises.keys():
        hypothesises[str(mainprocess)] = {}

    if subcmd not in hypothesises[mainprocess]:
        hypothesises[mainprocess][subcmd] = []

    subhypothesises = hypothesises[mainprocess][subcmd]

    try:
        out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        ret = 0
    except subprocess.CalledProcessError as detail:
        out = detail.output
        ret = 1
    data = [cmd, ret, out]

    hyp = hypothesis(cmd=data, env=deepcopy(env))

    for tmphyp in subhypothesises:
        tmpret = tmphyp.checkhypothesis(env, data)
        if tmpret == 0:
            print "a good hypothesis for a case"
            tmphyp.printhypothesis()
            print cmd
            print out
            return True
        elif tmpret == 2:
#            print "a case not cover"
            continue
        else:
            print "result not correct"
            tmphyp.printhypothesis()
            print cmd
            print out
            if revisedhypothesis(tmphyp, subhypothesises, data, env):
                return True
            else:
                return False

    if ret == 0:
        possible = {}
        """ TODO: split sub cmd and options """
        for opt in cmd.split()[2:]:
            tmpret = env.searchdata(opt)
            if tmpret is not None:
                possible[opt] = tmpret

        if len(possible) == 0:
            """ TODO """
            return False

        else:
            for d,x in possible.items():
                for member in x:
                    LEfromenvtmp = LEfromenv({'env':env, 'path': member})
                    LEintmp = LEin({'source': LEfromenvtmp, 'target': d})
                    hyp.append(LEintmp)

            LEcmdtmp = LEcmd({'cmd': cmd, 'ret': ret, 'output': out})
            hyp.result = LEcmdtmp
            hyp.tmpmergepara()
            print "create a hypothesis for a valid case"
            hyp.printhypothesis()
            subhypothesises.append(hyp)
    else:
        for tmphyp in subhypothesises:
            tmpdict = {}
            if not cmdmatch(tmphyp.result.paradict['cmd'], cmd, tmpdict):
                continue
            exdict = {}
            for le in tmphyp.leset:
                lecpy = deepcopy(le)
                lecpy.replace(tmpdict)
                if lecpy(exdict=exdict):
                    hyp.append(lecpy)
                else:
                    LEnegationtmp = LEnegation({'target': lecpy})
                    hyp.append(LEnegationtmp)

            LEcmdtmp = LEcmd({'cmd': cmd, 'ret': ret, 'output': out})
            hyp.result = LEcmdtmp
            hyp.tmpmergepara()

            if hyp.checkhypothesis(env, data) == 0:
                print "a good hypothesis for a invalid case"
                hyp.printhypothesis()
                subhypothesises.append(hyp)
                return True
            else:
                hyp.leset = []
                hyp.result = None

        """ just create a empty hypothesis for it, will get fix if it was wrong """
        LEcmdtmp = LEcmd({'cmd': cmd, 'ret': ret, 'output': out})
        hyp.result = LEcmdtmp
        hyp.tmpmergepara()
        print "create a tmp hypothesis for a invalid case"
        hyp.printhypothesis()
        subhypothesises.append(hyp)

    return True

def tmpexample():
    env = virtEnv()
    hypothesises = {}
#    subcmd = "virsh domiftune"
#    options = ["test4", "rhel7.0 52:54:00:67:a9:e7", "rhel7.0", "rhel7.0 123" , "2131 123535", "3 123"]
    subcmd = 'virsh blockjob'
    options = ['rhel7.0-rhel vda', 'rhel7.0-rhel', 'rhel7.0 vda', '123 345']
    for i in options:
        cmd = "%s %s" % (subcmd, i)
        if not genhypothesisV2(env, cmd, hypothesises):
            print "error"
            return

    while(True):
        cmd = genvirshcmd(subcmd, options, hypothesises, env)
        print cmd
        if not genhypothesisV2(env, cmd, hypothesises):
            print 'error'
            return

    printhypothesises(hypothesises)

def printhypothesises(hypothesises):
    for i in hypothesises.values():
        for n in i.values():
            for m in n:
                m.printhypothesis()

def genvirshcmd(subcmd, options, hypothesises, env):
    lay1 = random.choice(hypothesises.keys())
    lay2 = random.choice(hypothesises[lay1].keys())
    lay3 = random.choice(hypothesises[lay1][lay2])
    return lay3.foundposcmd(env)

#___________________________________________

class vagueConvey:
    def __init__(self, cmd, val, des):
        self.cmd = cmd
        self.val = val
        self.des = des

    def infocmd(string, cmdout, wale=None, rank=None):
        pass

class virshlabel:
    def __init__(self, strings, cmdinfo, keys):
        self.strings = strings
        self.cmdinfo = cmdinfo
        self.keys = keys
        self.labelforprint = self._genprint()

    def _genprint(self):
        labelp = "if "
        for i in self.strings:
            labelp += "%s " % i 
        labelp += "in %s output ?" % self.cmdinfo.gencleancmdline([[i[1], '$%s' % i[1][2:]] for i in self.keys])
        return labelp

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
            if len(strings) > 0:
                rets.append(virshlabel(strings, cmdinfo, keys))

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

            if len(strings) > 0:
                rets.append(virshlabel(strings, cmdinfo, keys))

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

    for label in labels:
        find = 0
        for data in traindatas:
            if data[2] != 0:
                continue
            tmpcmdinfo = virshcmdinfo(data[0])
            if len(label.keys) > 0:
                tmplist = []
                for string in label.keys:
                    if string[0] in tarcmdinfo.optvalueinfos.keys():
                        tmplist.append([string[1], tarcmdinfo.optvalueinfos[string[0]]])

                tmpstr = label.cmdinfo.gencleancmdline(tmplist)

            else:
                tmpstr = label.cmdinfo.cleancmdline

            if tmpcmdinfo.cmdequal(tmpstr):
                for i in label.strings:
                    print tarcmdinfo.optvalueinfos[i]
                    if not findinfo(tarcmdinfo.optvalueinfos[i], data[1]):
                        dataset.append(1)
                        find = 1
                        break
                if find != 1:
                    dataset.append(0)
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

def checklabelresult(tree, fulcmd, labels):
    tarcmdinfo = virshcmdinfo(fulcmd)

    if len(tree.keys()) != 1:
        raise

    print "check %s" % tree.keys()[0]
    for l in labels:
        if tree.keys()[0] == l[1]:
            label = l
            break

    if not label:
        raise

    tmplist = []
    for string in label[0][2]:
        if string[0] in tarcmdinfo.optvalueinfos.keys():
            tmplist.append([string[1], tarcmdinfo.optvalueinfos[string[0]]])

    tmpcmd = label[0][1].genoptcmdline(tmplist)
    dataset = gendata(tmpcmd)
    find = 0
    if dataset[2] != 0:
        result = 1
    else:
        for i in label[0][0]:
            try:
                if not findinfo(tarcmdinfo.optvalueinfos[i], dataset[1]):
                    result = 1
                    find = 1
                    break
            except KeyError:
                result = 1
                find = 1

        if find != 1:
            result = 0

    nextone = tree.values()[0][result]
    if isinstance(nextone, str):
        return nextone
    elif isinstance(nextone, dict):
        return checklabelresult(nextone, fulcmd, labels)
    else:
        raise

def getprintlabel(labels):
    rets=[]
    for label in labels:
        rets.append(label.labelforprint)

    return rets

def removeduplabel(labels):
    newlabels = []
    labelps = {}
    for label in labels:
        if label.labelforprint not in labelps.keys():
            labelps[label.labelforprint] = 1
            newlabels.append(label)

    return newlabels

def trylearn(traindatas,tarcmd):
    datasets = []
    labels = []
    memory = []

    for traindata in traindatas:
        labels.extend(genpossiblelabels(traindata, tarcmd, memory))

    labels = removeduplabel(labels)

    for traindata in traindatas:
        dataset = gendataset(traindata, labels, tarcmd)
        datasets.append(dataset)
    return datasets, labels

def managelearn(traindatas, tarcmd):
    pass

def gendata(cmd):
    try:
        out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        retnum = 0
    except subprocess.CalledProcessError as detail:
        out = detail.output
        retnum = 1

    return [cmd,out,retnum]

def justexample():

    cmds1 = ['virsh list --all',
            'virsh domiflist test4-clone',
            'virsh domifstat test4-clone vnet1',
            'virsh memtune test4-clone vnet1',
            'virsh net-list --all',
            'virsh dominfo testaaa4',
            ]
    cmds2 = ['virsh list --all',
            'virsh start test4-clone2',
            'virsh net-list --all',
            'virsh domifstat test4-clone2 vnet1',
            'virsh memtune test4-clone2 vnet1',
            'virsh domiflist test4-clone2',
            'virsh dominfo rhel7.0']

    cmds3 = ['virsh list --all',
            'virsh start test4',
            'virsh net-list --all',
            'virsh domifstat test4 vnet1',
            'virsh memtune test4',
            'virsh domiflist test4',
            'virsh dominfo test4_123']
    cmds4 = ['virsh dumpxml test4',
            'virsh domiflist test4as',
            'virsh list --all',
            'virsh domifstat test4as vnet0',
            'virsh memtune test4as',
            'virsh net-list --all',
            'virsh dominfo test433']
    cmds5 = ['virsh dumpxml test4',
            'virsh start testasdd --paused',
            'virsh domifstat test4 vnet0',
            'virsh memtune test4 -1',
            'virsh list --all',
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

    dataset, labels = trylearn(traindatas, "memtune")
    labelsforpr = getprintlabel(labels)
    print dataset
    print labelsforpr
    mytree = trees.createtree(dataset,labelsforpr)
    print mytree
    if isinstance(mytree, str):
        sys.exit(1)
#    print checklabelresult(mytree, "virsh domiftune test4 vnet0", labels)
    trees.createplot(mytree)
