#!/usr/bin/env python
from math import log
import operator
import matplotlib.pyplot as plt

def calShannonEnt(dataset):
    numentries = len(dataset)
    labelcounts = {}
    for featvec in dataset:
        currentlabel = featvec[-1]
        if currentlabel not in labelcounts.keys():
            labelcounts[currentlabel] = 0
        labelcounts[currentlabel] += 1
    shannonent = 0.0
    for key in labelcounts:
        prob = float(labelcounts[key])/numentries
        shannonent -= prob * log(prob, 2)
    return shannonent

def createdataset():
    dataset = [[1,1,'yes'],
               [1,1,'yes'],
               [1,0,'no'],
               [0,1,'no'],
               [0,1,'no'],
               ]
    labels = ['no surfacing','flippers']
    return dataset, labels

def splitdataset(dataset, axis, value):
    retdataset=[]
    for featvec in dataset:
        if featvec[axis] == value:
            reducedfeatvec = featvec[:axis]
            reducedfeatvec.extend(featvec[axis+1:])
            retdataset.append(reducedfeatvec)

    return retdataset

def choosebestfeaturetosplit(dataset):
    numfeatures = len(dataset[0]) - 1
    baseentropy = calShannonEnt(dataset)
    bestinfogain = 0.0; bestfeature = -1
    for i in range(numfeatures):
        featlist = [example[i] for example in dataset]
        uniquevals = set(featlist)
        newentropy = 0.0
        for value in uniquevals:
            subdataset = splitdataset(dataset,i,value)
            prob = len(subdataset)/float(len(dataset))
            newentropy += prob * calShannonEnt(subdataset)
        infogain = baseentropy - newentropy
        if (infogain > bestinfogain):
            bestinfogain = infogain
            bestfeature = i
    return bestfeature

def majoritycnt(classlist):
    classcount = {}
    for vote in classlist:
        if vote not in classcount.keys():
            classcount[vote] = 0
        classcount[vote] += 1
    sortedclasscount = sorted(classcount.iteritems(),key=operator.itemgetter(1),reverse=True)
    return sortedclasscount[0][0]

def createtree(dataset,labels):
    classlist = [example[-1] for example in dataset]
    if classlist.count(classlist[0]) == len(classlist):
        return classlist[0]
    if len(dataset[0]) == 1:
        return majoritycnt(classlist)
    bestfeat = choosebestfeaturetosplit(dataset)
    bestfeatlabel = labels[bestfeat]
    mytree = {bestfeatlabel: {}}
    del(labels[bestfeat])
    featvalues = [example[bestfeat] for example in dataset]
    uniquevals = set(featvalues)
    for value in uniquevals:
        sublabels = labels[:]
        mytree[bestfeatlabel][value] = createtree(splitdataset(dataset, bestfeat, value),sublabels)

    return mytree

""" give a figure """

decisionnode = dict(boxstyle='sawtooth',fc='0.8')
leafnode = dict(boxstyle='round4',fc='0.8')
arrow_args = dict(arrowstyle='<-')

def plotnode(nodetxt,centerpt,parentpt,nodetype):
    createplot.axl.annotate(nodetxt,xy=parentpt,xycoords='axes fraction',xytext=centerpt,textcoords='axes fraction',\
            va='center',ha='center',bbox=nodetype,arrowprops=arrow_args)

def getnumleafs(mytree):
    numleafs=0
    firststr=mytree.keys()[0]
    seconddict=mytree[firststr]
    for key in seconddict.keys():
        if type(seconddict[key]).__name__ == 'dict':
            numleafs += getnumleafs(seconddict[key])
        else:
            numleafs+=1
    return numleafs

def gettreedepth(mytree):
    maxdepth = 0
    firststr = mytree.keys()[0]
    seconddict=mytree[firststr]
    for key in seconddict.keys():
        if type(seconddict[key]).__name__ == 'dict':
            thisdepth = 1+gettreedepth(seconddict[key])
        else:
            thisdepth = 1
        if thisdepth > maxdepth:
            maxdepth = thisdepth
    return maxdepth

def plotmidtext(cntrpt,parentpt,txtstring):
    xmid = (parentpt[0] - cntrpt[0])/2.0 + cntrpt[0]
    ymid = (parentpt[1] - cntrpt[1])/2.0 + cntrpt[1]
    createplot.axl.text(xmid,ymid,txtstring)

def plottree(mytree,parentpt,nodetxt):
    numleafs=getnumleafs(mytree)
    depth=gettreedepth(mytree)
    firststr=mytree.keys()[0]
    cntrpt=(plottree.x0ff + (1.0 + float(numleafs))/2.0/plottree.totalw,plottree.y0ff)
    plotmidtext(cntrpt,parentpt,nodetxt)
    plotnode(firststr,cntrpt,parentpt,decisionnode)
    seconddict=mytree[firststr]
    plottree.y0ff = plottree.y0ff - 1.0/plottree.totald
    for key in seconddict.keys():
        if type(seconddict[key]).__name__ == 'dict':
            plottree(seconddict[key],cntrpt,str(key))
        else:
            plottree.x0ff = plottree.x0ff + 1.0/plottree.totalw
            plotnode(seconddict[key],(plottree.x0ff,plottree.y0ff),cntrpt,leafnode)
            plotmidtext((plottree.x0ff,plottree.y0ff),cntrpt,str(key))
    plottree.y0ff=plottree.y0ff + 1.0/plottree.totald

def createplot(intree):
    fig=plt.figure(1,facecolor='white')
    fig.clf()
    axprops=dict(xticks=[],yticks=[])
    createplot.axl=plt.subplot(111,frameon=False,**axprops)
    plottree.totalw=float(getnumleafs(intree))
    plottree.totald=float(gettreedepth(intree))
    plottree.x0ff = -0.5/plottree.totalw
    plottree.y0ff=1.0
    plottree(intree, (0.5,1.0), '')
    plt.show()

""" example """
def retrievetree(i):
    listoftrees = [{'no surfacing': {0:'no',1:{'flippers': {0:'no',1:'yes'}}}},
            {'no surfacing': {0: 'no', 1:{'flippers': {0:{'head': {0:'no',1:'yes'},1:'no'}}}}}]
    return listoftrees[i]
