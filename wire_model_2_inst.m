function [comp_el_del,R,L,C] = wire_model_2_inst(N,tech,metal_layer,sigma_limit,sigma_step,fmin,fmax,Nf,draw_fig)
%N   =   2500;            % Number of chain elements 
edges = 15;

Len_db = 50:50:2000;
step = sigma_step;
%sigma_limit = 0.25;

freq_db = linspace(fmin,fmax,Nf);             % 100MHz

meduim = 2;             % 1->Al 2->Cu   
permeability = [1.256665e-6,1.256629e-6];   % u
conductivity = [3.5e7,5.96e7];              % sigma
ro = [2.82e-8,1.68e-8];
e_0 = 8.854187e-12;

% Technology Variables
%tech = 3;           % 1:90-nm 2:
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

Len =   20000;           % Length of wire in micro-meters
Rw  =   Len*Rs/Wid;     % Wire resistance
%Cppw=   Len*Wid*Cpps;   % Wire parallel plate capacitance
%Cfw =   2*Len*Cfl;      % Wire fringing capacitance
Lw  =   Len*Ll;
C_ld=   0;              % Load capacitor at wire destination

mu_w =  1;              % Average width for the Normal distribution function
%sig_w =  0.25;         % Sigma for the Normal distrubution function of width
mu_h =  1;              % Average height for the Normal distribution function
%sig_h =  0;            % Sigma for the Normal distrubution function of height

round_w = 0:step:sigma_limit;
round_h = 0:step:sigma_limit;

simulation = 3;     % 1->two sigmas 2->sigma & length
switch simulation
   case 1           % two sigmas
      comp_el_del = zeros(length(round_w),length(round_h));
      tot_R = zeros(length(round_w),length(round_h));
      tot_C = zeros(length(round_w),length(round_h));
   case 2           % sigma & length
      comp_el_del = zeros(length(round_w),length(Len_db));
      tot_R = zeros(length(round_w),length(Len_db));
      tot_C = zeros(length(round_w),length(Len_db));
   case 3          % frequency sweep
      comp_el_del = zeros(length(round_w),length(freq_db));
      tot_R = zeros(length(round_w),length(freq_db));
      tot_C = zeros(length(round_w),length(freq_db));
end

for freq=1:length(freq_db)
    skin_depth = 1e6/sqrt(pi*freq_db(freq)*permeability(meduim)*conductivity(meduim));   % Skin Depth in micro meters
    
    for x=1:length(round_w)
        sig_w=round_w(x);
        pd_w =  makedist('Normal','mu',mu_w,'sigma',sig_w);     % Normal DF for width
        
        y=x;
        %for y=1:length(round_h)
            fac_w =  random(pd_w,[1,N]);                            % Random Chain Factors for width
            sig_h=round_h(y);
            pd_h =  makedist('Normal','mu',mu_h,'sigma',sig_h);     % Normal DF for width
            fac_h =  random(pd_h,[1,N]);                            % Random Chain Factors for width

            % Stage resitance calculation 
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
            tot_R(x,freq) = sum(R);
            % Stage capacitance calculation
            %Cpp =  ( (Cppw/N)*ones(1,N) ) .*(fac_w);   % Parallel plate apacitor per chain element
            % Better approximation by Eq. (4.2), p.141
            %Cpp =  ( (Cppw/N)*ones(1,N) ) .*(fac_w*Wid-fac_h*Hei/2)./(Wid-Hei/2);   % Parallel plate apacitor per chain element
            %Cf  =  ( (Cfw/N)*ones(1,N) ) .* (fac_h);               % Parallel plate apacitor per chain element
            %C   =  Cpp + Cf;
            C = zeros(1,N);
            for i=1:N
                C(i) = e*(Len/N)*( 1.15*(Wid*fac_w(i)/h) + 2.8*(Hei*fac_h(i)/h).^(0.222))*1e-6;
            end
            tot_C(x,freq) = sum(C);
            % Stage inductance calculation
            
            %fac_l = (Cpp.*fac_w + Cf.*fac_h)./(Cpp+Cf);
            L   =  Lw/N*ones(1,N) .* (Cw_o*(Len/N)* ones(1,N)) ./C;

            comp_elmore_delay = 0;

            % Disconnectivity check
            w_sign = sign(fac_w);
            h_sign = sign(fac_h);
            if ((sum(w_sign)~=N)||(sum(h_sign)~=N))
                comp_elmore_delay=NaN;
                tot_R(x,freq) = NaN;
            else
                for i=1:N
                   comp_elmore_delay = comp_elmore_delay + R(i)*sum(C(i:end));
                end
            end

            %comp_el_del(x,y)=comp_elmore_delay;
            comp_el_del(x,freq)=comp_elmore_delay;
       % end
    end

end

if (draw_fig==1)
    simp_elmore_delay = (N+1)*Rw*(Cw_o*Len)/(2*N)
    %surf(round_w,round_h,comp_el_del)
    figure
    subplot(2,3,1)
    %hist(R,100)
    surf(freq_db,round_w,tot_R)
    ylabel('\sigma=\sigma_w=\sigma_h')
    xlabel('Frequency (Hz)')
    zlabel('R_t_o_t');
    subplot(2,3,2)
    surf(freq_db,round_w,comp_el_del)
    ylabel('\sigma=\sigma_w=\sigma_h')
    xlabel('Frequency (Hz)')
    zlabel('T_p');
    str = sprintf('Tech: %dnm  Metal Layer:%d  Length:%dmm',tech,metal_layer,Len/1000);
    title(str)
    subplot(2,3,3)
    contour(freq_db,round_w,comp_el_del,20)
    ylabel('\sigma=\sigma_w=\sigma_h')
    xlabel('Frequency (Hz)')
    subplot(2,3,4)
    %hist(C,100)
    freq_db_det=linspace(fmin,fmax,10*Nf);
    skin_depth_det = 1e6./sqrt(pi*freq_db_det.*permeability(meduim).*conductivity(meduim));
    semilogy(freq_db_det,2*skin_depth_det,'k');
    hold on
    grid on
    semilogy(freq_db_det,Wid*ones(1,length(freq_db_det)),'b');
    semilogy(freq_db_det,Hei*ones(1,length(freq_db_det)),'r');
    legend('2 \times Skin Depth','Nominal Width','Nominal Height');
    ylabel('(\mum)')
    xlabel('Frequency (Hz)')
    subplot(2,3,5)
    L_det = (2*pi).*freq_db_det*Lw;
    loglog(freq_db_det,L_det,'k');
    hold on
    grid on
    loglog(freq_db_det,Rw*ones(1,length(freq_db_det)),'b');
    legend('Nominal Wire wL','Nominal Wire R');
    ylabel('Impedance (ohm)')
    xlabel('Frequency (Hz)')
    subplot(2,3,6)
    surf(freq_db,round_w,tot_C)
    ylabel('\sigma=\sigma_w=\sigma_h')
    xlabel('Frequency (Hz)')
    zlabel('C_t_o_t');
end
