import uproot
import numpy as np
import matplotlib.pyplot as plt
import os
from sys import argv


n_bins = 40
# input_path = "home/bobolde/coding/spacal/"
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

if __name__ == "__main__":
    files = os.listdir(input_path + "root_resolution/slanted_e")

    files = sorted(files, key=lambda x: int(x.split(".")[0].removeprefix("resolution_")))

    starting_energy = np.array([int(file.split(".")[0].removeprefix("resolution_")) for file in files])
    for file in files:
        cell_e, e_e = Resolution_convertion(input_path + "root_resolution/slanted_e/" + file)
        cell_pi, e_pi = Resolution_convertion(input_path + "root_resolution/slanted_pi/" + file)
        energy = file.removeprefix("resolution_").removesuffix(".root")
        en_e = np.zeros(1000)
        en_pi = np.zeros(1000)
        dist_e = np.zeros(1000)
        dist_pi = np.zeros(1000)
        for i in range(len(cell_e)):
            cell_e[i] /= e_e
            cell_pi[i] /= e_pi

            # Plot both cell distributions as histograms in the same plot
            plt.figure(figsize=(8, 6))
            bins = np.linspace(0, max([max(cell_e[i]), max(cell_pi[i])]), n_bins)
            plt.hist(cell_e[i], bins=bins, alpha=1, label="e" , histtype="step")
            plt.hist(cell_pi[i], bins=bins, alpha=1, label="pi", histtype="step")
            plt.title(f"Cell {i} Energy Distribution ({energy})")
            plt.xlabel("Energy percentage")
            plt.ylabel("Counts")
            plt.legend()
            plt.tight_layout()
            plt.savefig(input_path + f"data_analysis/e_pi_disc/energy_dist/{energy.removesuffix('.0GeV')}/cell_{i}_distribution.png")
            plt.clf()
            plt.close()

            en_e += cell_e[i]
            en_pi += cell_pi[i]

            if i in [0, 1, 2, 4, 5, 6, 8, 9, 10]:
                dist_e += cell_e[i]
                dist_pi += cell_pi[i]


            # Plot all cells in a matrix (e.g., 3x4 grid for 11 cells)
        fig, axes = plt.subplots(4, 4, figsize=(16, 16))
        axes = axes.flatten()
        for i in range(len(cell_e)):
            bins = np.linspace(0, max([max(cell_e[i]), max(cell_pi[i])]), n_bins)
            axes[i].set_title(f"Cell {i}")
            axes[i].set_xlabel("Energy percentage")
            axes[i].set_ylabel("Counts")
            axes[i].hist(cell_e[i], bins=bins, histtype="bar", alpha=0.5, label="e")
            axes[i].hist(cell_pi[i], bins=bins, histtype="bar", alpha=0.5, label="pi")
            axes[i].legend()
        # Hide unused subplots if any
        for j in range(len(cell_e), len(axes)):
            fig.delaxes(axes[j])
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(input_path + f"data_analysis/e_pi_disc/energy_dist/{energy.removesuffix('.0GeV')}/{energy}_cells_matrix.png")
        plt.clf()
        plt.close()

        bins = np.linspace(0.7, 1, n_bins)
        count_e, edges_e = np.histogram(dist_e, bins=bins, density=True)
        count_pi, edges_pi = np.histogram(dist_pi, bins=bins, density=True)
        plt.title(f"cluster cell energy distribution {energy}")
        plt.xlabel("Energy percentage")
        plt.ylabel("Normalized Counts")
        plt.hist(dist_e, bins=bins, histtype="stepfilled", color="#1f77b4", alpha=0.5, label="e")
        plt.hist(dist_pi, bins=bins, histtype="stepfilled", color="#ff7f0e", alpha=0.5, label="pi")
        plt.legend()
        # plt.show()
        plt.savefig(input_path + "data_analysis/e_pi_disc/energy_dist/cluster_dist/" + f"{energy}.png")
        plt.clf()
        plt.close()

        bins = np.linspace(0, max([max(en_e), max(en_pi)]), n_bins)
        plt.title(f"energy distribution {energy}")
        plt.xlabel("Energy percentage")
        plt.ylabel("Counts")
        plt.hist(en_e, bins=bins, histtype="bar", alpha=0.5, label="e")
        plt.hist(en_pi, bins=bins, histtype="bar", alpha=0.5, label="pi")
        plt.legend()
        # plt.show()
        plt.savefig(input_path + "data_analysis/e_pi_disc/energy_dist/" + f"{energy.removesuffix(".0GeV")}/{energy}_total_en.png")
        plt.clf()
        plt.close()
