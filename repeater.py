#!/usr/bin/python

import csv
import os, re
import numpy as np
import math
import copy
import time

NUM_TIME_SAMPLES = 3
GAMMA = 1
R_IN = {'90nm':4.25e3, '45nm':2.65e3, '32nm':1.7e3}
C_IN = {'90nm':2.47e-16, '45nm':9.13e-17, '32nm':5.20e-17}

class Stage(object):
	"""stage or a wire with R-L||C"""
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
	"""Ordered list of stages and inverters - parts"""
	s_flag = 0 # stage flag
	i_flag = 1 # inverter flag
	def __init__(self):
		self.parts = list()
		self.stage_cnt = 0
		self.inv_cnt = 0
		self.out_cap = None

	def appendStage(self, stages):
		if type(stages) == list:
			for i in range(len(stages)):
				self.parts.append((WireLine.s_flag, stages[i]))
				self.stage_cnt += 1
		else:
			self.parts.append((WireLine.s_flag, stages))
			self.stage_cnt += 1

	def removeStage(self, num):
		del self.parts[-num:]

	def appendBuffer(self, inverter):
		self.parts.append((WireLine.i_flag, inverter))
		self.inv_cnt += 1

	def genWireLine(self):
		n_cnt = 1 # node name
		s_cnt = 0 # stage counter
		i_cnt = 0 # inverter counter

		result_str = ''
		if self.out_cap != None:
			result_str += "Cout 1 0 %e\n" % self.out_cap
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
				result_str += "m%d %d %d vdd vdd pmos l=%sn w=%sn\n" %\
							  (2*i_cnt - 1, n_cnt+1, n_cnt, part.pmos_l, part.pmos_w)
				result_str += "m%d %d %d 0 0 nmos l=%sn w=%sn\n" %\
							  (2*i_cnt, n_cnt+1, n_cnt, part.nmos_l, part.nmos_w)
				n_cnt += 1
		return (n_cnt, result_str)

	def getWireParam(self, param_type):
		result = 0
		for part_element in self.parts:
			part_type = part_element[0]
			part = part_element[1]
			if part_type == WireLine.s_flag:
				if param_type == 'r': 
					result += part.r
				elif param_type == 'c':
					result += part.c
				elif param_type == 'l':
					result += part.l
		return result

	def getWireStages(self):
		res = list()
		for part_element in self.parts:
			part_type = part_element[0]
			part = part_element[1]
			if part_type == WireLine.s_flag:
				res.append(part)
		return copy.deepcopy(res)

def readCsvData(fname):
	stage_list = list()
	with open(fname) as csvfile:
		reader = csv.reader(csvfile, delimiter=',')
		row_num = 0
		for row in reader:
			if row_num == 1:
				length = int(row[0])
				technology = str(row[1]) + 'nm'
				metal_layer = int(row[2])
			elif row_num == 2:
				r_pul = float(row[0])
				l_pul = float(row[1])
				c_pul = float(row[2])
			elif row_num == 3:
				freq = int(row[0])
				out_cap = float(row[2])
			elif row_num != 0:
				s = Stage(float(row[0]), float(row[1]), float(row[2]))
				stage_list.append(s)

			row_num += 1
	
	return (length, technology, r_pul, l_pul, c_pul, freq, out_cap, stage_list)

# produce two outputs: 
# - buffer placing based on an ideal case
# - buffer placing based on the delay of the part of the equal to topt

def genSpiceModel(fname_sp, wire_line, technology, freq):
	file_sp = open(fname_sp, 'w')
	if technology == '90nm':
		vdd = '1.2'
	elif technology == '45nm':
		vdd = '1.0'
	elif technology == '32nm':
		vdd = '0.9'
	else:
		raise ValueError('Unknown technology')
		exit(2)

	period = 1./freq
	file_sp.write('* SPICE model for a wire with repeaters\n')
	file_sp.write('.param vdd=%sV\n' % vdd)
	file_sp.write('vdd0 vdd 0 vdd\n')
	file_sp.write('VSW 1 0 PULSE (0V vdd 5ns 0.1ns 0.1ns %es %es)\n' % (period/2, period))

	last_node, wire_string = wire_line.genWireLine()
	file_sp.write(wire_string)

	file_sp.write('\n\n')
	path = os.getcwd()
	file_sp.write(".include '%s/%s.m'\n\n" % (path, technology))

	for i in range(NUM_TIME_SAMPLES):
		cnt = i # TODO: why +2 ?
		edge_num = cnt + 2
		file_sp.write(".meas tran tp_hl%d TRIG v(1) VAL='vdd/2' FALL=%d TARG v(%d) VAL='vdd/2' FALL=%d\n" %\
					 (cnt, edge_num, last_node, edge_num))
		file_sp.write(".meas tran tp_lh%d TRIG v(1) VAL='vdd/2' RISE=%d TARG v(%d) VAL='vdd/2' RISE=%d\n" %\
					 (cnt, edge_num, last_node, edge_num))

	# file_sp.write(".options nomod post\n")
	sim_time = period*(NUM_TIME_SAMPLES+2)
	file_sp.write(".tran 0.1ns %es\n" % sim_time)
	file_sp.write(".END repeaters\n")

	file_sp.close()

def getTplh(fname_log):
	f = open(fname_log, 'r')
	cont = f.read()

	tp_lh_list = list()
	all_matches = re.findall(r'tp_lh.*targ.*trig', cont)
	for match in all_matches:
		m=re.match(r'tp_lh[\d]+=[\s]+([^\s]+)[\s]+', match)
		if m != None:
			try:
				tp_lh_list.append(float(m.group(1)))
			except:
				print "*** Warning ***"
				print '    Incorrect time: %s' % m.group(1)

	if len(tp_lh_list) == 0:
		print "No results for timing have been found. Check HSPICE output!"
		# exit(2)
	if len(tp_lh_list) < NUM_TIME_SAMPLES:
		print "*** Warning ***"
		print "    Number of raise times is less then expected"
	
	return np.mean(tp_lh_list)

def getInvSize(r_pul, c_pul, techn):
	return int((R_IN[techn]*c_pul/(r_pul*C_IN[techn]))**(0.5))

def getCritDelay(gamma, techn):
	tp1 = 0.69*R_IN[techn]*C_IN[techn]*(1+gamma)
	tp_crit = 2*(1 + (0.69/(0.38*(1+gamma)))**(0.5))*tp1
	return tp_crit

def getWireDelay(wire_line, techn, freq):
	genSpiceModel('tmp_wire.sp', wire_line, techn, freq)
	#print "Running HSPICE from:",
	#print time.strftime("%H:%M:%S")
	os.system('hspice tmp_wire.sp > tmp_wire.log 2> time.log')
	return getTplh('tmp_wire.log')

def getOneStageDelay(r, l, c, techn, freq):
	stage = Stage(r,l,c)
	wire = WireLine()
	wire.appendStage(stage)
	return getWireDelay(wire, techn, freq)


def getNumStages(wire_line, crit_delay, one_stage_delay, techn, freq): # rename
	""" Returns number of first stages in wire_line in order to meet crit_delay """
	stages = wire_line.getWireStages()

	# print "crit delay: %e" % crit_delay
	# print "one stage delay: %e" % one_stage_delay
	num_st_est = int((2*crit_delay/one_stage_delay)**(0.5))
	if num_st_est == 0:
		raise ValueError("Delay of one stage is greater than the critical one")

	tmp_wire = WireLine()
	tmp_wire.appendStage(stages[0:num_st_est])
	tmp_delay = getWireDelay(tmp_wire, techn, freq)
	# print "Estimated number of stages: %d" % num_st_est
	# print "Delay of these number of stages: %e" % tmp_delay

	num_stages = num_st_est
	if tmp_delay < crit_delay:
		while tmp_delay < crit_delay:
			#print "Current stage number: %d; delay: %e" % (num_stages, tmp_delay)
			if num_stages >= len(stages):
				return len(stages)
			tmp_wire.appendStage(stages[num_stages])
			num_stages += 1
			tmp_delay = getWireDelay(tmp_wire, techn, freq)
	elif tmp_delay > crit_delay:
		while tmp_delay > crit_delay:
			#print "Current stage number: %d; delay: %e" % (num_stages, tmp_delay)
			tmp_wire.removeStage(1)
			num_stages -= 1
			tmp_delay = getWireDelay(tmp_wire, techn, freq)
		num_stages += 1

	return num_stages
			
def insertInverters(wire_line, stage_dist, inv_size, techn):
	stages = wire_line.getWireStages()

	new_wire = WireLine()
	l_min = int(techn[:2])
	w = l_min * inv_size

	cnt = 0
	for s in stages:
		new_wire.appendStage(s)
		cnt += 1
		if (cnt % stage_dist) == 0:
			inv = Inverter(l_min, 2*w, l_min, w)
			new_wire.appendBuffer(inv)

	if new_wire.inv_cnt % 2 == 1:
		inv = Inverter(l_min, 2*w, l_min, w)
		new_wire.appendBuffer(inv)

	return new_wire

def postInsertInverters(init_wire, inv_size, techn, crit_delay, ideal_one_st_del, freq):
	stages = init_wire.getWireStages()
	res_wire = WireLine()
	l_min = int(techn[:2]) # TODO: method
	w = l_min * inv_size

	num = getNumStages(init_wire, crit_delay, ideal_one_st_del, techn, freq)
	while num != len(stages):
		for i in range(num):
			res_wire.appendStage(stages[i])
		inv = Inverter(l_min, 2*w, l_min, w)	
		res_wire.appendBuffer(inv)

		stages = stages[num:]
		#print "Remained num of stages %d" % len(stages)
		tmp_wire = WireLine()
		for s in stages:
			tmp_wire.appendStage(s)
		num = getNumStages(tmp_wire, crit_delay, ideal_one_st_del, techn, freq)
	for s in stages:
		res_wire.appendStage(s)

	if res_wire.inv_cnt % 2 == 1:
		inv = Inverter(l_min, 2*w, l_min, w)
		res_wire.appendBuffer(inv)

	return res_wire

def processData(fname_csv):
	# fname_csv = 'Data/data_90_M1_Var20pc.csv'
	fname_sp = 'repeaters.sp'
	fname_log = 'hspice.log'	

	print "*************************************************"
	print "Reading Input Data: %s" % fname_csv
	(wire_length, technology, r_pul, l_pul, c_pul, freq, out_cap, stage_list) = readCsvData(fname_csv)
	wire_line = WireLine()
	wire_line.appendStage(stage_list)
	wire_line.out_cap = out_cap
	delays_of_wire = list()
	inv_for_wire = list()
	# r_pul = 1.306666667 # read from csv
	# l_pul = 0.0000000000003805
	# c_pul = 1.0077968456205E-16
	# wire_length = 20000
	stage_len = float(wire_length)/len(stage_list)
	r_stage = stage_len * r_pul
	l_stage = stage_len * l_pul
	c_stage = stage_len * c_pul
	print "Technology: %s" % technology
	print "Frequency: %e" % freq
	print

	ideal_wire = WireLine()
	for i in range(len(stage_list)):
		stage = Stage(r_stage, l_stage, c_stage)
		ideal_wire.appendStage(stage)
	ideal_wire.out_cap = out_cap

	print "#################################"
	print "   Without any modifications"
	print "#################################"
	no_rep_delay = getWireDelay(wire_line, technology, freq)
	print "Delay without repeaters: %e\n" % no_rep_delay
	delays_of_wire.append(no_rep_delay)
        inv_for_wire.append(wire_line.inv_cnt)

	opt_inv_size = getInvSize(r_pul, c_pul, technology)
	print "Optimal inverter size: %d\n" % opt_inv_size

	crit_delay = getCritDelay(GAMMA, technology)
	print "Critical delay: %e\n" % crit_delay

	one_st_ideal_delay = getOneStageDelay(r_stage, l_stage, c_stage, technology, freq)
	opt_num_ideal_stages = getNumStages(ideal_wire, crit_delay, one_st_ideal_delay, technology, freq)
	print "Number of ideal stages between repeaters: %d\n" % opt_num_ideal_stages

	print "#################################"
	print "   Default placing of inverters"
	print "#################################"
	def_rep_wire = insertInverters(wire_line, opt_num_ideal_stages, opt_inv_size, technology)
	def_rep_wire_delay = getWireDelay(def_rep_wire, technology, freq)
	print "Delay with default placing of repeaters: %e" % def_rep_wire_delay
	delays_of_wire.append(def_rep_wire_delay)
        inv_for_wire.append(def_rep_wire.inv_cnt)
	print "Number of repeaters: %d" % def_rep_wire.inv_cnt
	print

	print "#################################"
	print "   Inserting repeaters with aware of line structure"
	print "#################################"
	adv_rep_wire = postInsertInverters(wire_line, opt_inv_size, technology, crit_delay, one_st_ideal_delay, freq)
	adv_rep_wire_delay = getWireDelay(adv_rep_wire, technology, freq)
	print "Delay with advanced placing of repeaters: %e" % adv_rep_wire_delay
	delays_of_wire.append(adv_rep_wire_delay)
        inv_for_wire.append(adv_rep_wire.inv_cnt)
	print "Number of repeaters: %d" % adv_rep_wire.inv_cnt
	print

	fout_name = fname_csv[:-4] + '_result.csv'
	fout = open(fout_name, 'w')
	for i in range(len(delays_of_wire)):
		cond_comma = ',' if (i != (len(delays_of_wire)-1)) else ''
		fout.write('%e%s' % (delays_of_wire[i],cond_comma))
        fout.write('\n')
        for i in range(len(inv_for_wire)):
                cond_comma = ',' if (i != (len(inv_for_wire)-1)) else ''
                fout.write('%e%s' % (inv_for_wire[i],cond_comma))
	fout.write('\n')
	fout.write('0,%e,%e' % (opt_inv_size, opt_inv_size))
        fout.write('\n')
        fout.close()

def main():
	dir_name = 'test_model' #'model_data_N2000_2mm_width'
	dir_path = os.path.join(os.getcwd(), dir_name)
	files_in_dir = os.listdir(dir_path)
	for f in files_in_dir:
		m = re.match(r'data',f)
		if m != None:
                    m = re.search(r'result',f)
                    if m == None:
			processData(dir_name+'/'+f)

	# processData('Data/short.csv')

	# fout_name = fname_csv[:-4] + '_result.csv'
	# fout_path = 'Data/short_result.csv'
	# fout = open(fout_path, 'w')
	# delays_of_wire=[1e3,3134.2e5,12.15e3]
	# for i in range(len(delays_of_wire)):
	# 	cond_comma = ',' if (i != len(delays_of_wire)) else ''
	# 	fout.write('%e%s' % (delays_of_wire[i],cond_comma))
	# fout.close()
	

if __name__ == '__main__':
	main()
