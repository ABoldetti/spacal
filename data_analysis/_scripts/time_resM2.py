import uproot
import numpy as np
import matplotlib.pyplot as plt
from iminuit import Minuit
from iminuit.cost import LeastSquares
import warnings
from scipy.optimize import curve_fit
from scipy.signal import lfilter
import copy
from IPython.display import display


event =0
# Global configuration variables
err_acceptability = 10 # Number of sigmas for noise threshold
baseline_sampling_factor = 150 # Number of points taken for noise studies
exp_gap = 100
var_peak = 15 # Range around peak to check the error (depends on the resolution of the data in input)
fit_range = 30 # n of elements to the left and the right for the fit to work (depends on the resolution of the data in input)
Fit_type = 0 # Fit method selector      1: iminuit 2: scipy
input_file = "big_data/1/100.0GeV/OutGroupd_0.root"
output_file = ""

n =100
filter_factors= np.ones(n)/n

# Data storage dictionary
struct= { 
    "cell considered" : [] ,
    "baseline" : [] ,
    "peak" : [] ,
    "matrix cell x percentages" : []
    }



def Out_Groupd_convertion(path: str):
    """
    Reads ROOT file and extracts 'mod0_ph' and 'mod0_pulse' arrays from the tree.
    Returns:
        mod_ph: numpy array of photon counts
        mod_pulse: numpy array of pulse shapes
    """
    file = uproot.open(path)
    tree = file["tree"]
    mod_ph = tree["mod0_ph"].array(library="np")
    mod_pulse = tree["mod0_pulse"].array(library="np")

    mod_ph = [i for i in mod_ph]
    mod_ph = np.array(mod_ph)

    mod_pulse = [i for i in mod_pulse]
    mod_pulse = np.array(mod_pulse)
    
    return mod_ph, mod_pulse

def IIR_filter(pulse):
    return lfilter(filter_factors , 1 , np.array(pulse , dtype=np.float32))

def Noise( pulse: np.array):
    noise = pulse[:baseline_sampling_factor:]
    return np.mean(noise) , np.std(noise)

def Fit_exp( pulse: np.array , sigma ):
    peak = min(pulse)
    index = (pulse.tolist().index(min(pulse)))-2
    crest = pulse[index - exp_gap :index:]
    try:
        ls = LeastSquares( np.arange( index - exp_gap , index , dtype=np.float128) , crest , sigma , exp)
        # pop, pcov = curve_fit(exp , np.arange( index - exp_gap , index ) , crest , [ 0.1 , 5] ,sigma= sigma)
        # m = Minuit( ls , A=pop[0] , t=pop[1])
        m = Minuit( ls , A=1, t=0.1)
        m.limits["t" , "A"]=(0.0000000001 , 1)
        m.migrad( ncall= 1000)
    except: return False

    # Fit_plot( np.arange( index - exp_gap , index , dtype=np.float128) , crest , np.full_like(crest , sigma) , m , exp)
    
    return m.valid

def exp( x , A , t):
    return -np.exp(t*x , dtype=np.float128)*A

def parabola(x, a, b, c):
    """Parabolic function for fitting."""
    return a * np.power(x, 2) - b * x + c

def err_prop(a, b, sa, sb):
    """Error propagation for ratio a/b."""
    return a/b * np.sqrt(np.power(sa,2)/np.power(a,2) + np.power(sb,2)/np.power(b,2))

def Check_Peak(pulse: np.array):
    """
    Checks if the peak is clear based on its deviation from the local mean.
    Returns True if the peak is not significant, else False.
    """
    ipeak = pulse.tolist().index(min(pulse))
    close_peak = pulse[max(ipeak-fit_range , 0):min(ipeak+fit_range , len(pulse)):]
    if ((np.mean(close_peak) - pulse[ipeak])/np.std(close_peak)) < 1:
        return True
    return False

def Clear_Peak(pulse: np.array):
    """
    Returns the minimum value (peak) and its local standard deviation.
    """
    ipeak = pulse.tolist().index(min(pulse))
    print("clear")
    return ( pulse[ipeak], ipeak)
def Find_Peak(pulse: np.array):
    """
    Fits a parabola to the peak region of the pulse.
    Returns the fitted peak position and its error.
    """

    ipeak = pulse.tolist().index(min(pulse))
    print("fit")
    close_peak = pulse[max(ipeak-fit_range , 0):min(ipeak+fit_range , len(pulse)):]
    pop, pcov = curve_fit(parabola, np.arange(max(ipeak-fit_range , 0), min(ipeak+fit_range , len(pulse))), close_peak, [0.001,0.001, pulse[ipeak]], np.std(close_peak))
    
    if Fit_type:
        return (pop[1]/(2*pop[0]), err_prop(pop[1], pop[0], pcov[1][1], pcov[0][0]))
    else:
        ls = LeastSquares(np.arange(max(ipeak-fit_range , 0), min(ipeak+fit_range , len(pulse))), close_peak, np.std(close_peak), parabola)
        m = Minuit(ls, a=pop[0], b=pop[1], c=pop[2])
        m.migrad( ncall=100)
        if(m.valid):
            ipeak = round(m.values[1]/(2*m.values[0]))
            # Fit_plot(np.arange(max(ipeak-fit_range , 0), min(ipeak+fit_range , len(pulse))), y_fit = close_peak, y_err = np.full_like(close_peak, np.std(close_peak)), m=m , func=parabola)
            return ( pulse[ipeak], ipeak)
        else: 
            warnings.warn("Fit Failed, peak and err are both 0")
            # Fit_plot(np.arange(max(ipeak-fit_range , 0), min(ipeak+fit_range , len(pulse))), y_fit = close_peak, y_err = np.full_like(close_peak, np.std(close_peak)), m=m , func=parabola)

            return (0,0)

def Fit_plot(x_fit , y_fit , y_err , m, func):

    plt.errorbar(x_fit, y_fit, yerr=y_err, fmt='o', label='Data')
    plt.plot(x_fit, func(x_fit, *m.values), label='Fit')
    plt.show()
    

if __name__ == "__main__":
    warnings.simplefilter("always")
    # Load data from ROOT file
    mod_ph, mod_pulse = Out_Groupd_convertion(input_file)

    # Separate empty and signal channels
    noise = mod_pulse[:, :16]
    mod_ph = mod_ph[:, 16:]
    mod_pulse = mod_pulse[:, 16:]

    random_noise = []

    # Analyze noise for each cell


    data= [copy.deepcopy(struct) for _ in range(len(mod_pulse)) ]
    
    
    # Select cells with significant signal above noise
    for event in range(len(mod_pulse)):
        for cell in range(16):
            mean, std = Noise( mod_pulse[event , cell])
            f_function =IIR_filter(mod_pulse[event , cell])
            f_min = min(f_function)
            if (np.abs(mean - f_min)> std): data[event]["cell considered"].append( f_min )
            

    # Analyze selected pulses
    for event in range(len(mod_pulse)):
        for cell in data[event]["cell considered"]:
            
            # Baseline calculation
            data[event]["baseline"].append((np.mean(mod_pulse[event][cell][:baseline_sampling_factor]), np.std(mod_pulse[event][cell][:baseline_sampling_factor])))
            
            # Peak analysis (clear or fit)
            data[event]["peak"].append(Clear_Peak(mod_pulse[event][cell]) if Check_Peak(mod_pulse[event][cell]) else Find_Peak(mod_pulse[event][cell]))
            
            # Calculate peak-to-baseline ratios at different percentages
            data[event]["matrix cell x percentages"].append([(data[event]["peak"][-1][0] - data[event]["baseline"][-1][0])*i/100 for i in range(10,100,10)])
    
    
    risetime_perc =[]
    for event in range(len(mod_pulse)):
        for cell in range(len(data[event]["cell considered"])):
            norm_data = np.array(mod_pulse[event][data[event]["cell considered"][cell]][:data[event]["peak"][cell][1]:] - data[event]["baseline"][cell][0])
            for stage in data[event]["matrix cell x percentages"][cell]:
                risetime_perc.append( (np.where( np.abs(norm_data - stage) < 0.001, norm_data , .0)).nonzero()[0] )
                print( risetime_perc[-1] , stage)
                plt.plot(mod_pulse[event][data[event]["cell considered"][cell]][:data[event]["peak"][cell][1]:] - data[event]["baseline"][cell][0])
                plt.axhline(y=stage, color='g', linestyle='--')
                for i in risetime_perc[-1]:
                    plt.axvline(x=i, color='r', linestyle='--')
                plt.show()


    print(len(risetime_perc))
    print(risetime_perc[0])
        