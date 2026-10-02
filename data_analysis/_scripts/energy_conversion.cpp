#include <iostream> // Per std::cout
#include <fstream>  // Per std::ifstream
#include <string>   // Per std::string
#include <vector>   // Per std::vector
#include <sstream>  // Per std::stringstream

#include <TFile.h>
#include <TTree.h>


int nCells = 16;

double conversion( double y , double m , double q){
    return (y-q)/m;
}

int main(int argc, char const *argv[])
{

    std::ifstream infile("/home/bobolde/coding/spacal/data_analysis/energy_res/linear_regression_coefficients.csv");
    if (!infile.is_open()) {
        std::cerr << "Error opening file" << std::endl;
        return 1;
    }
    std::string line;
    std::vector<double> values;
    while (std::getline(infile, line)) {
        std::stringstream ss(line);
        std::string token;
        double num1, num2;
        if (std::getline(ss, token, ',')) {
            num1 = std::stod(token);
        }
        if (std::getline(ss, token, ',')) {
            num2 = std::stod(token);
        }
        values.push_back(num1);
        values.push_back(num2);

    }
    infile.close();



    // Open a ROOT file
    TFile *inFile = TFile::Open(argv[1], "READ");
    if (!inFile || inFile->IsZombie()) {
        std::cerr << "Error opening ROOT file" << std::endl;
        return 1;
    }

    

    // Example: Access a TTree named "tree"
    auto tree = (TTree*)inFile->Get("tree");
    
    
    std::vector<double> * en_tot ;
    std::vector<int> * VMod = 0;
    std::vector<std::vector<double> * > en_cell;
    tree->SetBranchAddress("enTotal", &en_tot);

    for( int i = 0; i < nCells; i++){
        std::string branchName = "mod0_cell" + std::to_string(i) + "_reco_energy";
        tree->SetBranchAddress(branchName.c_str(), &en_cell[i]);
    }
    auto nEntries = tree->GetEntries();

    inFile->Close();
    delete inFile;

    TFile *outFile = TFile::Open(argv[2] , "UPDATE");
    if (!outFile || outFile->IsZombie()){
        TFile *outFile = TFile::Open(argv[2] , "CREATE");
        if (!outFile || outFile->IsZombie()){
            std::cerr << "ERROR creating output file" << std::endl;
        }
    }else{
        outFile->Delete("energy_resolution;*");
    }

    for( int i=0; i < nCells ; i++){
        for( int j = 0; i < en_cell[i].size() ; j++){
         en_cell[i][j] = conversion( en_cell[i][j] , values[0] , values[1]);
        }

    }
    for( int j = 0; j < en_tot -> size() ; j++){
            en_tot[j] = conversion( en_tot.at(j) , values[0] , values[1]);
    }

    TTree *en_tree = new TTree("energy_resolution","energy resoluton");
    en_tree -> Branch( "full_reconstructed_energy" , &en_tot , "total energy reconstructed with voltages summed beforehand");
    for (int i = 0; i < nCells; i++){
        en_tree -> Branch( (("cell"+std::to_string(i)+"_recunstructed_energy").c_str() , &en_cell[i] , "energy reconstructed of the single cell"));
    }

    en_tree -> Fill();
    outFile -> Write();
    outFile -> Close();
    

    
    std::cout <<"hello world"<<std::endl;
    return 0;
}
