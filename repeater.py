#!/usr/bin/python

import csv
import os, re
import numpy as np
import math
import copy

GAMMA = 1
R_IN = {'90nm':4.25e3, '45nm':2.65e3, '32nm':1.7e3}
C_IN = {'90nm':2.47e-16, '45nm':9.13e-17, '32nm':5.20e-17}
TECHNOLOGY = '90nm' # TODO: update all functions based on this parameter

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
			if row_num == 0:
				row_num += 1
				continue
			s = Stage(float(row[0]), float(row[1]), float(row[2]))
			stage_list.append(s)
	
	return stage_list

# produce two outputs: 
# - buffer placing based on an ideal case
# - buffer placing based on the delay of the part of the equal to topt

def genSpiceModel(fname_sp, wire_line):
	file_sp = open(fname_sp, 'w')

	measure_num = 5
	file_sp.write('* SPICE model for a wire with repeaters\n')
	file_sp.write('.param vdd=1.2V\n')
	file_sp.write('vdd0 vdd 0 vdd\n')
	file_sp.write('VSW 1 0 PULSE (0V vdd 5ns 0.1ns 0.1ns 5ns 10ns)\n')

	last_node, wire_string = wire_line.genWireLine()
	file_sp.write(wire_string)

	file_sp.write('\n\n')
	file_sp.write(".include '/u/alavrov/ele462/project/%s.m'\n\n" % TECHNOLOGY)

	for i in range(measure_num):
		cnt = i # TODO: why +2 ?
		edge_num = cnt + 2
		file_sp.write(".meas tran tp_hl%d TRIG v(1) VAL='vdd/2' FALL=%d TARG v(%d) VAL='vdd/2' FALL=%d\n" %\
					 (cnt, edge_num, last_node, edge_num))
		file_sp.write(".meas tran tp_lh%d TRIG v(1) VAL='vdd/2' RISE=%d TARG v(%d) VAL='vdd/2' RISE=%d\n" %\
					 (cnt, edge_num, last_node, edge_num))

	# file_sp.write(".options nomod post\n")
	file_sp.write(".tran 10fs 200ns\n")
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

def getInvSize(r_pul, c_pul, techn):
	return int((R_IN[techn]*c_pul/(r_pul*C_IN[techn]))**(0.5))

def getCritDelay(gamma, techn):
	tp1 = 0.69*R_IN[techn]*C_IN[techn]*(1+gamma)
	tp_crit = 2*(1 + (0.69/(0.38*(1+gamma)))**(0.5))*tp1
	return tp_crit

def getWireDelay(wire_line):
	genSpiceModel('tmp_wire.sp', wire_line)
	os.system('hspice tmp_wire.sp > tmp_wire.log 2> time.log')
	return getTplh('tmp_wire.log')

def getOneStageDelay(r, l, c):
	stage = Stage(r,l,c)
	wire = WireLine()
	wire.appendStage(stage)
	return getWireDelay(wire)


def getNumStages(wire_line, crit_delay, one_stage_delay): # rename
	""" Returns number of first stages in wire_line in order to meet crit_delay """
	stages = wire_line.getWireStages()

	num_st_est = int((2*crit_delay/one_stage_delay)**(0.5))
	if num_st_est == 0:
		raise "Delay of one stage is greater than the critical one"
		exit(2)

	tmp_wire = WireLine()
	tmp_wire.appendStage(stages[0:num_st_est])
	tmp_delay = getWireDelay(tmp_wire)
	print "Estimated number of stages: %d" % num_st_est
	print "Delay of these number of stages: %e" % tmp_delay

	num_stages = num_st_est
	if tmp_delay < crit_delay:
		while tmp_delay < crit_delay:
			print "Current stage number: %d; delay: %e" % (num_stages, tmp_delay)
			tmp_wire.appendStage(stages[num_stages])
			num_stages += 1
			tmp_delay = getWireDelay(tmp_wire)
	elif tmp_delay > crit_delay:
		while tmp_delay > crit_delay:
			print "Current stage number: %d; delay: %e" % (num_stages, tmp_delay)
			tmp_wire.removeStage(1)
			num_stages -= 1
			tmp_delay = getWireDelay(tmp_wire)
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

def postInsertInverters(init_wire, inv_size, techn, crit_delay):
	stages = init_wire.getWireStages()
	num_points = 100
	step = int(len(stages)/num_points)
	if step == 0:
		step = 1
	res_wire = WireLine()
	l_min = int(techn[:2]) # TODO: method
	w = l_min * inv_size

	num = getNumStages(init_wire, crit_delay, step)
	while num != None:
		for i in range(num):
			res_wire.appendStage(stages[i])
		inv = Inverter(l_min, 2*w, l_min, w)	
		res_wire.appendBuffer(inv)

		stages = stages[num:]
		print "Remained num of stages %d" % len(stages)
		tmp_wire = WireLine()
		for s in stages:
			tmp_wire.appendStage(s)
		num = getNumStages(tmp_wire, crit_delay, step)
	for s in stages:
		tmp_wire.appendStage(s)

	if res_wire.inv_cnt % 2 == 1:
		inv = Inverter(l_min, 2*w, l_min, w)
		res_wire.appendBuffer(inv)

	return res_wire




def main():
	fname_csv = 'Data/data_90_M1_Var00pc.csv'
	fname_sp = 'repeaters.sp'
	fname_log = 'hspice.log'	

	print "Reading Input Data"
	stage_list = readCsvData(fname_csv)
	wire_line = WireLine()
	wire_line.appendStage(stage_list)
	r_pul = 1.306666667 # read from csv
	l_pul = 0.0000000000003805
	c_pul = 1.0077968456205E-16
	wire_length = 20000
	technology = '90nm'
	stage_len = float(wire_length)/len(stage_list)
	r_stage = stage_len * r_pul
	l_stage = stage_len * l_pul
	c_stage = stage_len * c_pul
	
	# no_rep_delay = getWireDelay(wire_line)
	# print "Delay without repeaters: %e" % no_rep_delay

	opt_inv_size = getInvSize(r_pul, c_pul, technology)
	print "Optimal inverter size: %d" % opt_inv_size

	crit_delay = getCritDelay(GAMMA, '90nm')
	print "Critical delay: %e" % crit_delay

	one_stage_delay = getOneStageDelay(r_stage, l_stage, c_stage)
	opt_num_ideal_stages = getNumStages(wire_line, crit_delay, one_stage_delay)
	print "Number of wire stages between repeaters: %d" % opt_num_ideal_stages

	# new_wire = insertInverters(wire_line, opt_num_ideal_stages, opt_inv_size, TECHNOLOGY)
	# new_delay = getWireDelay(new_wire)
	# print "Delay with repeaters: %e" % new_delay

	# postInsertInverters(wire_line, opt_inv_size, TECHNOLOGY, crit_delay)

if __name__ == '__main__':
	main()