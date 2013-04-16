import math
import re
import numpy as np
import scipy as sp
import numpy.linalg as nl
import scipy.interpolate as si
import scipy.stats as st
import scipy.optimize as so
import bin.pypowder as pyd
import copy
import numpy.ma as ma
import gsas_routines as gsas
from traits.api import HasTraits, Int, Float, Bool
from traitsui.api import View,Group,Item
import itertools                  

ind = lambda x: math.sin(x*math.pi/180.)
asind = lambda x: 180.*math.asin(x)/math.pi
tand = lambda x: math.tan(x*math.pi/180.)
atand = lambda x: 180.*math.atan(x)/math.pi
atan2d = lambda y,x: 180.*math.atan2(y,x)/math.pi
cosd = lambda x: math.cos(x*math.pi/180.)
acosd = lambda x: 180.*math.acos(x)/math.pi
rdsq2d = lambda x,p: round(1.0/math.sqrt(x),p)
#numpy versions
npsind = lambda x: np.sin(x*np.pi/180.)
npasind = lambda x: 180.*np.arcsin(x)/math.pi
npcosd = lambda x: np.cos(x*math.pi/180.)
npacosd = lambda x: 180.*np.arccos(x)/math.pi
nptand = lambda x: np.tan(x*math.pi/180.)
npatand = lambda x: 180.*np.arctan(x)/np.pi
npatan2d = lambda y,x: 180.*np.arctan2(y,x)/np.pi
npT2stl = lambda tth, wave: 2.0*npsind(tth/2.0)/wave
npT2q = lambda tth,wave: 2.0*np.pi*npT2stl(tth,wave)

def createPeakRows(params):
    # get param sets by the peak number
    iPeak = 0
    peakList=[]
    while True:
        try:
            pos = params['pos'+str(iPeak)]                
            intens = params['int'+str(iPeak)]
            sig = params['sig'+str(iPeak)]
            gam=params['gam'+str(iPeak)]
            peak=PeakRowUI(peak_number=iPeak,position=pos,intensity=intens,sigma=sig,gamma=gam)
            peakList.append(peak)
            iPeak+=1
        except KeyError:        #no more peaks to process
                break
    return peakList

def updatePeakRows(params,peaks):
    for peak in peaks:
        iPeak=peak.peak_number
        peak.position= params['pos'+str(iPeak)]
        peak.intensity=params['int'+str(iPeak)]
        peak.sigma = params['sig'+str(iPeak)]
        peak.gamma=params['gam'+str(iPeak)]

    return peaks

class PeakRowUI(HasTraits):
    peak_number = Int
    fit = Bool(True)
    position = Float
    intensity = Float
    sigma = Float
    gamma=Float
    fwhm=Float
    
    
    def __init__(self, *args, **kwargs):        
        super(PeakRowUI, self).__init__(*args, **kwargs)
        fl=2*self.gamma
        fg=2*self.sigma*np.sqrt(2*np.log(2))
        self.fwhm=0.54346*fl + np.sqrt(0.2166*np.power(fl,2)+np.power(fg,2))
    
    def row_to_dict(self):
        newdict={}
        try:
            newdict={'pos'+str(self.peak_number):self.position,'int'+str(self.peak_number):self.intensity,'sig'+str(self.peak_number):self.sigma,'gam'+str(self.peak_number):self.gamma}
            
        except BaseException as b:
            print b.__class__
            print b.args
        return newdict


    traits_view = View(
        Group(
            Item('peak_number'),
            Item('fit'),
            Item('position'),
            Item('intensity'),
            Item('sigma'),
            Item('gamma'),
            Item('fwhm')
            )
    )


def autosearch_peaks(dataset,limits,params): 
    xdata=dataset.data[:,0]
    #limits=(xdata[0],xdata[-1])
    iBeg = np.searchsorted(xdata,limits[0])
    iFin = np.searchsorted(xdata,limits[1])
    x = xdata[iBeg:iFin]
    y0 = dataset.data[iBeg:iFin,1]
    y1 = copy.copy(y0)
    ysig = np.std(y1)
    offset = [-1,1]
    ymask = ma.array(y0,mask=(y0<ysig))
    for off in offset:
        ymask = ma.array(ymask,mask=(ymask-np.roll(y0,off)<=0.))
    indx = ymask.nonzero()
    mags = ymask[indx]
    poss = x[indx]
    iPeak=0
    max_peaks=50 # arbitrarily set for now
    if len(poss)>max_peaks:
        return None
    else:
        for pos,mag in zip(poss,mags):
            params.update(setPeakparms(pos,mag,params,iPeak))
            iPeak+=1
        return createPeakRows(params)
    
def fit_peaks_background(peaksList,varyListRegx,dataset,background_file,params):  
    bakType=params['backType']
    varyList=[]# get the list of parameters to vary   
    # this is going to be our version of the doPeaksFit routine in GSASII
    background=getBackground('',params,bakType,dataset.data[:,0])
    x=dataset.data[:,0]
    y=dataset.data[:,1]
    cw = np.diff(x)
    w= 1/dataset.data[:,2]**2 

    yc = np.zeros_like(y)                           #set calcd ones to zero
    yb = np.zeros_like(y)
    yd = np.zeros_like(y)
    xBeg = 0
    xFin = len(x)-1
    params['Pdabc'] = []      #dummy Pdabc
    varyList = []
    peakNumList=[peak.peak_number for peak in peaksList]
    param_combos=list(itertools.product(*[varyListRegx,peakNumList]))
    param_list=[str(param[0])+str(param[1]) for param in param_combos]
    back_keys=np.sort([key for key in params.keys() if re.search(r'Back:',key)]).tolist()
    #varyList= np.sort([key for regex in varyListRegx for key in params.keys() if re.search(regex,key)]).tolist()
    varyList=back_keys+param_list
    
    while True:
        values =  np.array(Dict2Values(params, varyList))
        try:
            result = so.leastsq(errPeakProfile,values,Dfun=devPeakProfile,full_output=True,col_deriv=True,\
                args=(x[xBeg:xFin],y[xBeg:xFin],w[xBeg:xFin],params,varyList,bakType))
         #   result = so.leastsq(errPeakProfile,values,full_output=True,\
         #       args=(x[xBeg:xFin],y[xBeg:xFin],w[xBeg:xFin],params,varyList,bakType))
            ncyc = int(result[2]['nfev']/2) 
        finally:
            pass                 
        chisq = np.sum(result[2]['fvec']**2)
        Values2Dict(params, varyList, result[0])
        Rwp = np.sqrt(chisq/np.sum(w[xBeg:xFin]*y[xBeg:xFin]**2))*100.      #to %
        GOF = chisq/(xFin-xBeg-len(varyList))
        print 'Number of function calls:',result[2]['nfev'],' Number of observations: ',xFin-xBeg,' Number of parameters: ',len(varyList)
        #print 'fitpeak time = %8.3fs, %8.3fs/cycle'%(runtime,runtime/ncyc)
        print 'Rwp = %7.2f%%, chi**2 = %12.6g, reduced chi**2 = %6.2f'%(Rwp,chisq,GOF)
        try:
            sig = np.sqrt(np.diag(result[1])*GOF)
            if np.any(np.isnan(sig)):
                print '*** Least squares aborted - some invalid esds possible ***'
            break                   #refinement succeeded - finish up!
        except ValueError:          #result[1] is None on singular matrix
            print '**** Refinement failed - singular matrix ****'
            Ipvt = result[2]['ipvt']
            for i,ipvt in enumerate(Ipvt):
                if not np.sum(result[2]['fjac'],axis=1)[i]:
                    print 'Removing parameter: ',varyList[ipvt-1]
                    del(varyList[ipvt-1])
                    break  

    sigDict = dict(zip(varyList,sig))
    yb[xBeg:xFin] = getBackground('',params,bakType,x[xBeg:xFin])
    yc[xBeg:xFin]= getPeakProfile(params,x[xBeg:xFin],varyList,bakType)
    yd[xBeg:xFin] = y[xBeg:xFin]-yc[xBeg:xFin]
    #getBackgroundParms(params,Background)
    #BackgroundPrint(Background,sigDict)
    #GetInstParms(parmDict,Inst,varyList,Peaks)
    #GetPeaksParms(Inst,parmDict,Peaks,varyList)    
    #PeaksPrint(dataType,parmDict,sigDict,varyList)       
    Values2Dict(params,varyList,result[0]) 
    return yb,yc,params
# all this stuff is from GSAS-II with modifications to remove peaks and debye scattering from the background and intrument parameters

def setPeakparms(pos,mag,Parms,iPeak,ifQ=False,useFit=False):
    ind = 0
    if useFit:
        ind = 1
    ins = {}
    for x in ['U','V','W','X','Y']:
        ins[x] = Parms[x]
    if ifQ:                              #qplot - convert back to 2-theta
        pos = 2.0*asind(pos*wave/(4*math.pi)) #what is wave? this doesn't seem to get used anyway...
    sig = ins['U']*tand(pos/2.0)**2+ins['V']*tand(pos/2.0)+ins['W']
    gam = ins['X']/cosd(pos/2.0)+ins['Y']*tand(pos/2.0)           
    #XY = [pos,0, mag,1, sig,0, gam,0]          
       #default refine intensity 1st
    XY={'pos'+str(iPeak):pos,'int'+str(iPeak):mag,'sig'+str(iPeak):sig,'gam'+str(iPeak):gam}
    return XY

def devPeakProfile(values,xdata,ydata, weights,parmdict,varylist,bakType):
        parmdict.update(zip(varylist,values))
        return np.sqrt(weights)*getPeakProfileDerv(parmdict,xdata,varylist,bakType)


def errPeakProfile(values,xdata,ydata, weights,parmdict,varylist,bakType):        
        parmdict.update(zip(varylist,values))
        M = np.sqrt(weights)*(getPeakProfile(parmdict,xdata,varylist,bakType)-ydata)
        Rwp = min(100.,np.sqrt(np.sum(M**2)/np.sum(weights*ydata**2))*100.)
        #if dlg:
         #   GoOn = dlg.Update(Rwp,newmsg='%s%8.3f%s'%('Peak fit Rwp =',Rwp,'%'))[0]
        #    if not GoOn:
        #        return -M           #abort!!
        return M


def getBackground(pfx,parmDict,bakType,xdata):
    yb = np.zeros_like(xdata)
    nBak = 0
    cw = np.diff(xdata)
    cw = np.append(cw,cw[-1])
    while True:
        key = pfx+'Back:'+str(nBak)
        if key in parmDict:
            nBak += 1
        else:
            break
    if bakType in ['Chebyschev Polynomial','Cosine Fourier Series']:
        for iBak in range(nBak):    
            key = pfx+'Back:'+str(iBak)
            if bakType == 'Chebyschev Polynomial':
                yb += parmDict[key]*(xdata-xdata[0])**iBak
            elif bakType == 'Cosine Fourier Series':
                yb += parmDict[key]*npcosd(xdata*iBak)
    elif bakType in ['Linear Interpolation','inv interpolate','log interpolate',]:
        if nBak == 1:
            yb = np.ones_like(xdata)*parmDict[pfx+'Back:0']
        elif nBak == 2:
            dX = xdata[-1]-xdata[0]
            T2 = (xdata-xdata[0])/dX
            T1 = 1.0-T2
            yb = parmDict[pfx+'Back:0']*T1+parmDict[pfx+'Back:1']*T2
        else:
            if bakType == 'Linear Interpolation':
                bakPos = np.linspace(xdata[0],xdata[-1],nBak,True)
            elif bakType == 'inv interpolate':
                bakPos = 1./np.linspace(1./xdata[-1],1./xdata[0],nBak,True)
            elif bakType == 'log interpolate':
                bakPos = np.exp(np.linspace(np.log(xdata[0]),np.log(xdata[-1]),nBak,True))
            bakPos[0] = xdata[0]
            bakPos[-1] = xdata[-1]
            bakVals = np.zeros(nBak)
            for i in range(nBak):
                bakVals[i] = parmDict[pfx+'Back:'+str(i)]
            bakInt = si.interp1d(bakPos,bakVals,'linear')
            yb = bakInt(xdata)
    return yb
    
def getBackgroundDerv(pfx,parmDict,bakType,xdata):
    nBak = 0
    while True:
        key = pfx+'Back:'+str(nBak)
        if key in parmDict:
            nBak += 1
        else:
            break
    dydb = np.zeros(shape=(nBak,len(xdata)))
   
    if bakType in ['Chebyschev Polynomial','Cosine Fourier Series']:
        for iBak in range(nBak):    
            if bakType == 'Chebyschev Polynomial':
                dydb[iBak] = (xdata-xdata[0])**iBak
            elif bakType == 'Cosine Fourier Series':
                dydb[iBak] = npcosd(xdata*iBak)
    elif bakType in ['Linear Interpolation','inv interpolate','log interpolate',]:
        if nBak == 1:
            dydb[0] = np.ones_like(xdata)
        elif nBak == 2:
            dX = xdata[-1]-xdata[0]
            T2 = (xdata-xdata[0])/dX
            T1 = 1.0-T2
            dydb = [T1,T2]
        else:
            if bakType == 'Linear Interpolation':
                bakPos = np.linspace(xdata[0],xdata[-1],nBak,True)
            elif bakType == 'inv interpolate':
                bakPos = 1./np.linspace(1./xdata[-1],1./xdata[0],nBak,True)
            elif bakType == 'log interpolate':
                bakPos = np.exp(np.linspace(np.log(xdata[0]),np.log(xdata[-1]),nBak,True))
            bakPos[0] = xdata[0]
            bakPos[-1] = xdata[-1]
            for i,pos in enumerate(bakPos):
                if i == 0:
                    dydb[0] = np.where(xdata<bakPos[1],(bakPos[1]-xdata)/(bakPos[1]-bakPos[0]),0.)
                elif i == len(bakPos)-1:
                    dydb[i] = np.where(xdata>bakPos[-2],(bakPos[-1]-xdata)/(bakPos[-1]-bakPos[-2]),0.)
                else:
                    dydb[i] = np.where(xdata>bakPos[i],
                        np.where(xdata<bakPos[i+1],(bakPos[i+1]-xdata)/(bakPos[i+1]-bakPos[i]),0.),
                        np.where(xdata>bakPos[i-1],(xdata-bakPos[i-1])/(bakPos[i]-bakPos[i-1]),0.))
    return dydb
     
   
def getPeakProfile(parmDict,xdata,varyList,bakType):
    yb = getBackground('',parmDict,bakType,xdata)
    yc = np.zeros_like(yb)
    cw = np.diff(xdata)
    cw = np.append(cw,cw[-1])
    #if 'C' in dataType:
    U = parmDict['U']
    V = parmDict['V']
    W = parmDict['W']
    X = parmDict['X']
    Y = parmDict['Y']
    #shl = max(parmDict['SH/L'],0.002)
    shl=0.002
    Ka2 = False
    if 'Lam1' in parmDict.keys():
        Ka2 = True
        lamRatio = 360*(parmDict['Lam2']-parmDict['Lam1'])/(np.pi*parmDict['Lam1'])
        kRatio = parmDict['I(L2)/I(L1)']
    iPeak = 0
    while True:
        try:
            pos = parmDict['pos'+str(iPeak)]
            theta = (pos-parmDict['Zero'])/2.0
            intens = parmDict['int'+str(iPeak)]
            sigName = 'sig'+str(iPeak)
            if sigName in varyList:
                sig = parmDict[sigName]
            else:
                sig = U*tand(theta)**2+V*tand(theta)+W
            sig = max(sig,0.001)          #avoid neg sigma
            gamName = 'gam'+str(iPeak)
            if gamName in varyList:
                gam = parmDict[gamName]
            else:
                gam = X/cosd(theta)+Y*tand(theta)
            gam = max(gam,0.001)             #avoid neg gamma
            Wd,fmin,fmax = gsas.getWidthsCW(pos,sig,gam,shl)
            iBeg = np.searchsorted(xdata,pos-fmin)
            iFin = np.searchsorted(xdata,pos+fmin)
            if not iBeg+iFin:       #peak below low limit
                iPeak += 1
                continue
            elif not iBeg-iFin:     #peak above high limit
                return yb+yc
            yc[iBeg:iFin] += intens*gsas.getFCJVoigt3(pos,sig,gam,shl,xdata[iBeg:iFin])
            if Ka2:
                pos2 = pos+lamRatio*tand(pos/2.0)       # + 360/pi * Dlam/lam * tan(th)
                iBeg = np.searchsorted(xdata,pos2-fmin)
                iFin = np.searchsorted(xdata,pos2+fmin)
                if iBeg-iFin:
                    yc[iBeg:iFin] += intens*kRatio*gsas.getFCJVoigt3(pos2,sig,gam,shl,xdata[iBeg:iFin])
            iPeak += 1
        except KeyError:        #no more peaks to process
            return yb+yc
    
            
def getPeakProfileDerv(parmDict,xdata,varyList,bakType):
# needs to return np.array([dMdx1,dMdx2,...]) in same order as varylist = backVary,insVary,peakVary order
    dMdv = np.zeros(shape=(len(varyList),len(xdata)))
    dMdb = getBackgroundDerv('',parmDict,bakType,xdata)
    if 'Back:0' in varyList:            #background derivs are in front if present
        dMdv[0:len(dMdb)] = dMdb
    
    cw = np.diff(xdata)
    cw = np.append(cw,cw[-1])
    U = parmDict['U']
    V = parmDict['V']
    W = parmDict['W']
    X = parmDict['X']
    Y = parmDict['Y']
   # shl = max(parmDict['SH/L'], 0.002)
    shl=0.002
    Ka2 = False
    
    iPeak = 0
    while True:
        try:
            pos = parmDict['pos' + str(iPeak)]
            theta = (pos - parmDict['Zero']) / 2.0
            intens = parmDict['int' + str(iPeak)]
            sigName = 'sig' + str(iPeak)
            tanth = tand(theta)
            costh = cosd(theta)
            if sigName in varyList:
                sig = parmDict[sigName]
            else:
                sig = U * tanth ** 2 + V * tanth + W
                dsdU = tanth ** 2
                dsdV = tanth
                dsdW = 1.0
            sig = max(sig, 0.001)  # avoid neg sigma
            gamName = 'gam' + str(iPeak)
            if gamName in varyList:
                gam = parmDict[gamName]
            else:
                gam = X / costh + Y * tanth
                dgdX = 1.0 / costh
                dgdY = tanth
            gam = max(gam, 0.001)  # avoid neg gamma
            Wd, fmin, fmax = gsas.getWidthsCW(pos, sig, gam, shl)
            iBeg = np.searchsorted(xdata, pos - fmin)
            iFin = np.searchsorted(xdata, pos + fmin)
            if not iBeg + iFin:  # peak below low limit
                iPeak += 1
                continue
            elif not iBeg - iFin:  # peak above high limit
                break
            dMdpk = np.zeros(shape=(6, len(xdata)))
            dMdipk = gsas.getdFCJVoigt3(pos, sig, gam, shl, xdata[iBeg:iFin]) 
            for i in range(1, 5):
                dMdpk[i][iBeg:iFin] += 100.*cw[iBeg:iFin] * intens * dMdipk[i]
            dMdpk[0][iBeg:iFin] += 100.*cw[iBeg:iFin] * dMdipk[0]
            dervDict = {'int':dMdpk[0], 'pos':dMdpk[1], 'sig':dMdpk[2], 'gam':dMdpk[3], 'shl':dMdpk[4]}
            for parmName in ['pos', 'int', 'sig', 'gam']:
                try:
                    idx = varyList.index(parmName + str(iPeak))
                    dMdv[idx] = dervDict[parmName]
                except ValueError:
                    pass
            if 'U' in varyList:
                dMdv[varyList.index('U')] += dsdU * dervDict['sig']
            if 'V' in varyList:
                dMdv[varyList.index('V')] += dsdV * dervDict['sig']
            if 'W' in varyList:
                dMdv[varyList.index('W')] += dsdW * dervDict['sig']
            if 'X' in varyList:
                dMdv[varyList.index('X')] += dgdX * dervDict['gam']
            if 'Y' in varyList:
                dMdv[varyList.index('Y')] += dgdY * dervDict['gam']
            if 'SH/L' in varyList:
                dMdv[varyList.index('SH/L')] += dervDict['shl']  # problem here
            if 'I(L2)/I(L1)' in varyList:
                dMdv[varyList.index('I(L2)/I(L1)')] += dervDict['L1/L2']
            iPeak += 1
        except KeyError:  # no more peaks to process
            break
    return dMdv     

def Dict2Values(parmdict, varylist):
    '''Use before call to leastsq to setup list of values for the parameters 
    in parmdict, as selected by key in varylist'''
    return [parmdict[key] for key in varylist] 
    
def Values2Dict(parmdict, varylist, values):
    ''' Use after call to leastsq to update the parameter dictionary with 
    values corresponding to keys in varylist'''
    parmdict.update(zip(varylist,values))
    
         
            
