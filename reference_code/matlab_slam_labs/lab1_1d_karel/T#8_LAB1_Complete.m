%-------------------------------------------------------------------------
% University of Zaragoza
%
% Author:  J. Neira
%-------------------------------------------------------------------------
% SLAM for Karel the robot in 1D
%-------------------------------------------------------------------------
%Team 8 Piyush Tiwari, Diego Mendez
% clear all; % variables

close all; % figures
randn('state', 1); % always use same random number sequence
rand('state', 1); % always use same random number sequence
format long

%-------------------------------------------------------------------------
% configuration parameters

global config;

% display correlation matrix and pause at every step
config.step_by_step = 0;

%number of robot motions for each local map
config.steps_per_map = 1000;

% figure counter (to always plot a new figure)
config.fig = 0;
%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
% 1D world characteristics

global world;

% In the absolute W reference, these will not change during program execution
world.true_point_locations = [0.5:1:100000]';
%world.true_point_locations = [0.5:1:100]';
%world.true_point_locations = [0.5:1:10000000]';
% In the absolute W reference, this will change as the robot moves
world.true_robot_location = 0;

%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
% robot characteristics

global robot;

%    factor_x: fraction of the motion that constitutes odometry error
%     true_uk: ground true robot motion per step

robot.factor_x = 0.1; % ten percent
robot.true_uk = 1; % each true motion is 1m
%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
% sensor characteristics

global sensor;

%     factor_z: measurement error is this fraction of the distance
%    range_min: minimum sensor range
%    range_max: maximum sensor rangea

sensor.factor_z = 0.01; % one percent
sensor.range_min = 0;
sensor.range_max = 2;
%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
% all map details

global map;

%                  R0: absolute location of base reference for map
%               hat_x: estimated robot and feature locations
%               hat_P: robot and feature covariance matrix
%                   n: number of features in map
%              true_x: true robot and feature location (with respect to R0)
%            true_ids: true label of features in map (according to world)
%  stats.true_robot_x: true robotlocation wrt R0 for the whole trajectory
% stats.error_robot_x: robotlocation error at every step of the trajectory
% stats.sigma_robot_x: robot location uncertainty at every step of the trajectory
%        stats.cost_t: computational cost (elapsed time) for each step
%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
% measurements (not global, but this is the structure)

%            z_k: measured distance to all visible features
%            R_k: covariance of z_k
%          ids_f: true ids of the ones that are already in the map
%          ids_n: true ids of the ones that new to the map
%        z_pos_f: positions in z_k of ids_f
%        z_pos_n: positions in z_k of ids_n
%        x_pos_f: positions in hat_x of ids_f
%            z_f: z_k(z_pos_f), measurements to features already in the map
%            R_f: R_k(z_pos_f), meas. cov. to features already in the map
%            z_n: z_k(z_pos_n), measurements to features new to the map
%            R_n: R_k(z_pos_n), Meas. cov. to features new to the map
%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
% BEGIN
%-------------------------------------------------------------------------

%[map] = Kalman_filter_slam (map, config.steps_per_map);

%display_map_results (map);

%-------------------------------------------------------------------------
% BEGIN
%-------------------------------------------------------------------------

% [map] = Kalman_filter_slam (map, config.steps_per_map);
% 
% display_map_results (map);
n_maps = 1;
map = [];

for i = 1:n_maps
    map_local = Kalman_filter_slam([], config.steps_per_map);
    
    if i == 1
        map = map_local;
    else
        n_A = length(map.hat_x);
        sigma_before = sqrt(map.hat_P(1,1));
        error_before = map.true_x(1) - map.hat_x(1);
        
        % Join Maps 
        [map.hat_x, map.hat_P] = join_maps(map.hat_x, map.hat_P, ...
                                            map_local.hat_x, map_local.hat_P);
        
        % Identify Duplicates 
        ids_A = map.true_ids(2:n_A);
        ids_B = map_local.true_ids(2:end);
        [~, idx_in_A, idx_in_B] = intersect(ids_A, ids_B);
        
        % Fuse Duplicates
        for k = 1:length(idx_in_A)
            pos_F1 = 1 + idx_in_A(k);
            pos_F2 = n_A + idx_in_B(k);
            
            n_states = length(map.hat_x);
            H = zeros(1, n_states);
            H(pos_F1) = 1;
            H(pos_F2) = -1;
            
            %Kalman Filter (Again)
            y = -(map.hat_x(pos_F1) - map.hat_x(pos_F2));
            S = H * map.hat_P * H';
            K = map.hat_P * H' / S;
            
            map.hat_x = map.hat_x + K * y;
            I = eye(size(map.hat_P));
            map.hat_P = (I - K*H) * map.hat_P * (I - K*H)';
        end
        
        %  Remove Duplicates
        dup_positions = n_A + idx_in_B;
        map.hat_x(dup_positions) = [];
        map.hat_P(dup_positions, :) = [];
        map.hat_P(:, dup_positions) = [];
        
        % uodating everything 
        new_feat_mask = ~ismember(map_local.true_ids(2:end), ids_A);
        map.true_ids = [map.true_ids; map_local.true_ids(1 + find(new_feat_mask))];
        map.n = length(map.hat_x) - 1;
        
        % Ground truth
        last_pos = map.true_x(1);
        map.true_x(1) = last_pos + map_local.true_x(1);
        map.true_x = [map.true_x; last_pos + map_local.true_x(1 + find(new_feat_mask))];
        
        % updating statsss
        offset_s = map.stats.true_robot_x(end);
        map.stats.true_robot_x = [map.stats.true_robot_x; offset_s + map_local.stats.true_robot_x];
        map.stats.sigma_robot_x = [map.stats.sigma_robot_x;
            sqrt(sigma_before^2 + map_local.stats.sigma_robot_x.^2)];
        map.stats.error_robot_x = [map.stats.error_robot_x;
            error_before + map_local.stats.error_robot_x];
        map.stats.cost_t = [map.stats.cost_t; map_local.stats.cost_t];
    end
end

% This was for our excel graphs
display_map_results(map);
fprintf('Total: %.4f s, Max: %.6f s, Size P: %d\n', ...
    sum(map.stats.cost_t), max(map.stats.cost_t), size(map.hat_P,1));
%-------------------------------------------------------------------------
% END
%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
% Kalman_filter_slam
%-------------------------------------------------------------------------

function[map] = Kalman_filter_slam (map, steps)

global world;

% initial ground truth of hat_x 
map.true_x = zeros(steps);
map.true_x = [0];

% initial number of features
map.n = 0;

% initial map state and covariance
map.R0 = world.true_robot_location;

map.hat_x = zeros(steps);
map.hat_x = [0];

map.hat_P = zeros(steps,steps);
map.hat_P = [0];

% feature ids, for robot = 0
map.true_ids = [0];

% useful statistics
map.stats.true_robot_x = [0];
map.stats.error_robot_x = [];
map.stats.sigma_robot_x = [];
map.stats.cost_t = [];

for k = 0:steps
    
    tstart = tic;
    
    if k > 0
        [map] = compute_motion (map);
    end
    
    % get measurements
    [measurements] = get_measurements_and_data_association(map);
    
    % seen features already in the map? KF update!
    if not(isempty(measurements.z_f))
        [map] = update_map (map, measurements);
    end
    
    % some new features?
    if not(isempty(measurements.z_n))
        [map] = add_new_features (map, measurements);
    end
    
    % record statistics
    map.stats.error_robot_x = [map.stats.error_robot_x; (map.stats.true_robot_x(end) - map.hat_x(1))];
    map.stats.sigma_robot_x = [map.stats.sigma_robot_x; sqrt(map.hat_P(1,1))];
    map.stats.cost_t = [map.stats.cost_t; toc(tstart)];
    
end
end

%-------------------------------------------------------------------------
% compute_motion
%-------------------------------------------------------------------------

function [map] = compute_motion (map)

global config;
global robot;
global world;

% move robot and update ground truth robot location
world.true_robot_location = world.true_robot_location + robot.true_uk;

% odometry error
sigma_xk = robot.factor_x * robot.true_uk;
error_k = randn(1)*sigma_xk;

% estimated motion
map.hat_x(1) = map.hat_x(1) + robot.true_uk + error_k;
map.hat_P(1,1) = map.hat_P(1,1) + sigma_xk^2;

% update ground truth for the current map
map.true_x(1) = map.true_x(1) + robot.true_uk;
map.stats.true_robot_x = [map.stats.true_robot_x; map.stats.true_robot_x(end) + robot.true_uk];

if config.step_by_step
    fprintf('Move to %d...\n',map.true_x(1));
    plot_correlation(map.hat_P);
    pause
end
end

%-------------------------------------------------------------------------
% get_measurements
%-------------------------------------------------------------------------

function [measurements] = get_measurements_and_data_association(map)

global world;
global sensor;

distances = world.true_point_locations - world.true_robot_location;
visible_ids = find((distances >= sensor.range_min) & (distances <= sensor.range_max));
visible_d = distances(visible_ids);
n_visible = length(visible_ids);

% sensor error
sigma_z = sensor.factor_z * visible_d;
error_z = randn(n_visible, 1) .* sigma_z;

measurements.z_k = visible_d + error_z;
measurements.R_k = diag(sigma_z.^2);

% data association
measurements.ids_f = intersect(map.true_ids, visible_ids);
measurements.ids_n = setdiff(visible_ids, map.true_ids);
measurements.z_pos_f = find(ismember(visible_ids, measurements.ids_f));
measurements.z_pos_n = find(ismember(visible_ids, measurements.ids_n));
measurements.x_pos_f = find(ismember(map.true_ids, visible_ids));

%features already in the map
measurements.z_f = measurements.z_k(measurements.z_pos_f);
measurements.R_f = measurements.R_k(measurements.z_pos_f,measurements.z_pos_f);

%new features
measurements.z_n = measurements.z_k(measurements.z_pos_n);
measurements.R_n = measurements.R_k(measurements.z_pos_n,measurements.z_pos_n);

end

%-------------------------------------------------------------------------
% update_map
%-------------------------------------------------------------------------

function[map] = update_map (map, measurements)

global config;

z_f = measurements.z_f; 
R_f = measurements.R_f; 
x_pos_f = measurements.x_pos_f; 

n_states = length(map.hat_x); 
m = length(z_f); 
H = zeros(m, n_states);

H(:, 1) = -1;
H(sub2ind(size(H), (1:m)', x_pos_f(:))) = 1;

% Innovation
hat_z = map.hat_x(x_pos_f) - map.hat_x(1); 
y = z_f - hat_z; 

S = H * map.hat_P * H' + R_f;
K = map.hat_P * H' / S;

% Update state
map.hat_x = map.hat_x + K * y;

map.hat_P = (eye(n_states) - K * H) * map.hat_P * (eye(n_states) - K * H)' + K * R_f * K';
% this is the formula 
%map.hat_P = (I - K*H) * map.hat_P * (I - K*H)' + K*R_f*K';

if config.step_by_step
    fprintf('Update map for last %d features...\n', length(measurements.ids_f));
    plot_correlation(map.hat_P);
    pause
end
end

%-------------------------------------------------------------------------
% add_new_features
%-------------------------------------------------------------------------

function [map] = add_new_features (map, measurements)

global config;
global world;

% DO SOMETHING HERE!
% update map.hat_x, map.hat_P, map.true_ids, map.true_x, map.n
z_n = measurements.z_n; %Distancia medida a los beepers nuevos
R_n = measurements.R_n; % cov de las mediciones de los beepers
ids_n = measurements.ids_n; %ids reales de los beepers

% new positions 
new_x = map.hat_x(1) +z_n;
map.hat_x = [map.hat_x; new_x]; 

% Logic de esto : "el beeper está donde yo creo que estoy, más la distancia que medí".
% ```
% f_nuevo = x_robot + z_medido
% ```

%Expanading the covarianze matrix 
P_robot_map =map.hat_P(:, 1);  %robot only
P_of = repmat(P_robot_map, 1, length(ids_n)); %covaruabzaed crrossed

%nueva covarianza 
n_new = length(ids_n);
%Pf = map.hat_P(1,1) * ones(n_new) + R_n;  % off-diagonal = P(1,1)
% Corrección sugerida:
Pf = map.hat_P(1,1) * ones(n_new, n_new) + R_n; % R_n ya es diagonal, está bien.
map.hat_P = [map.hat_P, P_of; 
            P_of',      Pf]; 


map.n = map.n + length(ids_n);       % Aumentar contador de features
map.true_ids = [map.true_ids; ids_n]; % Añadir los IDs a la lista oficial
map.true_x = [map.true_x; world.true_point_locations(ids_n) - map.R0];

% map.true_x: Aquí deberías añadir la posición REAL (sin error) 
% que viene en world.true_point_locations(ids_n)

if config.step_by_step
    fprintf('Add %d new features...\n',length(measurements.ids_n));
    plot_correlation(map.hat_P);
    pause
end
end


%-------------------   
% Join maps
%-------------------
function [x_join, P_joined] = join_maps(x_A, P_A, x_B, P_B)
    n_A = length(x_A);
    n_feat_A = n_A - 1;
    n_feat_B = length(x_B) - 1;
    
    % joint_stated
    x_join = [x_A(1) + x_B(1); x_A(2:end); x_A(1) + x_B(2:end)];
    
    % Jacobiano completo
    J = zeros(1 + n_feat_A + n_feat_B, n_A + length(x_B));
    J(1, 1) = 1;         
    J(1, n_A + 1) = 1;   
    
    % Features of Map A
    if n_feat_A > 0
        J(2:1+n_feat_A, 2:n_A) = eye(n_feat_A);
    end
    
    % Features of Map B
    J(2+n_feat_A:end, 1) = 1; 
    J(2+n_feat_A:end, n_A+2:end) = eye(n_feat_B);
    
    P_joined = J * blkdiag(P_A, P_B) * J';
end
%-------------------------------------------------------------------------
% display_results
%-------------------------------------------------------------------------

function  display_map_results (map)

global config;

config.fig = config.fig + 1;
figure(config.fig);
if max(sqrt(diag(map.hat_P))) > 0
   axis([0 length(map.hat_x) -2*max(sqrt(diag(map.hat_P))) 2*max(sqrt(diag(map.hat_P)))]);
else
   axis([0 length(map.hat_x) -2 2]);
end

grid on;
hold on;
plot(map.true_ids, map.true_x-map.hat_x, 'ro','Linewidth', 2);
plot(map.true_ids, 2*sqrt(diag(map.hat_P)), 'b+','Linewidth', 2);
plot(map.true_ids, -2*sqrt(diag(map.hat_P)), 'b+','Linewidth', 2);
xlabel('Feature number (robot = 0)');
ylabel('meters (m)');
title('Map estimation error + 2sigma bounds');

config.fig = config.fig + 1;
figure(config.fig);
plot_correlation(map.hat_P);
title(sprintf('Correlation matrix of size %d', size(map.hat_P,1)));

config.fig = config.fig + 1;
figure(config.fig);
grid on;
hold on;
plot(map.stats.true_robot_x, map.stats.cost_t,'r-','Linewidth',2);
xlabel('step');
ylabel('seconds');
title('Cost per step');

config.fig = config.fig + 1;
figure(config.fig);
grid on;
hold on;
plot(map.stats.true_robot_x,cumsum(map.stats.cost_t),'r-','Linewidth',2);
xlabel('step');
ylabel('seconds');
title('Cumulative cost');

config.fig = config.fig + 1;
figure(config.fig);
if max(map.stats.sigma_robot_x) > 0
    axis([0 map.stats.true_robot_x(end) -2*max(map.stats.sigma_robot_x) 2*max(map.stats.sigma_robot_x)]);
else
    axis([0 map.stats.true_robot_x(end) -2 2]);
end

grid on;
hold on;
plot(map.stats.true_robot_x, map.stats.error_robot_x,'r-','Linewidth',2);
plot(map.stats.true_robot_x, 2*map.stats.sigma_robot_x,'b-','Linewidth',2);
plot(map.stats.true_robot_x,-2*map.stats.sigma_robot_x,'b-','Linewidth',2);
xlabel('meters (m)');
ylabel('meters (m)');
title('Robot estimation error + 2sigma bounds');

end

%-------------------------------------------------------------------------
% plot_correlation
%-------------------------------------------------------------------------

function plot_correlation(P)

ncol=256 ;

% hot cold colormap
cmap=hsv2rgb([linspace(2/3, 0, ncol)' 0.9*ones(ncol,1) ones(ncol,1)]) ;
cmap(1,:)=[0 0 0] ;
colormap(cmap) ;

corr = correlation(P);
imagesc(abs(corr), [0 1]) ;  % no sign

axis image;
colorbar ;

end

%-------------------------------------------------------------------------
% correlation
%-------------------------------------------------------------------------

function Corr=correlation(Cov)

sigmas = sqrt(diag(Cov));
Corr = diag(1./sigmas)*Cov*diag(1./sigmas);

end