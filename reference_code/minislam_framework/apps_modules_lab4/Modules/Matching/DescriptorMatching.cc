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

#include "DescriptorMatching.h"

using namespace std;

int HammingDistance(const cv::Mat &a, const cv::Mat &b){
    const int *pa = a.ptr<int32_t>();
    const int *pb = b.ptr<int32_t>();

    int dist=0;

    for(int i=0; i<8; i++, pa++, pb++){
        unsigned  int v = *pa ^ *pb;
        v = v - ((v >> 1) & 0x55555555);
        v = (v & 0x33333333) + ((v >> 2) & 0x33333333);
        dist += (((v + (v >> 4)) & 0xF0F0F0F) * 0x1010101) >> 24;
    }

    return dist;
}



int searchForInitializaion(Frame& refFrame, Frame& currFrame, int th, vector<int>& vMatches, std::vector<cv::Point2f>& vPrevMatched){
    //inicias y extraes matches llenando el vector de matches con -1 (no match) y el vector de coordenadas de los puntos del frame anterior con las coordenadas de los keypoints del frame anterior
    fill(vMatches.begin(),vMatches.end(),-1);

    vector<size_t> vIndicesToCheck(100);
    //Obtienes los putnos de interés del frame anterior y sus descriptores matematicos
    vector<cv::KeyPoint>& vRefKeys = refFrame.getKeyPoints();

    vector<int> vMatchedDistance(vRefKeys.size(),INT_MAX);
    vector<int> vnMatches21(vRefKeys.size(),-1);
    
    //Utilizas caracteristicas ORB en todas sus tareas usando FAST para extraer los puntos de interés y ORB para extraer los descriptores matematicos de cada punto de interés. Para emparejar los puntos de interés entre el frame anterior y el frame actual, se puede usar la distancia de Hamming entre los descriptores ORB. Para cada punto de interés del frame anterior, se busca el punto de interés del frame actual que tenga la menor distancia de Hamming con un umbral dado. Si la distancia es menor que el umbral, se considera que hay una coincidencia entre los dos puntos de interés. El vector vMatches se llena con los índices de los puntos de interés del frame actual que coinciden con los puntos de interés del frame anterior, y el vector vPrevMatched se llena con las coordenadas de los puntos de interés del frame anterior que tienen una coincidencia en el frame actual.
    cv::Mat refDesc = refFrame.getDescriptors();
    cv::Mat currDesc = currFrame.getDescriptors();

    int nMatches = 0;

    //Inicias un ciclo para evaluar cada punto en la primera imagen 

    const int minOctave = 0, maxOctave = 0;
    for(size_t i = 0; i < vRefKeys.size(); i++){
        //Only search matches with KeyPoints in the finest scale
        if(vRefKeys[i].octave > maxOctave){
            continue;
        }

        /*
         * Your code for Lab 3 - Task 1 here!
         */
        //Extraes un feature
        //Para el punto ACTUAL solicita a current frame 
        // que te de una lista de candidatos a hacer match con ese punto, es decir, que te de los puntos del frame actual que estén cerca del punto del frame anterior. Para esto puedes usar la función getFeaturesInArea() del Frame, que te devuelve los índices de los puntos del frame actual que están dentro de un radio dado alrededor de las coordenadas del punto del frame anterior. 
        //El radio es de 100 pixeles. 
        cv::Mat desc1 = refDesc.row(i);
        //Where to look 
        int windowSize = 100; 
        //Buscas en vector de candidatos para ese punto 
        vIndicesToCheck.clear();

        // Pedimos la imagen actual
        /*
        Al utilizar una búsqueda guiada en un área limitada, se reduce drásticamente el coste computacional 
        permitiendo el funcionamiento en tiempo 
        */ 
        currFrame.getFeaturesInArea(vRefKeys[i].pt.x,vRefKeys[i].pt.y,windowSize,minOctave,maxOctave,vIndicesToCheck);

        if(vIndicesToCheck.empty()){
            continue;
        }

        //Consencius of candidates 
        /*
        Itera unicamente los candidatos encontrados en la nueva ventana
        Extratendo el descripto de cada candidato y lo compara con el punto punto original utilizando 
        HammingDistance Me quedo con el mejor match. 
        */
        int bestDist = 255; int secondBestDist = 255;
        int bestIdx = -1;
        for(size_t idx : vIndicesToCheck){ 
            cv::Mat desc2 = currDesc.row(idx);
            int dist = HammingDistance(desc1,desc2);

        //Esto solo es una comparacion del concenso de los candidatos, no es un umbral de distancia.
            if(dist < bestDist){
                secondBestDist = bestDist;
                bestDist = dist;
                bestIdx = idx;
            }
            else if(dist < secondBestDist){
                secondBestDist = dist;
            }
        }
        /*
        Para que la distancia sea considera valid e insertado en el vector de resultados vMatches[i] = bestIdx
        , la similitud debe ser nehir que un umbral tolerancia maximo (th)
        críticamente, la mejor distancia debe ser al menos un 10% más pequeña que la segunda mejor distancia
        */
        if(bestDist <= th && (float)bestDist < (float(secondBestDist)*0.9)){
            vMatches[i] = bestIdx;
            nMatches++;
        }
    }

    // fin del ciclo que hemos escrito
    for(size_t i = 0; i < vMatches.size(); i++){
        if(vMatches[i] != -1){
            vPrevMatched[i]=currFrame.getKeyPoint(vMatches[i]).pt;
        }
    }

    //cout << "Frame paired with " << nMatches << " matches found." << endl;
    //cout << "Match ratio: " << float(nMatches)/float(vRefKeys.size())  * 100 << endl;

    return nMatches;
}

int guidedMatching(Frame& refFrame, Frame& currFrame, int th, std::vector<int>& vMatches, int windowSizeFactor){
    currFrame.clearMapPoints();
    fill(vMatches.begin(),vMatches.end(),-1);
    vector<size_t> vIndicesToCheck(100);

    vector<shared_ptr<MapPoint>> vRefMapPoints = refFrame.getMapPoints();

    shared_ptr<CameraModel> currCamera = currFrame.getCalibration();
    Sophus::SE3f Tcw = currFrame.getPose();

    int nMatches = 0;
    for(size_t i = 0; i < vRefMapPoints.size(); i++){
        if(!vRefMapPoints[i]){
            continue;
        }

        //Project map point into the current frame
        Eigen::Vector3f p3Dcam = Tcw * vRefMapPoints[i]->getWorldPosition();
        cv::Point2f uv = currCamera->project(p3Dcam);

        //Clear previous matches
        vIndicesToCheck.clear();

        //Get last octave in which the point was seen
        int nLastOctave = refFrame.getKeyPoint(i).octave;

        //Search radius depends on the size of the point in the image
        float radius = 15 * windowSizeFactor * currFrame.getScaleFactor(nLastOctave);

        //Get candidates whose coordinates are close to the current point
        currFrame.getFeaturesInArea(uv.x,uv.y,radius,nLastOctave-1,nLastOctave+1,vIndicesToCheck);

        cv::Mat desc = vRefMapPoints[i]->getDescriptor();

        //Match with the one with the smallest Hamming distance
        int bestDist = 255, secondBestDist = 255;
        size_t bestIdx;
        for(auto j : vIndicesToCheck){
            if(currFrame.getMapPoint(j)){
                continue;
            }

            int dist = HammingDistance(desc.row(0),currFrame.getDescriptors().row(j));

            if(dist < bestDist){
                secondBestDist = bestDist;
                bestDist = dist;
                bestIdx = j;
            }
            else if(dist < secondBestDist){
                secondBestDist = dist;
            }
        }
        if(bestDist <= th && (float)bestDist < (float(secondBestDist)*0.9)){
            vMatches[i] = bestIdx;
            currFrame.setMapPoint(bestIdx,vRefMapPoints[i]);
            nMatches++;
        }
    }

    return nMatches;
}

//La funcio mejora la aprecision de rastreo usado el mapa 3D local. 
/*
parametros de entrada:
-Frame actual
-umbral de distancia de hamming para considerar un match valido 
vMapPoints que es una lista de ountos 3D conocidos en el mapa local (¿Que es el mapa local y el mapa gloabl??)

parametros de salida:
-Numero de matches encontrados
*/
int searchWithProjection(Frame& currFrame, int th, std::vector<std::shared_ptr<MapPoint>>& vMapPoints){
    CameraModel* currCalibration = currFrame.getCalibration().get();
    //propiedades de la camara y la pose del frame actual para proyectar los puntos 3D del mapa local en el frame actual. 
    Sophus::SE3f Tcw = currFrame.getPose();
    //inicializas vector de indices a revisar para cada punto del mapa local, que se llenara con los indices de los puntos del frame actual que esten cerca de la proyeccion del punto 3D del mapa local.
    vector<size_t> vIndicesToCheck(100);

    //Variables para estadisticas
    int nMatches = 0, vCos = 0, invDist = 0, noClose = 0;
    for(shared_ptr<MapPoint> pMP : vMapPoints){
        //Clear previous matches
        vIndicesToCheck.clear();

        //Check normal orientation
        assert(pMP);
        Eigen::Vector3f rayWorld = pMP->getWorldPosition() - currFrame.getPose().inverse().translation();
        float viewCos = rayWorld.normalized().dot(pMP->getNormalOrientation());
        
        /*
        2) Compute the angle between the current viewing ray v and the map point mean viewing direction n. Discard if v · n <cos(60◦).
        */
        if(viewCos < 0.5){
            vCos++;
            continue;
        }

        //Check distance is in the scale invariance region of the MapPoint
        float dist = rayWorld.norm();
        float maxDistance = pMP->getMaxDistanceInvariance();
        float minDistance = pMP->getMinDistanceInvariance();

        /*
        3) Compute the distance dfrom map point to camera center. Discard if it is out of the scale invariance region of the map point d/∈[dmin,dmax].*/

        if(dist < minDistance || dist > maxDistance){
            invDist++;
            continue;
        }

        //Predict scale
        int predictedOctave = ceil(log(maxDistance/dist)/log(currFrame.getScaleFactor(1)));
        if(predictedOctave < 0)
            predictedOctave = 0;
        else if(predictedOctave > currFrame.getNumberOfScales())
            predictedOctave = currFrame.getNumberOfScales();

        //Project MapPoint into the Frame
        Eigen::Vector3f p3Dc = Tcw*pMP->getWorldPosition();
        cv::Point2f uv = currCalibration->project(p3Dc);

        float radius = currFrame.getScaleFactor(predictedOctave);
        if(viewCos>0.998)
            radius *= 2.5;
        else
            radius *= 4.0;

        /*
         * Your matching code for Lab 3 - Task 4 goes here
         */
        //Search for points in the radius
        currFrame.getFeaturesInArea(uv.x,uv.y,radius,predictedOctave-1,predictedOctave+1,vIndicesToCheck);

        //obtenemos el descritor del mapPoint
        cv::Mat desc = pMP->getDescriptor();
        //Match with the one with the smallest Hamming distance

        int bestDist = 255, secondBestDist = 255;
        size_t bestIdx;
        for (auto idx : vIndicesToCheck){
            if(currFrame.getMapPoint(idx)){
                continue;
            }
            //Es como decir: "de todos los descriptores del frame, dame el que corresponde al candidato número idx".
            int dist = HammingDistance(desc.row(0),currFrame.getDescriptors().row(idx));

            if(dist < bestDist){
                secondBestDist = bestDist;
                bestDist = dist;
                bestIdx = idx;
            }
            else if(dist < secondBestDist){
                secondBestDist = dist;
            }
        }
        // Agregamos esto como para descartar emparejamientos ambiguos cuando se parecen demasido
        if(bestDist <= th && (float)bestDist < (float(secondBestDist)*0.9)){
            currFrame.setMapPoint(bestIdx,pMP);
            nMatches++;
        }
        else{
            noClose++;
        }
    }
    return nMatches;
    
}

int searchForTriangulation(KeyFrame* kf1, KeyFrame* kf2, int th, float fEpipolarTh, Eigen::Matrix<float,3,3>& E, std::vector<int>& vMatches){
    //Clear matches
    fill(vMatches.begin(),vMatches.end(),-1);

    //Retrieve KeyFrame descriptors
    cv::Mat& desc1 = kf1->getDescriptors();
    cv::Mat& desc2 = kf2->getDescriptors();

    //Get MaPoints
    vector<shared_ptr<MapPoint>>& vMapPoints1 = kf1->getMapPoints();
    vector<shared_ptr<MapPoint>>& vMapPoints2 = kf2->getMapPoints();

    shared_ptr<CameraModel> calibration = kf1->getCalibration();

    vector<int> vMatchedDistance(vMapPoints2.size(),INT_MAX);
    vector<int> vnMatches21(vMapPoints2.size(),-1);

    vector<bool> vbMatched2(vMapPoints2.size(),false);

    int nMatches = 0;
    for(size_t i = 0; i < vMapPoints1.size(); i++){
        //Check that there is no MapPoint already triangulated
        if(vMapPoints1[i]){
            continue;
        }

        //Unrpoject KeyPoint
        Eigen::Vector3f ray1 = (E*calibration->unproject(kf1->getKeyPoint(i).pt).transpose()).normalized();

        //Search a match in the other KeyFrame
        int bestDist = 255, secondBestDist = 255;
        size_t bestIdx;
        for(size_t j = 0; j < vMapPoints2.size(); j++){
            if(vMapPoints2[j] || vbMatched2[j])
                continue;

            int dist = HammingDistance(desc1.row(i),desc2.row(j));

            if(dist > 50 || dist > bestDist)
                continue;

            if(vMatchedDistance[j] <= dist)
                continue;

            //Unproject KeyPoint
            Eigen::Vector3f ray2 = calibration->unproject(kf2->getKeyPoint(j).pt).normalized();

            //Check epipolar constrain
            float err = fabs(M_PI/2 - acos(ray2.dot(ray1)));
            if(err < fEpipolarTh){
                bestDist = dist;
                bestIdx = j;
            }
        }

        if(bestDist < th){
            if(vMapPoints2[bestIdx])
                continue;

            if(vnMatches21[bestIdx]>=0){
                vMatches[vnMatches21[bestIdx]]=-1;
                nMatches--;
            }

            vMatches[i] = bestIdx;
            vnMatches21[bestIdx]= i;
            vbMatched2[bestIdx] = true;
            vMatchedDistance[bestIdx]=bestDist;
            nMatches++;
        }
    }

    return nMatches;
}


//Task 3 
/*
Cuando triangulamos, hay matches espurios genernado puntos duplicados, dos mappoints 3D distintos que representan el mismo punto ficiso en el mundo
Hace que el mapa se vuelva mas grande y menos preciso, ya que cada punto 3D tiene una unica observacion, lo que hace que su posicion sea muy imprecisa.
Para solucionar esto, se puede usar la funcion fuse, que recibe un KeyFrame. 

*/
int fuse(std::shared_ptr<KeyFrame> pKF, int th, std::vector<std::shared_ptr<MapPoint>>& vMapPoints, Map* pMap){
    Sophus::SE3f Tcw = pKF->getPose();
    shared_ptr<CameraModel> calibration = pKF->getCalibration();

    vector<size_t> vIndicesToCheck(100);

    vector<shared_ptr<MapPoint>>& vKFMps = pKF->getMapPoints();

    cv::Mat descMat = pKF->getDescriptors();
    int nFused = 0;

    for(size_t i = 0; i < vMapPoints.size(); i++){
        //Clear previous matches
        vIndicesToCheck.clear();

        shared_ptr<MapPoint> pMP = vMapPoints[i];

        if(!pMP)
            continue;

        if(pMap->getNumberOfObservations(pMP->getId()) == 0)
            continue;

        if(pMap->isMapPointInKeyFrame(pMP->getId(),pKF->getId()) != -1){
            continue;
        }

        /*
         * Your code for Lab 4 - Task 3 here!
         */
        //1. Proyectar el MapPoint en el KeyFrame
        Eigen::Vector3f p3Dc = Tcw*pMP->getWorldPosition(); //PROJECTAR EL PUNTO 3D EN EL KEYFRAME
        cv::Point2f uv = calibration->project(p3Dc);
        //2. Buscar puntos cercanos a la proyección del MapPoint en el KeyFrame
        if(p3Dc(2) < 0){
            continue;
        }   
        //2.Predecir la octava del punto a partir de su distancia a la cámara
        float distancia = p3Dc.norm();
        float maxDistance = pMP->getMaxDistanceInvariance();
        

        //Igual que searchWithProjection pero sin el chequeo de la orientacion del punto, ya que se asume que los puntos a fusionar son el mismo punto observado desde diferentes posiciones, por lo que su orientacion no deberia cambiar demasiado.
        int predictedOctave = ceil(log(maxDistance / distancia) / log(pKF->getScaleFactor(1)));
        if(predictedOctave < 0)
            predictedOctave = 0;
        else if(predictedOctave > pKF->getNumberOfScales())
            predictedOctave = pKF->getNumberOfScales();

        float radius = pKF->getScaleFactor(predictedOctave) * 4.0f;

        // Buscar candidatos en el KeyFrame
        pKF->getFeaturesInArea(uv.x, uv.y, radius, predictedOctave - 1, predictedOctave + 1, vIndicesToCheck);
        if(vIndicesToCheck.empty())
            continue;
       // 3. Comparar descriptores por Hamming
        cv::Mat desc = pMP->getDescriptor();
        int bestDist = 255;
        int secondBestDist = 255;
        size_t bestIdx = 0;
        for(auto idx : vIndicesToCheck){
            int dist = HammingDistance(desc.row(0), descMat.row(idx));
            if(dist < bestDist){
                secondBestDist = bestDist;
                bestDist = dist;
                bestIdx = idx;
            } else if(dist < secondBestDist){
                        secondBestDist = dist;
        }
        }
        // 4. Validar umbral y tratar los dos casos
        if(bestDist <= th){
            if(vKFMps[bestIdx] != nullptr && vKFMps[bestIdx]->getId() != pMP->getId()){
                if(pMap->getNumberOfObservations(vKFMps[bestIdx]->getId()) > 0 &&
                pMap->getNumberOfObservations(pMP->getId()) > 0){
                    pMap->fuseMapPoints(vKFMps[bestIdx]->getId(), pMP->getId());
                    nFused++;
                }
            }
        }
    }
    return nFused;
}