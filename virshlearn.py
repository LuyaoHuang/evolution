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
    def __init__(self, name, paradict, cb):
        self.name = name
        self.paradict = paradict
        self.cb = cb

    def __call__(self, paradict=None):
        if paradict == None:
            paradict = deepcopy(self.paradict)

        for i in paradict.keys():
            if isinstance(paradict[i], logicalExp):
                paradict[i] = paradict[i]()

#       print paradict
        return self.cb(paradict)

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
    def replace(self, replacedict):
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
                    x.replace(replacedict)

def Instrings(paradict):
    if "target" not in paradict.keys():
        return False
    if "source" not in paradict.keys():
        return False

    if isinstance(paradict["source"], str):
        if paradict["target"] in paradict["source"].split():
            return True
        else:
#            print "target %s not in source %s" % (paradict["target"], paradict["source"])
            return False
    elif isinstance(paradict["source"], list):
        for i in paradict["source"]:
            if paradict["target"] in i.split():
                return True

#        print "target %s not in source" % paradict["target"]
        return False
    else:
        return False

LEin = logicalExp("In", {"target": '', "source": ''}, Instrings)

def InRows(paradict):
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

LEinrow = logicalExp("InRow", {"target": '', "source": '', "row": ''}, InRows)

def InColumn(paradict):
    if "target" not in paradict.keys():
        return False
    if "source" not in paradict.keys():
        return False
    if "column" not in paradict.keys():
        return False

    if paradict["target"] in [i.split()[int(paradict["column"])] for i in paradict["source"].splitlines()]:
        return True
    else:
        return False

LEincolumn = logicalExp("InColumn", {"target": '', "source": '', "column": ''}, InColumn)

def InPath(paradict):
    if "target" not in paradict.keys():
        return False
    if "source" not in paradict.keys():
        return False
    if "row" not in paradict.keys():
        return False
    if "column" not in paradict.keys():
        return False

    if paradict["target"] == paradict["source"].splitlines()[int(paradict["row"])].split()[int(paradict["column"])]:
        return True
    else:
        return False

LEinpath = logicalExp("InPath", {"target": '', "source": '', "row": '', "column": ''}, InPath)

def fromEnv(paradict):
    if "env" not in paradict.keys():
        return False
    if "path" not in paradict.keys():
        return False

    ret = paradict["env"].getdatabypath(paradict["path"])
    return ret

LEfromenv = logicalExp("fromEnv", {"env": '', "path": ''}, fromEnv)

def cmd(paradict):
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

LEcmd = logicalExp("cmd", {"cmd": '', "ret": '', "output": ''}, cmd)

def negation(paradict):
    if "target" not in paradict.keys():
        return False

    if paradict["target"] == False:
        return True
    else:
        return False

LEnegation = logicalExp("negation", {"target": ''}, negation)

#____________________________________________________

def tmpmergepara(hypothesis):
    def _parse(data, opt, target):
        count = 0
        for i in data.keys():
            if isinstance(data[i], str):
                if opt in data[i]:
                    data[i] = data[i].replace(opt, target)
                    count += 1

            if isinstance(data[i], logicalExp):
                count += _parse(data[i].paradict, opt, target)

        return count

    index = 1
    cmd = hypothesis[-1].paradict["cmd"]

    if "virsh" in cmd.split()[0]:
        virshinfo = virshcmdinfo(cmd)
        opts = [i for i in virshinfo.optvalueinfos.values()]
    else:
        opts = cmd.split()

    for opt in opts:
        count = 0
        for i in hypothesis[:-1]:
            count += _parse(i.paradict, opt, "$X%s" % index)

        if count != 0 or len(hypothesis) == 1:
            _parse(hypothesis[-1].paradict, opt, "$X%s" % index)
            index += 1

def mergehypothesis(hypothesises):
    for i in hypothesises:
        for n in hypothesises.remove(i):
            pass
            

def cmdmatch(source, target, ret):
    srclist = source.split()
    tgtlist = target.split()
    if len(srclist) != len(tgtlist):
        return False

    for i in range(len(srclist)):
        if "$X" in srclist[i] or "$X" in tgtlist[i]:
            if "$X" in srclist[i]:
                ret[srclist[i]] = tgtlist[i]
            if "$X" in tgtlist[i]:
                ret[tgtlist[i]] = srclist[i]
            continue
        if srclist[i] != tgtlist[i]:
            return False

    return True

def checkhypothesis(env, hypothesis, data):
    """ return 0 for sucess, 1 for fail and 2 for not satisfy """
    ret = []
    cmd = hypothesis[-1].paradict["cmd"]
    stolen = {}
    if not cmdmatch(cmd, data[0], stolen):
        return 2

    tmphypothesis = deepcopy(hypothesis)
    for i in tmphypothesis:
        if i.name == "cmd":
            continue

        i.replace(stolen)
        ret.append(i())

    if False in ret:
        return 2

    result = tmphypothesis[-1]
    result.replace(stolen)

    if result.paradict["ret"] != data[1]:
        print "return number not except"
        return 1
    if len(data[2]) > 20 and result.paradict["ret"] == 0:
        print "looks like a getinfo type cmd"
        return 0
    if result.paradict["output"] != data[2]:
        print "output not except"
        return 1

    return 0

def genhypothesis(env, basecmds, options):
    hypothesises = []
    sucopts = []
    failopts = []
    tmpoptions = options
    while(tmpoptions != []):
        for i in tmpoptions:
            hypothesis = []
            tmpcmd = "%s %s" % (basecmds, i)
            try:
                out = subprocess.check_output(tmpcmd.split(), stderr=subprocess.STDOUT)
                ret = 0
            except subprocess.CalledProcessError as detail:
                out = detail.output
                ret = 1
            data = [tmpcmd, ret, out]

            for hyp in hypothesises:
                tmpret = checkhypothesis(env, hyp, data)
                if tmpret == 0:
                    print "a good hypothesis for a case"
                    hypothesis = hyp
                    tmpoptions.remove(i)
                    break
                elif tmpret == 2:
                    print "a case not cover"
                    print tmpcmd
                    print out
                    continue
                else:
                    print "result not correct"
                    print out
                    return

            if not hypothesis:
                if ret == 0:
                    possible = {}
                    for opt in i.split():
                        tmpret = env.searchdata(opt)
                        if tmpret is not None:
                            possible[opt] = tmpret
                    if len(possible) == 0:
                        """ TODO """
                        continue

                    else:
                        for d,x in possible.items():
                            for member in x:
                                LEintmp = deepcopy(LEin)
                                LEfromenvtmp = deepcopy(LEfromenv)
                                LEfromenvtmp.paradict = {'env':env, 'path': member}
                                LEintmp.paradict = {'source': LEfromenvtmp, 'target': d}
                                hypothesis.append(LEintmp)

                        LEcmdtmp = deepcopy(LEcmd)
                        LEcmdtmp.paradict = {'cmd': tmpcmd, 'ret': ret, 'output': out}
                        hypothesis.append(LEcmdtmp)
                        tmpmergepara(hypothesis)
                        print "create a hypothesis for a valid case"
                        printhypothesis(hypothesis)
                        hypothesises.append(hypothesis)
                        tmpoptions.remove(i)
                else:
                    if not hypothesises:
                        continue

                    for hyp in hypothesises:
                        tmpdict = {}
                        if not cmdmatch(hyp[-1].paradict['cmd'], tmpcmd, tmpdict):
                            continue
                        for le in hyp[:-1]:
                            lecpy = deepcopy(le)
                            lecpy.replace(tmpdict)
                            if lecpy():
                                hypothesis.append(lecpy)
                            else:
                                LEnegationtmp = deepcopy(LEnegation)
                                LEnegationtmp.paradict = {'target': lecpy}
                                hypothesis.append(LEnegationtmp)

                        LEcmdtmp = deepcopy(LEcmd)
                        LEcmdtmp.paradict = {'cmd': tmpcmd, 'ret': ret, 'output': out}
                        hypothesis.append(LEcmdtmp)
                        tmpmergepara(hypothesis)

                        if checkhypothesis(env, hypothesis, data) == 0:
                            print "a good hypothesis for a invalid case"
                            printhypothesis(hypothesis)
                            hypothesises.append(hypothesis)
                            tmpoptions.remove(i)
                            break
                        else:
                            hypothesis = []

                    if not hypothesis:
                        """ just create a empty hypothesis for it, will get fix if it was wrong """
                        LEcmdtmp = deepcopy(LEcmd)
                        LEcmdtmp.paradict = {'cmd': tmpcmd, 'ret': ret, 'output': out}
                        hypothesis.append(LEcmdtmp)
                        tmpmergepara(hypothesis)
                        print "create a tmp hypothesis for a invalid case"
                        printhypothesis(hypothesis)
                        hypothesises.append(hypothesis)

    return hypothesises


def tmpexample():
    env = virtEnv()
    subcmd = "virsh domiftune"
    options = ["test4", "rhel7.0 52:54:00:67:a9:e7", "rhel7.0", "rhel7.0 123"]
    ret = genhypothesis(env, subcmd, options)
    if ret is not None:
        printhypothesises(ret)

def printhypothesises(hypothesises):
    for i in hypothesises:
        printhypothesis(i)

def printhypothesis(hypothesis):
    print "hypothesis:"
    for n in hypothesis:
        print n

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
