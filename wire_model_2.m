% Wire Model
% Mohammad Shahrad
%function [elmore_delay] = wire_model_2(N)
% N                     % Number of chain elements 
N = 2000;
Len =   20000;          % Length of wire in micro-meters
edges = 15;
freq = 1e8;

% Technology Variables
tech = 90;          % 90/45/32
metal_layer = 1;

meduim = 2;             % 1->Al 2->Cu   
permeability = [1.256665e-6,1.256629e-6];   % u
conductivity = [3.5e7,5.96e7];              % sigma
ro = [2.82e-8,1.68e-8];
e_0 = 8.854187e-12;

switch tech
    case 90         % 90nm (Intel)
        % total 7 metal_layers
        % Because of the Carbon-doped Oxide (CDO) numbers are complicated
        e_r = 3.1 + metal_layer*0.043;      % Relative permittivity
        e = e_r*e_0;                        % Permittivity
        
        metal_thick  = [.15,.256,.256,.32,.384,.576,.972];
        aspect_ratio = [1.4,1.6,1.6,1.6,1.6,1.6,1.8];
        metal_wid = metal_thick./aspect_ratio;
        Rs_db = [.140,.075,0.075,0.065,0.05,0.03,0.02];
        Cll_db =[104,78,78,79,82,83,114];   % Line-to-line capacitance as a function of metal layer
        Cll_db = 1e-18*Cll_db;
        
        Wid =   metal_wid(metal_layer);     % Width in micro-meters
        Hei =   metal_thick(metal_layer);   % Height
        Rs  =   Rs_db(metal_layer);         % Resistance per micro-meters sqaure (7ohm)
        %Cpps=   30e-18;         % Parallel plate capacitance per micro-meters square
        %Cfl =   40e-18;         % Fringing capacitance per micro-meter
        if metal_layer==1
            h = metal_thick(1);    % Distance from substrate
        else
            h = metal_thick(1)+sum(metal_thick(1:metal_layer-1));    % Distance from substrate
        end
        Cw_o = e*( 1.15*(Wid/h) + 2.8*(Hei/h).^(0.222))*1e-6; % Total Cap per micro-meter
        Ll  =   0.38e-12+metal_layer*0.5e-15;   % Self Inductance per micro-meter
    case 45         % 45nm (Intel)
        % total 9 metal_layers
        e_r = 2.5 + metal_layer*0.0333;     % Relative permittivity
        e = e_r*e_0;                        % Permittivity
        
        metal_thick  = [.144,.144,.144,.216,.252,.324,.504,.720,7];
        aspect_ratio = [1.8,1.8,1.8,1.8,1.8,1.8,1.8,1.8,0.4];
        metal_wid = metal_thick./aspect_ratio;
        
        Wid =   metal_wid(metal_layer);       % Width in micro-meters
        Hei =   metal_thick(metal_layer);     % Height
        Rs  =   2*ro(meduim)/(Hei*1e-6);      % Resistance per micro-meters sqaure (7ohm)
        %Cpps=   30e-18;         % Parallel plate capacitance per micro-meters square
        %Cfl =   40e-18;         % Fringing capacitance per micro-meter
        if metal_layer==1
            h = metal_thick(1);    % Distance from substrate
        else
            h = metal_thick(1)+sum(metal_thick(1:metal_layer-1));    % Distance from substrate
        end
        Cw_o = e*( 1.15*(Wid/h) + 2.8*(Hei/h).^(0.222))*1e-6; % Total Cap per micro-meter
        Ll  =   0.381e-12+metal_layer*0.67e-15; % Self Inductance per micro-meter
    case 32         % 32nm (Intel)
        % total 9 metal_layers
        e_r = 2.1 + metal_layer*0.0333;     % Relative permittivity
        e = e_r*e_0;                        % Permittivity
        
        lambda = 0.018;
        metal_thick  = [.095,.095,.095,.151,.204,.303,.388,.504,8];
        aspect_ratio = [1.7,1.7,1.7,1.8,1.8,1.8,1.7,1.8,1.5];
        metal_wid = metal_thick./aspect_ratio;
        
        Wid =   metal_wid(metal_layer);       % Width in micro-meters
        Hei =   metal_thick(metal_layer);     % Height
        Rs  =   2*ro(meduim)/(Hei*1e-6);      % Resistance per micro-meters sqaure (7ohm)
        %Cpps=   30e-18;         % Parallel plate capacitance per micro-meters square
        %Cfl =   40e-18;         % Fringing capacitance per micro-meter
        if metal_layer==1
            h = metal_thick(1);    % Distance from substrate
        else
            h = metal_thick(1)+sum(metal_thick(1:metal_layer-1));    % Distance from substrate
        end
        Cw_o = e*( 1.15*(Wid/h) + 2.8*(Hei/h).^(0.222))*1e-6; % Total Cap per micro-meter        
        Ll  =   0.381e-12+metal_layer*0.67e-15; % Self Inductance per micro-meter
end

Rw  =   Len*Rs/Wid;     % Wire resistance
%Cppw=   Len*Wid*Cpps;  % Wire parallel plate capacitance
%Cfw =   2*Len*Cfl;     % Wire fringing capacitance
Lw  =   Len*Ll;
C_ld=   0;              % Load capacitor at wire destination

mu_w =  1;              % Average width for the Normal distribution function
sig_w =  0.25;          % Sigma for the Normal distrubution function of width
mu_h =  1;              % Average height for the Normal distribution function
sig_h =  0.25;          % Sigma for the Normal distrubution function of height

pd_w =  makedist('Normal','mu',mu_w,'sigma',sig_w);     % Normal DF for width
fac_w =  random(pd_w,[1,N]);                            % Random Chain Factors for width
pd_h =  makedist('Normal','mu',mu_h,'sigma',sig_h);     % Normal DF for width
fac_h =  random(pd_h,[1,N]);                            % Random Chain Factors for width

% Skin Effect
skin_depth = 1e6/sqrt(pi*freq*permeability(meduim)*conductivity(meduim));   % Skin Depth in micro meters

R   =   ( ( (Rw/N)*ones(1,N) ) ./ (fac_w) ) ./ (fac_h); % Resistor per chain element
% Checking for the skin effect 
% (Assumption -> Height is relatively longer than W
% and thus it's skin effect is neglected)
max_eff_wid_fact = 2*skin_depth/Wid;
for i=1:N
    if(fac_w(i)>max_eff_wid_fact)
        R(i) = R(i)*fac_w(i)/max_eff_wid_fact;
    end
end
max_eff_hei_fact = 2*skin_depth/Hei;
for i=1:N
    if(fac_h(i)>max_eff_hei_fact)
        R(i) = R(i)*fac_h(i)/max_eff_hei_fact;
    end
end
% Stage capacitance calculation
C = zeros(1,N);
for i=1:N
    C(i) = e*(Len/N)*( 1.15*(Wid*fac_w(i)/h) + 2.8*(Hei*fac_h(i)/h).^(0.222))*1e-6;
end
% Stage inductance calculation
L = (Lw/N*ones(1,N)) .* (Cw_o*(Len/N)* ones(1,N)) ./C;

% Generating the SPICE Netlist
dlmwrite('wire_model_2.sp','* Code generated by MATLAB','-append');
switch tech
    case 90
        dlmwrite('wire_model_2.sp','.param vdd=1.2V','-append');
    case 45
        dlmwrite('wire_model_2.sp','.param vdd=1.0V','-append');
    case 32
        dlmwrite('wire_model_2.sp','.param vdd=0.9V','-append');
end
% R
for j=1:N
    str = sprintf('R%d %d %d %d',j,2*j-1,2*j,R(j));
    dlmwrite('wire_model_2.sp',str,'-append');
end
% L
for j=1:N
    str = sprintf('L%d %d %d %d',j,2*j,2*j+1,L(j));
    dlmwrite('wire_model_2.sp',str,'-append');
end
% C
str = sprintf('C0 1 0 %d',C(N)/2);
dlmwrite('wire_model_2.sp',str,'-append');
for j=1:N-1
    str = sprintf('C%d %d 0 %d',j,2*j+1,C(j));
    dlmwrite('wire_model_2.sp',str,'-append');
end
% Load
str = sprintf('C%d %d 0 %d',N,2*N+1,C(N)/2+C_ld);
dlmwrite('wire_model_2.sp',str,'-append');

str = sprintf('VSW 1 0 PULSE (0V vdd 5ns 1ns 1ns 5ns 10ns)');
dlmwrite('wire_model_2.sp',str,'-append');
for j=1:edges
    str = sprintf('.meas tran tp_hl%d TRIG v(1) VAL=''vdd/2'' FALL=%d TARG v(%d) VAL=''vdd/2'' FALL=%d',j,j+1,2*N+1,j+1);
    dlmwrite('wire_model_2.sp',str,'-append');
end
for j=1:edges
    str = sprintf('.meas tran tp_lh%d TRIG v(1) VAL=''vdd/2'' RISE=%d TARG v(%d) VAL=''vdd/2'' RISE=%d',j,j+1,2*N+1,j+1);
    dlmwrite('wire_model_2.sp',str,'-append');
end

dlmwrite('wire_model_2.sp','.options nomod post','-append');
dlmwrite('wire_model_2.sp','.tran 10fs 400ns','-append');
dlmwrite('wire_model_2.sp','.END wire_model_1','-append');

% v   =   zeros(N+1,1);
% 
% syms s t
% 
% 
% i   =   zeros(N+1,1);
% i(N+1)= C_ld*s*v(N+1);
% for j=N:-1:1
%     v(j) = v(j+1) + ( C(j)*s*v(j+1) + i(j+1) ) * ( R(j) + L(j)*s );
% end

%plot(R)
%hold on
%plot(C)

simp_elmore_delay = (N+1)*Rw*(Cw_o*Len)/(2*N)
comp_elmore_delay = 0;
% Disconnectivity check
w_sign = sign(fac_w);
h_sign = sign(fac_h);
if ((sum(w_sign)~=N)||(sum(h_sign)~=N))
    comp_elmore_delay=NaN;
else
    for i=1:N
       comp_elmore_delay = comp_elmore_delay + R(i)*sum(C(i:end));
    end
end
comp_elmore_delay
