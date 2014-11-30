% Parameters
N    = 100;
Vdd  = 1.2;
Tsim = 500;

wave = loadsig('wire_model_1.tr0');
time = wave(1).data;
Vin  = wave(3).data;
Vout = wave(2*N+3).data;

n    = length(time);
count_flag = 0;
counter = 0;
dis = 0.001;
tplh = zeros(1,n);
for i=1:n
    if (abs(Vin(i)-Vdd/2)<dis)&&(count_flag==0)
        count_flag=1;
        t1 = time(i);
    end
    if (abs(Vout(i)-Vdd/2)<dis)&&(count_flag==1)
        count_flag=0;
        counter = counter + 1;
        t2 = time(i);
        tplh(counter) = t2 - t1;
    end
    if (count_flag==1)
        counter = counter + 1;
    end
end

% figure
% plot(tplh);

figure
hold on
plot(time, Vin);
plot(time, Vout, 'r');