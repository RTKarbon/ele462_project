#!/usr/bin/python

import csv
import os, re
import numpy as np

class Section(object):
	"""Section or a wire with R-L||C"""
	def __init__(self, r, l, c):
		self.r = r
		self.l = l
		self.c = c

	def __str__(self):
		s = 'r = %e, l = %e, c = %e' % (self.r, self.l, self.c)
		return s

class Inverter(object):
	"""Inverter"""
	def __init__(self, pmos_l, pmos_w, nmos_l, nmos_w):
		self.pmos_l = pmos_l
		self.pmos_w = pmos_w
		self.nmos_l = nmos_l
		self.nmos_w = nmos_w

class WireLine(object):
	"""Ordered list of sections and inverters - parts"""
	s_flag = 0 # section flag
	i_flag = 1 # inverter flag
	def __init__(self):
		self.parts = list()

	def appendSection(self, section):
		self.parts.append((WireLine.s_flag, section))

	def appendBuffer(self, inverter):
		self.parts.append((WireLine.i_flag, inverter))

	def genWireLine(self):
		n_cnt = 1 # node name
		s_cnt = 0 # section counter
		i_cnt = 0 # inverter counter

		result_str = ''
		for part_element in self.parts:
			part_type = part_element[0]
			part = part_element[1]
			if part_type == WireLine.s_flag:
				s_cnt += 1
				result_str += "R%d %d %d %e\n" % (s_cnt, n_cnt, n_cnt+1, part.r)
				n_cnt += 1
				result_str += "L%d %d %d %e\n" % (s_cnt, n_cnt, n_cnt+1, part.l)
				n_cnt += 1
				result_str += "C%d %d 0 %e\n" % (s_cnt, n_cnt, part.c)
			elif part_type == WireLine.i_flag:
				i_cnt += 1
				result_str += "m%d %d %d vdd vdd pmos l=%s w=%s\n" %\
							  (2*i_cnt - 1, n_cnt, n_cnt+1, part.pmos_l, part.pmos_w)
				result_str += "m%d %d %d 0 0 nmos l=%s w=%s\n" %\
							  (2*i_cnt, n_cnt, n_cnt+1, part.nmos_l, part.nmos_w)
				n_cnt += 1
		return (n_cnt, result_str)

def readCsvData(fname):
	section_list = list()
	with open(fname) as csvfile:
		reader = csv.reader(csvfile, delimiter=',')
		for row in reader:
			s = Section(float(row[0]), float(row[1]), float(row[2]))
			section_list.append(s)
	
	return section_list

# produce two outputs: 
# - buffer placing based on an ideal case
# - buffer placing based on the delay of the part of the equal to topt

def genSpiceModel(fname_sp, wire_line):
	file_sp = open(fname_sp, 'w')

	measure_num = 15
	file_sp.write('* SPICE model for a wire with repeaters\n')
	file_sp.write('.param vdd=1.2V\n')

	last_node, wire_string = wire_line.genWireLine()
	file_sp.write(wire_string)

	file_sp.write('VSW 1 0 PULSE (0V vdd 5ns 0.1ns 0.1ns 5ns 10ns)\n')
	for i in range(measure_num):
		cnt = i # TODO: why +2 ?
		edge_num = cnt + 2
		file_sp.write(".meas tran tp_hl%d TRIG v(1) VAL='vdd/2' FALL=%d TARG v(%d) VAL='vdd/2' FALL=%d\n" %\
					 (cnt, edge_num, last_node, edge_num))
		file_sp.write(".meas tran tp_lh%d TRIG v(1) VAL='vdd/2' RISE=%d TARG v(%d) VAL='vdd/2' RISE=%d\n" %\
					 (cnt, edge_num, last_node, edge_num))

	file_sp.write(".options nomod post\n")
	file_sp.write(".tran 10fs 400ns\n")
	file_sp.write(".END repeaters\n")

	file_sp.close()

def getTplh(fname_log):
	f = open(fname_log, 'r')
	cont = f.read()

	tp_lh_list = list()
	all_matches = re.findall(r'tp_lh.*targ.*trig', cont)
	for match in all_matches:
		m=re.match(r'tp_lh[\d]+=[\s]+([^\s]+)[\s]+', match)
		tp_lh_list.append(float(m.group(1)))
	
	return np.mean(tp_lh_list)



def main():
	fname_csv = 'data.csv'
	fname_sp = 'repeaters.sp'
	fname_log = 'hspice.log'
	

	print "Reading Input Data"
	section_list = readCsvData(fname_csv)
	# in micrometers
	wire_length = 20000 # TODO: read from the file

	print "Construction of initial wire line without repeaters"
	wire_line = WireLine()
	for s in section_list:
		wire_line.appendSection(s)
	
	print "Generation of SPICE model"
	# genSpiceModel(fname_sp, wire_line)

	print "Running SPICE"
	# os.system('hspice %s > %s' % (fname_sp, fname_log))

	print "Calculation of the delay without repeaters"
	no_rep_delay = getTplh(fname_log)
	print no_rep_delay


if __name__ == '__main__':
	main()