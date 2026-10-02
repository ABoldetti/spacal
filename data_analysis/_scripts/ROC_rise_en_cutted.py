import uproot
import numpy as np
import matplotlib.pyplot as plt
import os

from sklearn.metrics import auc



p_start = 10
p_end = 90

output_dir = "data_analysis/e_pi_disc"


remove_peak = 0.98
l_cut = 0.7
u_cut = 0.900
sections = 80

r_bound = 1000
l_bound = 0
u_bound = 1000
d_bound = 0

x_len = 10
y_len = 10

def Resolution_convertion(path: str):
    """
    Reads ROOT file and extracts 'mod0_ph' and 'mod0_pulse' arrays from the tree.

    Parameters
    ----------
    path : str
        Path to the ROOT file.

    Returns
    -------
    mod_ph : np.ndarrayx == cell[0]
        Array of photon counts.
    mod_pulse : np.ndarray
        Array of pulse shapes.
    """
    file = uproot.open(path)
    t_res = file["time_resolution"]
    e_res = file["energy_resolution"]

    t_keys=t_res.keys()
    e_keys=e_res.keys()[1::]

    risetime = []
    
    for key in t_keys:
        if str(p_start) in key and not "error" in key:
            risetime.append( t_res[key].array(library="np") )
        if str(p_end) in key and not "error" in key:
            risetime.append( t_res[key].array(library="np"))
    e_tot = e_res["full_reconstructed_energy"].array(library="np")
    e_cell = []
    cell = [int(key.split("_")[1]) for key in t_keys]
    if not all(x == cell[0] for x in cell):
        raise KeyError("not every raisetime is from the same cell")
    for key in e_keys:
        e_cell.append( e_res[key].array(library="np"))
    
    return risetime[1] - risetime[0] , e_cell , e_tot

def true_positive( frac , tot):
    return frac/tot

if __name__ =="__main__":
    files = os.listdir("root_resolution/slanted_e")

    os.makedirs( output_dir + f"/end{p_end}%" , exist_ok= True)

    files = sorted(files, key=lambda x: int(x.split(".")[0].removeprefix("resolution_")))


    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])

    for file in files:

        energy = file.removeprefix("resolution_").removesuffix(".root")
        r_e , cell_e , e_e = Resolution_convertion( "root_resolution/slanted_e/" + file)
        r_pi , cell_pi , e_pi = Resolution_convertion( "root_resolution/slanted_pi/" + file)

        mask_e = r_e > 0
        mask_pi = r_pi > 0
        e_e = e_e[mask_e]
        r_e = r_e[mask_e]
        e_pi = e_pi[mask_pi]
        r_pi = r_pi[mask_pi]
        cell_e = [np.array(c)[mask_e] for c in cell_e]
        cell_pi = [np.array(c)[mask_pi] for c in cell_pi]

        # Read the CSV file into a 5x5 matrix of floats
        # with open(output_dir + f"/end{p_end}%/threshold.csv", "r") as myfile:
        #     matrix = [list(map(float, line.strip().split(','))) for line in myfile if line.strip()]

        # energies_idx = [matrix[i][-1] for i in range( len(matrix))]
        # if float(file.split(".")[0].removeprefix("resolution_")) in energies_idx:
        #     idx = energies_idx.index(float(file.split(".")[0].removeprefix("resolution_")))
        #     l_bound = matrix[idx][0]
        #     d_bound = matrix[idx][1]
        #     r_bound = matrix[idx][2]
        #     u_bound = matrix[idx][3]



        
        # mask_e = (e_e >= l_bound) & (e_e <= r_bound) & (r_e >= d_bound) & (r_e <= u_bound)
        # mask_pi = (e_pi >= l_bound) & (e_pi <= r_bound) & (r_pi >= d_bound) & (r_pi <= u_bound)

        # sliced_e_e = e_e[mask_e]
        # sliced_r_e = r_e[mask_e]
        # sliced_e_pi = e_pi[mask_pi]
        # sliced_r_pi = r_pi[mask_pi]
        mask_e = ((cell_e[5]/e_e) < max(cell_e[5]/e_e)) & ((cell_e[5]/e_e) > min(cell_e[5]/e_e))
        mask_pi = ((cell_pi[5]/e_pi) < max(cell_e[5]/e_e)) & ((cell_pi[5]/e_pi) > min(cell_e[5]/e_e))
        
        
        with open(output_dir + f"/end{p_end}%/threshold.csv", "r") as myfile:
            matrix = [list(map(float, line.strip().split(','))) for line in myfile if line.strip()]

        energies_idx = [matrix[i][-1] for i in range(len(matrix))]
        if float(file.split(".")[0].removeprefix("resolution_")) in energies_idx:
            idx = energies_idx.index(float(file.split(".")[0].removeprefix("resolution_")))
            d_bound = matrix[idx][1]
            u_bound = matrix[idx][3]
            # Add masks to exclude r values outside [d_bound, u_bound]
            mask_e = mask_e & (r_e >= d_bound) & (r_e <= u_bound)
            mask_pi = mask_pi & (r_pi >= d_bound) & (r_pi <= u_bound)

        f_cell_e = (cell_e[5]/e_e)[mask_e]
        r_e = r_e[mask_e]
        f_cell_pi = (cell_pi[5]/e_e)[mask_pi]
        r_pi = r_pi[mask_pi]


        
        r_e = r_e[(f_cell_e< max(f_cell_e)) & (f_cell_e > min(f_cell_e))]

        r_pi = r_pi[(f_cell_pi< max(f_cell_e)) & (f_cell_pi > min(f_cell_e))]
        f_cell_pi = f_cell_pi[(f_cell_pi< max(f_cell_e)) & (f_cell_pi > min(f_cell_e))]
        f_cell_e = f_cell_e[(f_cell_e< max(f_cell_e)) & (f_cell_e > min(f_cell_e))]

        plt.figure(figsize=(7, 5))
        plt.scatter(f_cell_e, r_e, color="orange", label="Electron")
        plt.scatter(f_cell_pi, r_pi, color="blue", label="Pion")
        plt.xlabel("energy distribution (cell_e[5]/e_e or cell_pi[5]/e_pi)")
        plt.ylabel("Risetime [ns]")
        plt.title(f"Scatter plot of f_cell vs risetime for energy {energy}")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.show()
        # plt.savefig(output_dir + f"/end{p_end}%/scatter_fcell_r_{energy}.pdf")
        plt.clf()
        plt.close()

        r_pi = 1 - (np.abs( np.array(r_pi) - np.mean(r_e)))/np.mean(r_e)
        r_e = 1 - (np.abs( np.array(r_e) - np.mean(r_e)))/np.mean(r_e)

        plt.scatter(f_cell_e, r_e, color="orange", label="Electron")
        plt.scatter(f_cell_pi, r_pi, color="blue", label="Pion")
        plt.show()
        if len(r_pi) == 0 :
            min_val = min(r_e)
            max_val = max(r_e)
        else:
            min_val = min(min(r_e) , min(r_pi))
            max_val = max(max(r_e) , max(r_pi))
        true_pos = []
        false_pos = []

        
        for i in np.arange( min_val, max_val , (max_val - min_val)/sections):

            tp = np.count_nonzero(r_e > i)
            fp = np.count_nonzero(r_pi > i)
            true_pos.append(true_positive(tp, len(r_e)))
            if len(r_pi) == 0:
                false_pos.append(0)
            else:
                false_pos.append(true_positive(fp, len(r_pi)))

        roc_auc = auc(false_pos, true_pos)
        plt.figure(figsize=(7, 5))
        plt.plot(false_pos, true_pos, marker='o', linestyle='-', label=f'Energy {energy} (AUC={roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--', label='Random (AUC=0.5)')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve of risetimes for {energy} particles ')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig("data_analysis/e_pi_disc/ROC_rise/ROC_risetime_" + energy + ".pdf")
        plt.show()
        plt.clf()
        plt.close()


    
    
    
    
    
    
    
    
    
        

        


