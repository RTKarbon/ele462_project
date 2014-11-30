#!/usr/bin/python

import os, re
from optparse import OptionParser


def setEnv():
    os.system('source /usr/licensed/synopsys/profile.20130806')

def main():
    setEnv()

    # Parsing rutime arguments
    parser = OptionParser()
    parser.add_option("-N", dest="N",
                  help="Number of chains", default=100)

    (options, args) = parser.parse_args()


    print "number of stages: %d" % int(options.N)
    print "Starting work"


    os.system('rm -f wire_model_1.sp')
    os.system('echo "exit;" >> wire_model_1.m')
    os.system('matlab -nodisplay -nosplash -nodesktop -r "wire_model_1(%d)"' % int(options.N))
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
    print 'hspice finished work'

    os.system('echo "exit;" >> hspice_output_analyzer.m')
    os.system('matlab -nodisplay -nosplash -nodesktop -r "hspice_output_analyzer(%d)"' % int(options.N))
    print 'Matlab analyzer finished'

if __name__ == '__main__':
    main()
