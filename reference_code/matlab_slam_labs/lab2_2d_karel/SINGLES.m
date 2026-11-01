% function H = SINGLES (prediction, observations, compatibility)
% %-------------------------------------------------------
% % University of Zaragoza
% % Authors:  J. Neira, J. Tardos
% %-------------------------------------------------------
% %-------------------------------------------------------
% global chi2;
% global configuration;
% 
% H = zeros(1, observations.m);
% 
% % You have observations.m observations, and prediction.n
% % predicted features.
% %
% % For every observation i, check whether it has only one neighbour,
% % say feature j, and whether that feature j  has only that one neighbour
% % observation i.  If so, H(i) = j.
% %
% % You will need to check the compatib2ility.ic matrix
% % for this:
% %
% % compatibility.ic(i,j) = 1 if observation i is a neighbour of
% % feature j.
% 
% configuration.name = 'SINGLES';


function H = SINGLES (prediction, observations, compatibility)
%-------------------------------------------------------
% University of Zaragoza
% Authors:  J. Neira, J. Tardos
%-------------------------------------------------------
global chi2;
global configuration;

H = zeros(1, observations.m);

configuration.name = 'SINGLES';

for i = 1:observations.m
    % Find all features compatible with observation i
    compatible_features = find(compatibility.ic(i,:) == 1);
    
    if length(compatible_features) == 1
        j = compatible_features(1);
        % Find all observations compatible with feature j
        compatible_obs = find(compatibility.ic(:,j) == 1);
        
        if length(compatible_obs) == 1
            % Mutually exclusive pair - safe to assign
            H(i) = j;
        end
    end
end