#!/usr/bin/python

import os, re

def setEnv():
	os.system('source /usr/licensed/synopsys/profile.20130806')

def main():
	setEnv()

        os.system('rm -f wire_model_1.sp')
	os.system('echo "exit;" >> wire_model_1.m')
	os.system('matlab -nodisplay -nosplash -nodesktop -r "wire_model_1(100)"')
	print 'Matlab finished generation of SPICE model'

        fin = open('wire_model_1.sp', 'r')
        cont = fin.read()
        fin.close()
        cont = re.sub(',', '', cont)
	fout = open('wire_model_1.sp', 'w')
        fout.write(cont)
        fout.close()
	print 'SPICE model has been processed for running with hspice'

        os.system('hspice wire_model_1.sp > hspice.log')	

if __name__ == '__main__':
	main()
