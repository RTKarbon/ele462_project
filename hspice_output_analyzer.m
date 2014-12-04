function [] = hspice_output_analyzer(N)

%addpath('./HspiceToolbox');

% Parameters
%N    = 100;
edges = 15;
Vdd  = 1.2;
Tsim = 500;

% wave = loadsig('wire_model_1.tr0');
% time = wave(1).data;
% Vin  = wave(3).data;
% Vout = wave(2*N+3).data;

% n    = length(time);
% count_flag = 0;
% counter = 0;
% dis = 0.001;

fileID = fopen('hspice.log');
log_file = fread(fileID,'*char');
fclose(fileID);

tplh_indx = findstr(log_file', 'tp_lh');
tplh_indx = tplh_indx(end-edges+1:end);
tp_lh = zeros(1,edges);  % Containing double precision data
tphl_indx = findstr(log_file', 'tp_hl');
tphl_indx = tphl_indx(end-edges+1:end);
tp_hl = zeros(1,edges);
for i=1:edges
    if i<10
        tplh(i,1:10) = log_file(tplh_indx(i)+9:tplh_indx(i)+18);
        tphl(i,1:10) = log_file(tphl_indx(i)+9:tphl_indx(i)+18);
    else
        tplh(i,1:10) = log_file(tplh_indx(i)+10:tplh_indx(i)+19);
        tphl(i,1:10) = log_file(tphl_indx(i)+10:tphl_indx(i)+19);
    end
    tp_lh(i) = str2double(tplh(i,1:10));
    tp_hl(i) = str2double(tphl(i,1:10));
end
mean_tplh = mean(tp_lh);
mean_tphl = mean(tp_hl);

T = table(N,edges,mean_tplh,mean_tphl);
writetable(T,'result_table.txt','Delimiter','\t')

% 
% disp('MATLAB analyzer finished');
% 
% figure
% subplot(2,1,1);
% hold on
% plot(time, Vin);
% plot(time, Vout, 'r');
% subplot(2,1,2);
% plot(Vin-Vout);


exit;
exit;
exit;
exit;
exit;
exit;
exit;
