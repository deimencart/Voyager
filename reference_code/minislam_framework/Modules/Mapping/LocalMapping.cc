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

#include "Mapping/LocalMapping.h"
#include "Optimization/g2oBundleAdjustment.h"
#include "Matching/DescriptorMatching.h"
#include "Utils/Geometry.h"
#include <iostream>

using namespace std;

LocalMapping::LocalMapping() {

}

LocalMapping::LocalMapping(Settings& settings, std::shared_ptr<Map> pMap) {
    settings_ = settings;
    pMap_ = pMap;
}

void LocalMapping::doMapping(std::shared_ptr<KeyFrame> &pCurrKeyFrame) {
    //Keep input keyframe
    currKeyFrame_ = pCurrKeyFrame;

    if(!currKeyFrame_)
        return;

    //Remove redundant MapPoints
    mapPointCulling();

    //Triangulate new MapPoints
    triangulateNewMapPoints();

    checkDuplicatedMapPoints();

    //Run a local Bundle Adjustment
    localBundleAdjustment(pMap_.get(),currKeyFrame_->getId());
}

void LocalMapping::mapPointCulling() {
    /*
     * Your code for Lab 4 - Task 4 here!
     *
     * Strategy: remove MapPoints with 0 observations (orphaned after BA outlier rejection)
     * and those with only 1 observation that are unlikely to be matched again.
     * 
     * 
     * ¿Por qué nObs < 3?
El paper dice explícitamente: "it can only be removed if at any time it is observed f
bservaciones el BA tiene muy pocas restricciones para estimar bien la posición 3D del punto — es mejor eliminarlo.
*/
     std::cout << "Se esta ejecutanco el culling" << std::endl;

    // Proteger puntos si hay pocos KFs — aún no han tenido tiempo de acumular observaciones
    //KeyFrame Guardian: protege los puntos de ser eliminados hasta que haya suficientes KFs en el mapa para que tengan varias observaciones y así poder evaluar su calidad de manera más confiable.
    // Protect points if there are few KFs — they haven't had time to accumulate observations
    //KeyFrame Guardian: protects points from being removed until there are enough KFs in the map for them to have multiple observations and thus be evaluated more reliably.
    if(pMap_->getKeyFrames().size() < 5){
        std::cout << "Culling: removed 0 (not enough KFs yet)" << std::endl;
        return;
    }

    auto& vMapPoints = pMap_->getMapPoints();
    vector<ID> toRemove;

    for(auto& pair : vMapPoints){
        ID mpId = pair.first;
        int nObs = pMap_->getNumberOfObservations(mpId);

        // Criterio 1 — sin observaciones - eliminar siempre
        if(nObs == 0){
            toRemove.push_back(mpId);
            continue;
        }

        // Criterio 2 — paper ORB-SLAM: menos de 3 KFs observando is less confident 
        // Criterion 2 — ORB-SLAM paper: less than 3 KFs observing is less confident
        if(nObs < 3){
            toRemove.push_back(mpId);
            continue;
        }
    }

    for(ID id : toRemove){
        pMap_->removeMapPoint(id);
    }

    std::cout << "Culling: removed " << toRemove.size() << std::endl;
}
void LocalMapping::triangulateNewMapPoints() {
    //Get a list of the best covisible KeyFrames with the current one
    //Keyframes vecinos que ven la misma zona del mapa
    vector<pair<ID,int>> vKeyFrameCovisible = pMap_->getCovisibleKeyFrames(currKeyFrame_->getId());

    vector<int> vMatches(currKeyFrame_->getMapPoints().size());

    //Get data from the current KeyFrame
    shared_ptr<CameraModel> calibration1 = currKeyFrame_->getCalibration();
    Sophus::SE3f T1w = currKeyFrame_->getPose();

    int nTriangulated = 0;

    for(pair<ID,int> pairKeyFrame_Obs : vKeyFrameCovisible){
        int commonObservations = pairKeyFrame_Obs.second;
        if(commonObservations < 20)
            continue;

        shared_ptr<KeyFrame> pKF = pMap_->getKeyFrame(pairKeyFrame_Obs.first);
        if(pKF->getId() == currKeyFrame_->getId())
            continue;

        //Check that baseline between KeyFrames is not too short
        Eigen::Vector3f vBaseLine = currKeyFrame_->getPose().inverse().translation() - pKF->getPose().inverse().translation();
        float medianDepth = pKF->computeSceneMedianDepth();
        float ratioBaseLineDepth = vBaseLine.norm() / medianDepth;

        if(ratioBaseLineDepth < 0.01){
            continue;
        }

        Sophus::SE3f T2w = pKF->getPose();

        Sophus::SE3f T21 = T2w*T1w.inverse();
        Eigen::Matrix<float,3,3> E = computeEssentialMatrixFromPose(T21);

        //Match features between the current and the covisible KeyFrame
        //TODO: this can be further improved using the orb vocabulary
        int nMatches = searchForTriangulation(currKeyFrame_.get(),pKF.get(),settings_.getMatchingForTriangulationTh(),
                settings_.getEpipolarTh(),E,vMatches);

                //Esto es para debuguear, para ver cuántos matches tenemos con cada covisible y cuántas observaciones comunes hay.
                //This is for debugging, to see how many matches we have with each covisible and how many common observations there are.
        //std::cout << "KF " << pKF->getId() << " commonObs=" << commonObservations << " matches=" << nMatches << std::endl;
        vector<cv::KeyPoint> vTriangulated1, vTriangulated2;
        vector<int> vMatches_;
        //Try to triangulate a new MapPoint with each match
        for(size_t i = 0; i < vMatches.size(); i++){
            if(vMatches[i] != -1){

                if (currKeyFrame_->getMapPoints()[i] != nullptr)
                    continue;
                if (pKF->getMapPoints()[vMatches[i]] != nullptr)
                    continue;

                /*
                 * Your code for Lab 4 - Task 2 here!
                 * Note that the last KeyFrame inserted is stored at this->currKeyFrame_
                 */
                //Extract and unproyect 
                /*
                Tenemos un match entre el punto i del KeyFrame actual y el punto vMatches[i] del KeyFrame covisible. Con esta información, podemos triangular un nuevo MapPoint. 
                */
               //kEPOINT i DEK KEYFRAME ACTUAL
               //Keypoint i of the current KeyFrame
                cv::KeyPoint kp1 = currKeyFrame_->getKeyPoint(i);
                //el keypoint número vMatches[i] del KF vecino
                //the keypoint number vMatches[i] of the neighboring KF
                cv::KeyPoint kp2 = pKF->getKeyPoint(vMatches[i]);
                
                //espacio vecino calibracio
                //neighboring KF calibration
                shared_ptr<CameraModel> calibration2 = pKF->getCalibration();
                //Unproject KeyPoints
                // 1. Desproyectar a rayos normalizados (en el marco de la cámara)
                // 1. Unproject to normalized rays (in the camera frame)
                Eigen::Vector3f ray1_c = calibration1->unproject(kp1.pt).normalized();
                Eigen::Vector3f ray2_c = calibration2->unproject(kp2.pt).normalized();
                // 2. Transformar al marco del mundo usando la rotación inversa de la cámara
                // 2. Transform to the world frame using the inverse rotation of the camera
                Eigen::Vector3f ray1 = (T1w.rotationMatrix().inverse() * ray1_c).normalized();
                Eigen::Vector3f ray2 = (T2w.rotationMatrix().inverse() * ray2_c).normalized();
                /*¿Por qué normalizar? cosRayParallax calcula el coseno del ángulo entre los dos rayos usando el producto escalar. 
                El producto escalar solo da el coseno directamente si los vectores son unitarios. 
                Sin normalizar, el resultado sería incorrecto.*/
                //Why normalize? cosRayParallax calculates the cosine of the angle between the two rays using the dot product.
                //The dot product only gives the cosine directly if the vectors are unit vectors.

                //check parallax
                //Esto esta mal creo que ya estan en coordenadas del mundo, no hace falta transformar
                float cosParallax = ray1.dot(ray2);
                //este vlaor viene del YAML, es el coseno del ángulo mínimo de paralaje que queremos para considerar que la triangulación es buena.
                //This value comes from the YAML, it's the cosine of the minimum parallax angle we want to consider the triangulation good.
                if(cosParallax > settings_.getMinCos())
                    continue;
                //Triangulate
                Eigen::Vector3f p3D;
                triangulate(ray1_c,ray2_c,T1w,T2w, p3D);
                //Check positive depth and reprojection error
                /*
                Ejemplo tangible: apuntas con el dedo hacia adelante pero la intersección de los rayos cae detrás de tu cabeza — geométricamente imposible en la realidad.
                ¿Cómo se verifica?
                Transformas el punto del sistema mundo al sistema cámara y miras si la coordenada Z es positiva.
                */
                Eigen::Vector3f p3D1 = T1w*p3D;
                if(p3D1(2) < 0){
                    //std::cout << "REJECTED: negative depth cam1" << std::endl;
                    continue;}
                Eigen::Vector3f p3D2 = T2w*p3D;
                if(p3D2(2) < 0){
                    //std::cout << "REJECTED: negative depth cam2" << std::endl;
                    continue;}
                //Error de reproyección
                cv::Point2f proj1 = calibration1->project(p3D1);
                float err1 = squaredReprojectionError(proj1, kp1.pt);
                float thresh1 = 5.991f * currKeyFrame_->getSigma2(kp1.octave);
                if (err1 > 5.991f * currKeyFrame_->getSigma2(kp1.octave)){
                    std::cout << "REJECTED reproj1: err=" << err1 << " thresh=" << thresh1 << std::endl;
                    continue;
                }

                cv::Point2f proj2 = calibration2->project(p3D2);
                float err2 = squaredReprojectionError(proj2, kp2.pt);
                float thresh2 = 5.991f * pKF->getSigma2(kp2.octave);
                if (err2 > thresh2){
                    std::cout << "REJECTED reproj2: err=" << err2 << " thresh=" << thresh2 << std::endl;
                    continue;
                }

                //If all good, insert the new MapPoint in the map and add the corresponding observations
                /*
                ¿Qué operaciones necesitamos?
                Tres cosas en orden:
                1 — Crear el MapPoint con la posición 3D calculada
                2 — Insertarlo en el mapa para que el resto del sistema lo conozca
                3 — Añadir las dos observaciones — el KF actual lo ve en el feature i, el KF vecino lo ve en el feature vMatches[i]
                
                What operations do we need?
                Three things in order:  
                1 — Create the MapPoint with the calculated 3D position
                2 — Insert it into the map so the rest of the system knows it
                3 — Add the two observations — the current KF sees it in feature i, the neighboring KF sees it in feature vMatches[i]
                */
                shared_ptr<MapPoint> pNewMP = make_shared<MapPoint>(p3D);
                pMap_->insertMapPoint(pNewMP);
                pMap_->addObservation(currKeyFrame_->getId(), pNewMP->getId(), i);
                // AÑADIR: asignar el MapPoint al vector del KF vecino
                pMap_->addObservation(pKF->getId(), pNewMP->getId(), vMatches[i]);
                currKeyFrame_->setMapPoint(i, pNewMP);
                pKF->setMapPoint(vMatches[i], pNewMP);

                nTriangulated++;
                

                
            }
        }
    }
    std::cout << "Triangulated: " <<nTriangulated << std::endl;
}

void LocalMapping::checkDuplicatedMapPoints() {
    ///*
    vector<pair<ID,int>> vKFcovisible = pMap_->getCovisibleKeyFrames(currKeyFrame_->getId());
    vector<shared_ptr<MapPoint>> vCurrMapPoints = currKeyFrame_->getMapPoints();

    for(int i = 0; i < vKFcovisible.size(); i++){
        if(vKFcovisible[i].first == currKeyFrame_->getId())
            continue;
        int nFused = fuse(pMap_->getKeyFrame(vKFcovisible[i].first),settings_.getMatchingFuseTh(),vCurrMapPoints,pMap_.get());
        pMap_->checkKeyFrame(vKFcovisible[i].first);
        pMap_->checkKeyFrame(currKeyFrame_->getId());

        return; 
    //*/
    }
}