import uproot
import numpy as np
import matplotlib.pyplot as plt
import os
from sys import argv
import seaborn as sns
from sklearn.metrics import roc_curve, auc

# Define start and end percentage for energy threshold
p_start = 10
p_end = 90

n_bins = 50

section = 60

# Output directory for results
output_dir = ""
# Check if threshold file already exists
threshold_exist = os.path.exists(output_dir + f"/end{p_end}%/threshold.csv")



def Resolution_convertion(path: str):
    """
    Reads ROOT file and extracts 'mod0_ph' and 'mod0_pulse' arrays from the tree.

    Parameters
    ----------
    path : str
        Path to the ROOT file.

    Returns
    -------
    risetime_diff : np.ndarray
        Difference in risetime between p_end and p_start.
    e_cell : list of np.ndarray
        List of energy arrays for each cell.
    e_tot : np.ndarray
        Array of total reconstructed energy.
    """
    file = uproot.open(path)
    t_res = file["time_resolution"]
    e_res = file["energy_resolution"]

    t_keys = t_res.keys()
    e_keys = e_res.keys()[1::]

    risetime = []
    # Extract risetime arrays for p_start and p_end
    for key in t_keys:
        if str(p_start) in key and not "error" in key:
            risetime.append(t_res[key].array(library="np"))
        if str(p_end) in key and not "error" in key:
            risetime.append(t_res[key].array(library="np"))
    # Extract total reconstructed energy
    e_tot = e_res["full_reconstructed_energy"].array(library="np")
    e_cell = []
    # Extract cell indices from keys
    cell = [int(key.split("_")[1]) for key in t_keys]
    # Ensure all risetime arrays are from the same cell
    if not all(x == cell[0] for x in cell):
        raise KeyError("not every raisetime is from the same cell")
    # Extract energy arrays for each cell
    for key in e_keys:
        e_cell.append(e_res[key].array(library="np"))
    # Return difference in risetime, cell energies, and total energy
    return risetime[1] - risetime[0], e_cell, e_tot

def true_positive( frac , tot):
    return frac/tot

if __name__ == "__main__":
    # List all ROOT files for electrons
    files = os.listdir("root_resolution/slanted_e")


    # Sort files by energy value
    files = sorted(files, key=lambda x: int(x.split(".")[0].removeprefix("resolution_")))

    # Extract starting energies from filenames
    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])
    idx = 0
    for file in files:
        # Extract risetime and energy for electrons and pions
        r_e, cell_e, e_e = Resolution_convertion("root_resolution/slanted_e/" + file)
        r_pi, cell_pi, e_pi = Resolution_convertion("root_resolution/slanted_pi/" + file)
        energy = file.removeprefix("resolution_").removesuffix(".root")

        # Use the same binning for both electrons and pions
        risetime_bins = np.histogram_bin_edges(np.concatenate([r_e, r_pi]), bins=50)

        # Plot and save risetime histogram
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.hist(r_e, bins=risetime_bins, alpha=0.7, label='Electron')
        ax.hist(r_pi, bins=risetime_bins, alpha=0.7, label='Pion')
        ax.set_title(f'Risetime Histogram (Energy={energy})')
        ax.set_xlabel('Risetime')
        ax.set_ylabel('Counts')
        ax.legend()
        plt.tight_layout()
        plt.savefig(f"end{p_end}%_risetime_hist_{energy}GeV.png")
        plt.close(fig)

        # Create new figure for energy histogram
        # normalize energies by beam momentum
        # normalize energies by beam momentum
        e_e_norm = (e_e) / starting_energy[idx]
        e_pi_norm = (e_pi) / starting_energy[idx]

        # compute and plot ROC for energy-based classifier

        true_pos = []
        false_pos = []
        m_val = min(min(e_e_norm) , min(e_pi_norm))
        for i in np.arange( m_val, 1 , (1-m_val)/section):

            tp = np.count_nonzero(e_e_norm > i)
            fp = np.count_nonzero(e_pi_norm > i)
            print( tp , fp , i)
            true_pos.append(true_positive(tp, len(e_e_norm)))
            false_pos.append(true_positive(fp, len(e_pi_norm)))
        fpr, tpr, _ = roc_curve(true_pos, false_pos)
        auc_val = auc(fpr, tpr)

        fig_roc, ax_roc = plt.subplots(figsize=(6, 5))
        ax_roc.plot(fpr, tpr, label=f'AUC = {auc_val:.3f}')
        ax_roc.plot([0, 1], [0, 1], 'k--', alpha=0.5)
        ax_roc.set_xlabel('False Positive Rate')
        ax_roc.set_ylabel('True Positive Rate')
        ax_roc.set_title(f'ROC (Energy) (Energy={energy})')
        ax_roc.legend()
        plt.tight_layout()
        plt.savefig(f"end{p_end}%_roc_energy_{energy}.png", dpi=150)
        plt.close(fig_roc)

        # compute and plot ROC for risetime-based classifier
        # r_e and r_pi were computed above (risetime differences for e/pi)
        y_true_r = np.concatenate([np.ones_like(r_e), np.zeros_like(r_pi)])
        y_scores_r = np.concatenate([r_e, r_pi])
        fpr_r, tpr_r, _ = roc_curve(y_true_r, y_scores_r)
        auc_r = auc(fpr_r, tpr_r)

        fig_roc_r, ax_roc_r = plt.subplots(figsize=(6, 5))
        ax_roc_r.plot(fpr_r, tpr_r, label=f'AUC = {auc_r:.3f}')
        ax_roc_r.plot([0, 1], [0, 1], 'k--', alpha=0.5)
        ax_roc_r.set_xlabel('False Positive Rate')
        ax_roc_r.set_ylabel('True Positive Rate')
        ax_roc_r.set_title(f'ROC (Risetime) (Energy={energy})')
        ax_roc_r.legend()
        plt.tight_layout()
        plt.savefig(f"end{p_end}%_roc_risetime_{energy}.png", dpi=150)
        plt.close(fig_roc_r)

        # shared bins based on both distributions
        e_combined = np.concatenate([e_e_norm, e_pi_norm])
        e_bins = np.linspace(0, max(1e-8, e_combined.max()), n_bins)


        fig_energy, ax_energy = plt.subplots(figsize=(6, 5))
        ax_energy.hist(e_e_norm, bins=e_bins, alpha=0.7, label='Electron', color="#FF7F0E")
        ax_energy.hist(e_pi_norm, bins=e_bins, alpha=0.7, label='Pion', color="#1F77B4")


        ax_energy.set_title(f'Energy Histogram (Energy={energy})')
        ax_energy.set_xlabel('E_tot / p')
        ax_energy.set_ylabel('Counts')
        ax_energy.legend()
        plt.tight_layout()
        plt.savefig(f"end{p_end}%_energy_hist_{energy}.png", dpi=150)
        plt.close(fig_energy)
        idx += 1

