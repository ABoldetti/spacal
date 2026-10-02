import uproot
import numpy as np
import matplotlib.pyplot as plt
import os
from sys import argv
from sklearn.metrics import auc


n_bins = 40

remove_peak = 0.95

l_cut = 0.8
u_cut = 0.9
sections = 80
input_path = "/home/bobolde/coding/spacal/"
input_path = "/Users/ibolde/coding/spacal/"

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

    e_tot = e_res["full_reconstructed_energy"].array(library="np")
    e_cell = []
    cell = [int(key.split("_")[1]) for key in t_keys]
    if not all(x == cell[0] for x in cell):
        raise KeyError("not every raisetime is from the same cell")
    for key in e_keys:
        e_cell.append( e_res[key].array(library="np"))
    
    return e_cell , e_tot

def true_positive( frac , tot):
    return frac/tot


if __name__ == "__main__":
    files = os.listdir(input_path + "root_resolution/slanted_e")

    files = sorted(files, key=lambda x: int(x.split(".")[0].removeprefix("resolution_")))

    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])
    for file in files:
        cell_e, e_e = Resolution_convertion(input_path + "root_resolution/slanted_e/" + file)
        cell_pi, e_pi = Resolution_convertion(input_path + "root_resolution/slanted_pi/" + file)
        energy = file.removeprefix("resolution_").removesuffix(".root")

        dist_e = np.zeros(1000)
        dist_pi = np.zeros(1000)
        f_cell_e = cell_e[5]/e_e
        f_cell_pi = (cell_pi[5]/e_pi)[(cell_pi[5]/e_pi)<remove_peak]

        for i in range( len(cell_e)):

            cell_e[i] /= e_e
            cell_pi[i] /= e_pi

            if i in [0, 1, 2, 4, 5, 6, 8, 9, 10]:
                dist_e += cell_e[i]
                dist_pi += cell_pi[i]


        dist_pi = 1 - np.abs(np.array(dist_pi) - np.mean(dist_e))
        dist_e = 1 - np.abs(np.array(dist_e) - np.mean(dist_e))

        # Plot histograms of dist_e and dist_pi
        plt.figure(figsize=(7, 5))
        plt.hist(dist_e, bins=40, alpha=0.7, label='dist_e', color='blue', density=True)
        plt.hist(dist_pi, bins=40, alpha=0.7, label='dist_pi', color='orange', density=True)
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.title(f'Histogram of dist_e and dist_pi at {energy}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        # plt.show()
        plt.clf()
        plt.close()

        
        true_pos = []
        false_pos = []
        for i in np.arange(0 , 1 , 1/sections):
            print( i)
            tp = np.count_nonzero(f_cell_e > i)
            fp = np.count_nonzero(f_cell_pi > i)
            true_pos.append( true_positive(tp, len(dist_e)))
            false_pos.append( true_positive(fp, len(dist_pi)))

        roc_auc = auc(false_pos, true_pos)
        plt.figure(figsize=(7, 5))
        plt.plot(false_pos, true_pos, marker='o', linestyle='-', label=f'Energy {energy} (AUC={roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--', label='Random (AUC=0.5)')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve for electrons at {energy}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(input_path + "data_analysis/e_pi_disc/ROC/ROC_cell5_" + energy + ".pdf")
        # plt.show()
        plt.clf()
        plt.close()


        e_cell_e = f_cell_e[(f_cell_e >= l_cut) & (f_cell_e <= u_cut)]
        e_cell_pi = f_cell_pi[(f_cell_pi >= l_cut) & (f_cell_pi <= u_cut)]

        e_cell_pi = 1 - np.abs( np.array(e_cell_pi) - np.mean(e_cell_e))
        e_cell_e = 1 - np.abs( np.array(e_cell_e) - np.mean(e_cell_e))

        # Plot histograms of e_cell_e and e_cell_pi
        plt.figure(figsize=(7, 5))
        plt.hist(e_cell_e, bins=40, alpha=0.7, label='e_cell_e', color='purple')
        plt.hist(e_cell_pi, bins=40, alpha=0.7, label='e_cell_pi', color='brown')
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.title(f'Histogram of e_cell_e and e_cell_pi at {energy} (with cuts)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.show()
        plt.clf()
        plt.close()
        

        true_pos = []
        false_pos = []
        m_val = min(min(e_cell_e) , min(e_cell_pi))
        for i in np.arange( m_val, 1 , (1-m_val)/sections):

            tp = np.count_nonzero(e_cell_e > i)
            fp = np.count_nonzero(e_cell_pi > i)
            print( tp , fp , i)
            true_pos.append(true_positive(tp, len(e_cell_e)))
            false_pos.append(true_positive(fp, len(e_cell_pi)))

        roc_auc = auc(false_pos, true_pos)
        plt.figure(figsize=(7, 5))
        plt.plot(false_pos, true_pos, marker='o', linestyle='-', label=f'Energy {energy} (AUC={roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--', label='Random (AUC=0.5)')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve for electrons at {energy} with cuts')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(input_path + "data_analysis/e_pi_disc/ROC/cutted_ROC_cell5_" + energy + ".pdf")
        plt.show()
        plt.clf()
        plt.close()


        f_cell_pi = 1 - np.abs( np.array(f_cell_pi) - np.mean(f_cell_e))
        f_cell_e = 1 - np.abs( np.array(f_cell_e) - np.mean(f_cell_e))
        # Plot histograms of f_cell_e and f_cell_pi
        plt.figure(figsize=(7, 5))
        plt.hist(f_cell_e, bins=40, alpha=0.7, label='f_cell_e', color='green', density=True)
        plt.hist(f_cell_pi, bins=40, alpha=0.7, label='f_cell_pi', color='red', density=True)
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.title(f'Histogram of f_cell_e and f_cell_pi at {energy}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        # plt.show()
        plt.clf()
        plt.close()
        true_pos = []
        false_pos = []
        for i in np.arange(0 , 1 , 1/sections):
            tp = np.count_nonzero(f_cell_e > i)
            fp = np.count_nonzero(f_cell_pi > i)
            true_pos.append( true_positive(tp, len(f_cell_e)))
            false_pos.append( true_positive(fp, len(f_cell_pi)))

        roc_auc = auc(false_pos, true_pos)
        plt.figure(figsize=(7, 5))
        plt.plot(false_pos, true_pos, marker='o', linestyle='-', label=f'Energy {energy} (AUC={roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--', label='Random (AUC=0.5)')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve for electrons at {energy}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(input_path + "data_analysis/e_pi_disc/ROC/ROC_cell5_" + energy + ".pdf")
        # plt.show()
        plt.clf()
        plt.close()

        

