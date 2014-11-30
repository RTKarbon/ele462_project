% Wire Model
% Mohammad Shahrad
function [elmore_delay] = wire_model_1(N)
%N   =   100;            % Number of chain elements         

Len =   1000;           % Length of wire in micro-meters
Wid =   0.12;           % Width in micro-meters
Rs  =   0.065;          % Resistance per micro-meters sqaure
Cpps=   30e-18;         % Parallel plate capacitance per micro-meters square
Cfl =   40e-18;         % Fringing capacitance per micro-meter
Ll  =   1e-10;
Rw  =   Len*Rs/Wid;     % Wire resistance
Cppw=   Len*Wid*Cpps;   % Wire parallel plate capacitance
Cfw =   2*Len*Cfl;      % Wire fringing capacitance
Lw  =   Len*Ll;
C_ld=   0;              % Load capacitor at wire destination

d_r =   0.2;            % Max defect ratio
def =   d_r*rand(1,N);  % Defects
obd =   0.05;           % Out of boundray defects
dfe =   0.1;            % Defect Fringe Effect

R   =   ( (Rw/N)*ones(1,N) ) ./ (1-(1-2*obd)*def);      % Resistor per chain element
Cpp =   ( (Cppw/N)*ones(1,N) ) .* (1-(1-2*obd)*def);  % Parallel plate apacitor per chain element
Cf  =   ( (Cfw/N)*ones(1,N) ) .* (1+dfe*def);  % Parallel plate apacitor per chain element
C   =   Cpp + Cf;
L   =   Lw/N*ones(1,N);

% Generating the SPICE Netlist
dlmwrite('wire_model_1.sp','* Code generated by MATLAB','-append');
dlmwrite('wire_model_1.sp','.param vdd=1.2V','-append');
% R
for j=1:N
    str = sprintf('R%d %d %d %d',j,2*j-1,2*j,R(j));
    dlmwrite('wire_model_1.sp',str,'-append');
end
% L
for j=1:N
    str = sprintf('L%d %d %d %d',j,2*j,2*j+1,L(j));
    dlmwrite('wire_model_1.sp',str,'-append');
end
% C
str = sprintf('C0 1 0 %d',C(N)/2);
dlmwrite('wire_model_1.sp',str,'-append');
for j=1:N-1
    str = sprintf('C%d %d 0 %d',j,2*j+1,C(j));
    dlmwrite('wire_model_1.sp',str,'-append');
end
% C_load
str = sprintf('C%d %d 0 %d',N,2*N+1,C(N)/2+C_ld);
dlmwrite('wire_model_1.sp',str,'-append');

str = sprintf('VSW 1 0 PULSE (0V vdd 5ns 1ns 1ns 5ns 10ns)');
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_hl1 TRIG v(1) VAL=''vdd/2'' FALL=1 TARG v(%d) VAL=''vdd/2'' FALL=1',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_hl2 TRIG v(1) VAL=''vdd/2'' FALL=2 TARG v(%d) VAL=''vdd/2'' FALL=2',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_hl3 TRIG v(1) VAL=''vdd/2'' FALL=3 TARG v(%d) VAL=''vdd/2'' FALL=3',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_hl4 TRIG v(1) VAL=''vdd/2'' FALL=4 TARG v(%d) VAL=''vdd/2'' FALL=4',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_hl5 TRIG v(1) VAL=''vdd/2'' FALL=5 TARG v(%d) VAL=''vdd/2'' FALL=5',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_lh1 TRIG v(1) VAL=''vdd/2'' RISE=1 TARG v(%d) VAL=''vdd/2'' RISE=1',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_lh2 TRIG v(1) VAL=''vdd/2'' RISE=2 TARG v(%d) VAL=''vdd/2'' RISE=2',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_lh3 TRIG v(1) VAL=''vdd/2'' RISE=3 TARG v(%d) VAL=''vdd/2'' RISE=3',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_lh4 TRIG v(1) VAL=''vdd/2'' RISE=4 TARG v(%d) VAL=''vdd/2'' RISE=4',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
str = sprintf('.meas tran tp_lh5 TRIG v(1) VAL=''vdd/2'' RISE=5 TARG v(%d) VAL=''vdd/2'' RISE=5',2*N+1);
dlmwrite('wire_model_1.sp',str,'-append');
dlmwrite('wire_model_1.sp','.options nomod post','-append');
dlmwrite('wire_model_1.sp','.tran 1ps 500ns','-append');
dlmwrite('wire_model_1.sp','.END wire_model_1','-append');

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

elmore_delay = (N+1)*Rw*(Cppw + Cfw)/(2*N);
