// ###########################################################################
// ### Short macro to visualise the output of the simReadout SPACAL simulation.
// ### The input file name, module number, and event desired can be selected by the three variables heredown.
// ### 

#include <iostream>
#include <vector>

#include "TROOT.h"
#include "TFile.h"
#include "TTree.h"
#include "TBranch.h"
#include "TInterpreter.h"



int nModule = 0;                                               // MODULE DESIRED
int nEvent  = 0;                                                // EVENT DESIRED



void edit_pulseVisualization(std::string inFile = "OutGroupd_0" , std::string inFolder =".", std::string outFolder =".")        // INPUT FILE NAME
{
    
    std::string outFileName = outFolder + "/" + inFile + "_pulse.root";                                //OUTPUT FILE NAME
    inFile+=".root";
    std::cout << ".Start." << std::endl;


    // --- FAST DICTIONARIES COMPILATION ON THE FLY
    gInterpreter -> GenerateDictionary("std::vector<std::vector<float>>", "vector");
    gInterpreter -> GenerateDictionary("std::vector<std::vector<std::vector<float>>>", "vector");
    gStyle->SetOptStat(0000);



    TFile f ((inFolder+"/"+inFile).c_str(), "READ");
    auto TT = (TTree*) f.Get("tree");
    std::string moduleName = "mod" + std::to_string(nModule);

    std::vector<std::vector<float>> *VVec=0;
    std::vector<int> * VPh = 0;
    std::vector<int> * VMod = 0;
    int entry = 0;


    // --- Assign branches' addresses
    TT->SetBranchAddress("modulesHit", &VMod);
    TT->SetBranchAddress( (moduleName + "_pulse").c_str(), &VVec);
    TT->SetBranchAddress( (moduleName + "_ph").c_str(), &VPh);
    auto entries = TT->GetEntries();




    // --- Load the desired entry
    std::cout << "Loading entry " << nEvent << "\n";
    if (nEvent >= entries) {
        std::cout << "ERROR! There are only " << entries << " entries!" << std::endl;
        return;
    }

    TT->GetEntry(nEvent);


    // --- Check which modules were hit.
    std::cout << "In this event the following modules were hit: ";
    for (auto && mod : *VMod) std::cout << mod << " " ;
    std::cout << std::endl;



    std::cout << "Looping over the cells of module " << nModule << std::endl;
    TFile outFile (outFileName.c_str(), "RECREATE");
    for (size_t iCell = 0; iCell < VPh->size(); ++iCell)
    {
        // --- How many photons detected in this cell
        std::cout << "Cell " << iCell << " Photons detected: " << VPh->at(iCell) << std::endl;


        // --- Make a histogram with the pulse
        auto samples = VVec->at(iCell).size();
        TCanvas c (("canvas"+std::to_string(iCell)).c_str(), ("canvas"+std::to_string(iCell)).c_str() , 600, 400 );
        TH1F h ( ("Pulse_"+moduleName+"_cell"+std::to_string(iCell)).c_str(), ("Pulse_"+moduleName+"_cell"+std::to_string(iCell)).c_str(), samples, 0, samples);
        for (int i = 0; i < samples; i++)
        {
            h.SetBinContent(i+1, VVec->at(iCell).at(i));
        }

        h.GetXaxis()->SetTitle("Time [sampling units]");
        h.GetYaxis()->SetTitle("Voltage [V]");
        h.DrawClone();
        c.DrawClone();
        c.Write();

    }





    std::cout << ".End." << std::endl;
}
