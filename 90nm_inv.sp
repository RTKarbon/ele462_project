* comment
*
.param vdd=1.2

vdd0 vdd 0 vdd
vin in 0 pulse(0 vdd 1p 1p 1p 6n 12n)
* transistors
m1 out in vdd vdd pmos l=90n w=90n
m2 out in 0 0 nmos l=90n w=90n
Cout out 0 20f

* Model
.include '/u/alavrov/ele462/project/90nm.m'

.options nomod post
.tran 0.01p 12n

.meas tran tp_hl TRIG v(in) VAL='vdd/2' CROSS=1 TARG v(out) VAL='vdd/2' CROSS=1
.meas tran tp_lh TRIG v(in) VAL='vdd/2' CROSS=2 TARG v(out) VAL='vdd/2' CROSS=2
.meas tran slew DERIV v(in) when v(in)='vdd/2'
.MEAS TRAN result FIND i(vin) WHEN v(in)='vdd/2' CROSS=2

.end