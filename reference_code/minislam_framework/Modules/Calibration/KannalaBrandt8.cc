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

#include "KannalaBrandt8.h"
#include <cmath>

#define fx vParameters_[0]
#define fy vParameters_[1]
#define cx vParameters_[2]
#define cy vParameters_[3]
#define k0 vParameters_[4]
#define k1 vParameters_[5]
#define k2 vParameters_[6]
#define k3 vParameters_[7]

void KannalaBrandt8::project(const Eigen::Vector3f& p3D, Eigen::Vector2f& p2D){
    
    float x = p3D(0);
    float y = p3D(1);
    float z = p3D(2);

    // Step 1: compute r and theta
    float r = std::sqrt(x*x + y*y);
    float theta = std::atan2(r, z);

    // Step 2: compute distorted radius d(theta)
    float theta2 = theta * theta;
    float theta3 = theta2 * theta;
    float theta5 = theta3 * theta2;
    float theta7 = theta5 * theta2;
    float theta9 = theta7 * theta2;
    float d = theta + k0*theta3 + k1*theta5 + k2*theta7 + k3*theta9;

    // Step 3: project to pixel
    float invR = (r > 1e-8f) ? 1.0f / r : 0.0f;
    p2D(0) = fx * d * (x * invR) + cx;
    p2D(1) = fy * d * (y * invR) + cy;
}

void KannalaBrandt8::unproject(const Eigen::Vector2f& p2D, Eigen::Vector3f& p3D) {
   
    // Step 1: normalize pixel
    float mx = (p2D(0) - cx) / fx;
    float my = (p2D(1) - cy) / fy;
    float rp = std::sqrt(mx*mx + my*my);

    // Step 2: invert d(theta) using Newton's method
    float theta = rp; // initial guess
    for(int i = 0; i < 10; i++){
        float theta2 = theta * theta;
        float theta3 = theta2 * theta;
        float theta5 = theta3 * theta2;
        float theta7 = theta5 * theta2;
        float theta9 = theta7 * theta2;

        float f  = theta + k0*theta3 + k1*theta5 + k2*theta7 + k3*theta9 - rp;
        float df = 1.0f + 3.0f*k0*theta2 + 5.0f*k1*theta2*theta2
                       + 7.0f*k2*theta2*theta2*theta2
                       + 9.0f*k3*theta2*theta2*theta2*theta2;
        theta -= f / df;
    }

    // Step 3: recover direction vector
    float invRp = (rp > 1e-8f) ? 1.0f / rp : 0.0f;
    p3D(0) = std::sin(theta) * mx * invRp;
    p3D(1) = std::sin(theta) * my * invRp;
    p3D(2) = std::cos(theta);
}

void KannalaBrandt8::projectJac(const Eigen::Vector3f& p3D, Eigen::Matrix<float,2,3>& Jac) {
    
    float x = p3D(0);
    float y = p3D(1);
    float z = p3D(2);

    float r2 = x*x + y*y;
    float r  = std::sqrt(r2);
    float r3 = r2 * r;
    float rz2 = r2 + z*z;

    float theta  = std::atan2(r, z);
    float theta2 = theta * theta;
    float theta3 = theta2 * theta;
    float theta5 = theta3 * theta2;
    float theta7 = theta5 * theta2;
    float theta9 = theta7 * theta2;

    float d  = theta + k0*theta3 + k1*theta5 + k2*theta7 + k3*theta9;
    float dd = 1.0f + 3.0f*k0*theta2 + 5.0f*k1*theta2*theta2
                    + 7.0f*k2*theta2*theta2*theta2
                    + 9.0f*k3*theta2*theta2*theta2*theta2;

    // partial derivatives of theta w.r.t. x, y, z
    // theta = atan2(r, z), r = sqrt(x²+y²)
    // d(theta)/dx = x*z / (r * (r²+z²))
    // d(theta)/dy = y*z / (r * (r²+z²))
    // d(theta)/dz = -r / (r²+z²)
    float dtheta_dx = (r > 1e-8f) ? x * z / (r * rz2) : 0.0f;
    float dtheta_dy = (r > 1e-8f) ? y * z / (r * rz2) : 0.0f;
    float dtheta_dz = -r / rz2;

    // partial derivatives of (x/r) w.r.t x, y, z
    // d(x/r)/dx = y²/r³,  d(x/r)/dy = -xy/r³,  d(x/r)/dz = 0
    float invR  = (r > 1e-8f) ? 1.0f / r  : 0.0f;
    float invR3 = (r > 1e-8f) ? 1.0f / r3 : 0.0f;

    float d_xr_dx = y*y * invR3;
    float d_xr_dy = -x*y * invR3;
    float d_yr_dx = -x*y * invR3;
    float d_yr_dy = x*x * invR3;

    float xr = x * invR;
    float yr = y * invR;

    // u = fx * d * (x/r) + cx  =>  du/d* = fx * (dd * d(theta)/d* * (x/r) + d * d(x/r)/d*)
    // v = fy * d * (y/r) + cy  =>  dv/d* = fy * (dd * d(theta)/d* * (y/r) + d * d(y/r)/d*)

    Jac(0,0) = fx * (dd * dtheta_dx * xr + d * d_xr_dx);
    Jac(0,1) = fx * (dd * dtheta_dy * xr + d * d_xr_dy);
    Jac(0,2) = fx *  dd * dtheta_dz * xr;

    Jac(1,0) = fy * (dd * dtheta_dx * yr + d * d_yr_dx);
    Jac(1,1) = fy * (dd * dtheta_dy * yr + d * d_yr_dy);
    Jac(1,2) = fy *  dd * dtheta_dz * yr;
}

void KannalaBrandt8::unprojectJac(const Eigen::Vector2f& p2D, Eigen::Matrix<float,3,2>& Jac) {
    throw std::runtime_error("KannalaBrandt8::unprojectJac not implemented yet");
}
