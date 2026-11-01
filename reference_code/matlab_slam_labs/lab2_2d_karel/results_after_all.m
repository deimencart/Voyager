load('results_NN.mat'); time_nn = results.time;
load('results_SINGLES.mat'); time_singles = results.time;
load('results_JCBB.mat'); time_jcbb = results.time;

figure;
plot(time_nn, 'r', 'LineWidth', 1.5); hold on;
plot(time_singles, 'g', 'LineWidth', 1.5);
plot(time_jcbb, 'b', 'LineWidth', 1.5);
xlabel('Step');
ylabel('Time (s)');
title('Data Association Computational Cost per Step');
legend('NN', 'SINGLES', 'JCBB');
grid on;