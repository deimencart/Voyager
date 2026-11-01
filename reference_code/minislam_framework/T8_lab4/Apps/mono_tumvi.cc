/**
* This file is part of Mini-SLAM
*
* Copyright (C) 2021 Juan J. Gómez Rodríguez and Juan D. Tardós, University of Zaragoza.
*
* Mini-SLAM is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
* License as published by the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* Mini-SLAM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
* the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License along with Mini-SLAM.
* If not, see <http://www.gnu.org/licenses/>.
*/

/*
 * A demo showing the Mini-SLAM library processing a sequence of the TUM-VI dataset
 * using the KannalaBrandt8 fish-eye camera model.
 */

#include "DatasetLoader/TUMVILoader.h"
#include "System/MiniSLAM.h"

#include <opencv2/opencv.hpp>

using namespace std;

int main(int argc, char **argv){
    //Check program parameters
    if(argc != 4){
        cerr << "[Error]: you need to invoke the program with 3 parameters: " << endl;
        cerr << "\t./mono_tumvi <dataset_path> <timestamps_path> <groundtruth_path>" << endl;
        cerr << "Finishing execution..." << endl;
        return -1;
    }

    //Load dataset sequence
    string datasetPath    = argv[1];
    string timestampsPath = argv[2];
    string groundTruthPath = argv[3];

    TUMVILoader sequence(datasetPath, timestampsPath, groundTruthPath);

    //Create SLAM system with TUM-VI config (KannalaBrandt8)
    //MiniSLAM SLAM("Data/TUM-VI.yaml");
    MiniSLAM SLAM("Data/EuRoC.yaml");


    //File to store the trajectory
    ofstream trajectoryFile("trajectory.txt");
    if(!trajectoryFile.is_open()){
        cerr << "[Error]: could not open the trajectory file, aborting..." << endl;
        return -2;
    }

    //Process the sequence
    cv::Mat currIm;
    double currTs;
    for(int i = 0; i < sequence.getLenght(); i++){
        sequence.getLeftImage(i, currIm);
        sequence.getTimeStamp(i, currTs);

        Sophus::SE3f Tcw;
        if(SLAM.processImage(currIm, Tcw)){
            Sophus::SE3f Twc = Tcw.inverse();
            trajectoryFile << setprecision(17) << currTs << "," << setprecision(7)
                           << Twc.translation()(0) << ","
                           << Twc.translation()(1) << ","
                           << Twc.translation()(2) << ","
                           << Twc.unit_quaternion().x() << ","
                           << Twc.unit_quaternion().y() << ","
                           << Twc.unit_quaternion().z() << ","
                           << Twc.unit_quaternion().w() << endl;
        }
    }

    trajectoryFile.close();

    return 0;
}
