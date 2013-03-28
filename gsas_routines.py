## These routines are copied from GSAS-II 
## 
import math
import numpy as np
import scipy as sp
import numpy.linalg as nl
from numpy.fft import ifft, fft, fftshift
import scipy.interpolate as si
import scipy.stats as st
import scipy.optimize as so

import bin.pypowder as pyd

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



class fcjde_gen(st.rv_continuous):
    """
    Finger-Cox-Jephcoat D(2phi,2th) function for S/L = H/L
    Ref: J. Appl. Cryst. (1994) 27, 892-900.
    Parameters
    -----------------------------------------
    x: array -1 to 1
    t: 2-theta position of peak
    s: sum(S/L,H/L); S: sample height, H: detector opening, 
        L: sample to detector opening distance
    dx: 2-theta step size in deg
    Result for fcj.pdf
    -----------------------------------------
    T = x*dx+t
    s = S/L+H/L
    if x < 0: 
        fcj.pdf = [1/sqrt({cos(T)**2/cos(t)**2}-1) - 1/s]/|cos(T)|    
    if x >= 0:
        fcj.pdf = 0    
    """
    def _pdf(self,x,t,s,dx):
        T = dx*x+t
        ax2 = abs(npcosd(T))
        ax = ax2**2
        bx = npcosd(t)**2
        bx = np.where(ax>bx,bx,ax)
        fx = np.where(ax>bx,(np.sqrt(bx/(ax-bx))-1./s)/ax2,0.0)
        fx = np.where(fx > 0.,fx,0.0)
        return fx
             
    def pdf(self,x,*args,**kwds):
        loc=kwds['loc']
        return self._pdf(x-loc,*args)
    
 # Normal distribution

# loc = mu, scale = std
_norm_pdf_C = 1./math.sqrt(2*math.pi)

class norm_gen(st.rv_continuous):
        
    def pdf(self,x,*args,**kwds):
        loc,scale=kwds['loc'],kwds['scale']
        x = (x-loc)/scale
        return np.exp(-x**2/2.0) * _norm_pdf_C / scale
        
norm = norm_gen(name='norm',longname='A normal',extradoc="""

Normal distribution

The location (loc) keyword specifies the mean.
The scale (scale) keyword specifies the standard deviation.

normal.pdf(x) = exp(-x**2/2)/sqrt(2*pi)
""") 
class cauchy_gen(st.rv_continuous):

    def pdf(self,x,*args,**kwds):
        loc,scale=kwds['loc'],kwds['scale']
        x = (x-loc)/scale
        return 1.0/np.pi/(1.0+x*x) / scale
        
cauchy = cauchy_gen(name='cauchy',longname='Cauchy',extradoc="""
Cauchy distribution

cauchy.pdf(x) = 1/(pi*(1+x**2))

This is the t distribution with one degree of freedom.
""")
  


def getWidthsTOF(pos,alp,bet,sig,gam):
    lnf = 3.3      # =log(0.001/2)
    widths = [np.sqrt(sig),gam]
    fwhm = 2.355*widths[0]+2.*widths[1]
    fmin = 10.*fwhm*(1.+1./alp)    
    fmax = 10.*fwhm*(1.+1./bet)
    return widths,fmin,fmax

fcjde = fcjde_gen(name='fcjde',shapes='t,s,dx')
                
def getWidthsCW(pos,sig,gam,shl):
    widths = [np.sqrt(sig)/100.,gam/200.]
    fwhm = 2.355*widths[0]+2.*widths[1]
    fmin = 10.*(fwhm+shl*abs(npcosd(pos)))
    fmax = 15.0*fwhm
    if pos > 90:
        fmin,fmax = [fmax,fmin]          
    return widths,fmin,fmax


def getFWHM(TTh,Inst):
    sig = lambda Th,U,V,W: 1.17741*math.sqrt(max(0.001,U*tand(Th)**2+V*tand(Th)+W))*math.pi/180.
    gam = lambda Th,X,Y: (X/cosd(Th)+Y*tand(Th))*math.pi/180.
    gamFW = lambda s,g: math.exp(math.log(s**5+2.69269*s**4*g+2.42843*s**3*g**2+4.47163*s**2*g**3+0.07842*s*g**4+g**5)/5.)
    s = sig(TTh/2.,Inst['U'][1],Inst['V'][1],Inst['W'][1])*100.
    g = gam(TTh/2.,Inst['X'][1],Inst['Y'][1])*100.
    return gamFW(g,s)    
                
def getFCJVoigt(pos,intens,sig,gam,shl,xdata):    
    DX = xdata[1]-xdata[0]
    widths,fmin,fmax = getWidthsCW(pos,sig,gam,shl)
    x = np.linspace(pos-fmin,pos+fmin,256)
    dx = x[1]-x[0]
    Norm = norm.pdf(x,loc=pos,scale=widths[0])
    Cauchy = cauchy.pdf(x,loc=pos,scale=widths[1])
    arg = [pos,shl/57.2958,dx,]
    FCJ = fcjde.pdf(x,*arg,loc=pos)
    if len(np.nonzero(FCJ)[0])>5:
        z = np.column_stack([Norm,Cauchy,FCJ]).T
        Z = fft(z)
        Df = ifft(Z.prod(axis=0)).real
    else:
        z = np.column_stack([Norm,Cauchy]).T
        Z = fft(z)
        Df = fftshift(ifft(Z.prod(axis=0))).real
    Df /= np.sum(Df)
    Df = si.interp1d(x,Df,bounds_error=False,fill_value=0.0)
    return intens*Df(xdata)*DX/dx


def getFCJVoigt3(pos,sig,gam,shl,xdata):
    
    Df = pyd.pypsvfcj(len(xdata),xdata-pos,pos,sig,gam,shl)
#    Df = pyd.pypsvfcjo(len(xdata),xdata-pos,pos,sig,gam,shl)
    Df /= np.sum(Df)
    return Df

def getdFCJVoigt3(pos,sig,gam,shl,xdata):
    
    Df,dFdp,dFds,dFdg,dFdsh = pyd.pydpsvfcj(len(xdata),xdata-pos,pos,sig,gam,shl)
#    Df,dFdp,dFds,dFdg,dFdsh = pyd.pydpsvfcjo(len(xdata),xdata-pos,pos,sig,gam,shl)
    sumDf = np.sum(Df)
    return Df,dFdp,dFds,dFdg,dFdsh

def getEpsVoigt(pos,alp,bet,sig,gam,xdata):
    #Df = pyd.pyepsvoigt(len(xdata),xdata-pos,alp,bet,sig,gam)
    Df = pyd.pyepsvoigt(len(xdata),xdata-pos,alp,bet,sig,gam)
    Df /= np.sum(Df)
    return Df  
    
def getdEpsVoigt(pos,alp,bet,sig,gam,xdata):
  #  Df,dFdp,dFda,dFdb,dFds,dFdg = pyd.pydepsvoigt(len(xdata),xdata-pos,alp,bet,sig,gam)
    Df,dFdp,dFda,dFdb,dFds,dFdg = pyd.pydepsvoigt(len(xdata),xdata-pos,alp,bet,sig,gam)
    sumDf = np.sum(Df)
    return Df,dFdp,dFda,dFdb,dFds,dFdg  



