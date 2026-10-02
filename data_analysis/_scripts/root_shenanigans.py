import uproot
import ROOT

f = uproot.open("data_analysis/root_resolution/slanted_e/resolution_1.0GeV.root")
        

output_root_file = ROOT.TFile("data_analysis/root_resolution/slanted_e/resolution_1.0GeV.root", "UPDATE")


f = uproot.open("data_analysis/root_resolution/slanted_e/resolution_1.0GeV.root")
print(f.keys())
for key in f.keys():
    if "energy_resolution" in key:
        output_root_file.Delete(key)
f.close()
