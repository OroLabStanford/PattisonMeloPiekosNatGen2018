""" 
Author: Samantha Piekos
Title: MasterConnections.py
Date Created:  4/5/17
Date Modified: 1/14/19

Description:  Checks connection of TSSs to a regulatory element of interest. Checks if the regulatory element directly binds to the TSS (0°); the regulatory
element binds distally, which loops to the TSS (1°); the regulatory element loops to a second regulatory element, which then loops to the TSS (2°),
or the TSS loops to a regulatory element, which loops to a different regulatory element which loops to the regulatory element of interest (3°).
The output is a file containing info about the elements involved in these connections as well as the strength and identity of the contacts involved. 

@HiChIP_target_file	output file generated by AnchorLoops.py for the target regulatory element of interest
@HiChIP_element1_file	output file generated by AnchorLoops.py for a secondary regulatory element of interest
@HiChIP_element2_file	output file generated by AnchorLoops.py for a tertiary regulatory element of interest
@target_file	bed file of the target regulatory element of interest
@target_name	name of the target regulatory element of interest
@gene_file	bed file of genes of interest
@gene_name	name for genes of interest
@element1_file	bed file of the secondary regulatory element of interest
@element1_name	name of the secondary regulatory element of interest
@element2_file	bed file of the tertiary regulatory element of interest
@element2_name	name of the tertiary regulatory element of interest
@deg0_output_file	pathway to output file for deg0 connections (target binds directly to the TSS)
@deg1_output_file	pathway to output file for deg1 connections (target loops directly to the TSS)
@deg2_output_file	pathway to output file for deg2 connections (target loops to the TSS via the intermediate secondary or tertiary regulatory element of interest)
@deg3_output_file	pathway to output file for deg3 connections (target loops to the TSS by 2 intermeidate regulatory elements of interest)
@promoter_dist	set integer distance for the TSS (TSS = gene start =/- promoter_dist)
"""

import sys
import timeit

HiChIP_target_file = sys.argv[1] # loops targeted in the regulatory element of interest
HiChIP_element1_file = sys.argv[2]
HiChIP_element2_file = sys.argv[3]
target_file = sys.argv[4] # the element whose connection with the gene TSS is being analyzed
target_name = sys.argv[5]
gene_file = sys.argv[6]  # code writen for the gene to be the gene!
gene_name = sys.argv[7]
element1_file = sys.argv[8]  # other element that can act as a connection point between target and TSS
element1_name = sys.argv[9]
element2_file = sys.argv[10]  # other element that can act as a connection point between target and TSS
element2_name = sys.argv[11]
deg0_output_file = sys.argv[12]
deg1_output_file = sys.argv[13]
deg2_output_file = sys.argv[14]
deg3_output_file = sys.argv[15]
promoter_dist = int(sys.argv[16])

start_time = timeit.default_timer()
HiChIP_target = {}
HiChIP_element1 = {}
HiChIP_element2 = {}
target_loop_dict = {}
target_dict = {}
gene = {}
element1 = {}
element2 = {}
unpack = [(target_file, target_dict, target_name), (element1_file, element1, element1_name), (element2_file, element2, element2_name)]
unpack2 = [(HiChIP_target_file, HiChIP_target), (HiChIP_element1_file, HiChIP_element1), (HiChIP_element2_file, HiChIP_element2)]
deg1 = {}
deg2 = {}
deg3 = {}
g_e1 = {}
g_e2 = {}
target_deg1_list = set()
e1_deg1_list = set()
e2_deg1_list = set()
g_e1_e2 = {}
g_e2_e1 = {}
g_e1_e1 = {}
g_e2_e2 = {}

def write2dict(key, value, dictionary):
# writes only unique entries to a dictionary in which the value is a set to which the entry is appended
	if key in dictionary:
		if value not in dictionary[key]:
			dictionary[key].append(value)
	else:
		dictionary[key] = [value]
	return(dictionary)

def OrderChrDict(chr_dict):  # orders keys in dictionary and sorts values by second component of values
	from collections import OrderedDict

	for key, value in chr_dict.items():  # sort values for each key
		chr_dict[key] = sorted(value, key=lambda element: (element[1], element[2]))
	final_dict = OrderedDict(sorted(chr_dict.items(), key=lambda t: t[0]))  # sort keys and write sorted info to an Ordered Dict
	return(final_dict)

def CheckBin(val, Bin):  # checks if a given value falls within a bin (bin = [start, stop])
	start, stop = int(Bin[0]), int(Bin[1])
	val = int(val)
	return(val < stop and val > start)

def MiddleBin(start, stop, Bin):
	bin_start, bin_stop = int(Bin[0]), int(Bin[1])
	start, stop = int(start), int(stop)
	return(start <= bin_start and stop >= bin_stop)

def BinChecker(feature_start, feature_stop, bin_coordinates):
	feature_start, feature_stop = int(feature_start), int(feature_stop)
	bin_coordinates[0], bin_coordinates[1] = int(bin_coordinates[0]), int(bin_coordinates[1])
	bin_start, bin_stop = int(bin_coordinates[0]), int(bin_coordinates[1])

	# return HiChIP bin coordinates if start or stop of the peak coordinates falls within one of the bins
	if CheckBin(feature_start, bin_coordinates) or CheckBin(feature_stop, bin_coordinates):
		return(bin_coordinates)
	# return HiCHIP coordinates if the peak overlaps with the entirity of the loop bins
	elif MiddleBin(feature_start, feature_stop, bin_coordinates):
		return(bin_coordinates)
	else:  # return False if there is no overlap between the peak and either of the loop bins
		return(False)

def DistalConnectCheck(feature, anchor, loop):
# identifies which end of the loop the anchor is associated and checks if the feature is on the other end of the loop
	feature_start, feature_stop = int(feature[0]), int(feature[1])
	anchor_start, anchor_stop = int(anchor[0]), int(anchor[1])
	loop1 = [int(loop[1]), int(loop[2])]
	loop2 = [int(loop[4]), int(loop[5])]

	check = BinChecker(anchor_start, anchor_stop, loop1)
	if check:
		isin0 = BinChecker(feature_start, feature_stop, loop2)
		if isin0:
			return('yes')
	else:  # anchor is in bin 2 and check if feature is in bin 1
		isin1 = BinChecker(feature_start, feature_stop, loop1)
		if isin1:  # write lines of HiChIP files to dictionary if they are anchored at one end with the feature of interest
			return('yes')
	return(False)

def countUniqueGene(dictionary):
# Count the number of the unique genes in a dictionary in which the value is a list of loops (also in list form)
	UniqueGene = []
	for key, value in dictionary.items():
		for item in value:
			if item[4] not in UniqueGene:  # gene name has to be in index[4] position in the loop list
				UniqueGene.append(item[4])
	return(len(UniqueGene))


def getTSS(gene_dict, promoter_dist):  # establish coordinates for TSS based on gene coordinates
	# outputs the TSS as a given distance upstream and downstream of the gene start in a chr dictionary
	TSS = {}
	for chrom, value in gene_dict.items():
		for line in value:
			if line[5] == '+':
				line[2], line[3] = (int(line[2]) - promoter_dist), (int(line[2]) + promoter_dist)
			elif line[5] == '-':
				line[2], line[3] = (int(line[3]) - promoter_dist), (int(line[3]) + promoter_dist)
			else:
				print('Error: incorrect formatting in gene input file!')
			TSS = write2dict(chrom, line[:5], TSS)
	return(TSS)


def deg0_analysis(TSS_dict, target_dict):  # find overlap between TSSs and target coordinates; verified by bedtools intersect
	deg0 = {}
	for chrom, value0 in TSS_dict.items():
		if chrom in target_dict:
			for item0 in value0:
				for item1 in target_dict[chrom]:
					start, stop = int(item1[2]), int(item1[3])
					Bin = [int(item0[2]), int(item0[3])]
					check = BinChecker(start, stop, Bin)  # check if target is contained within the TSS
					if check:
						keep = item0[:]
						keep.extend(item1)
						deg0 = write2dict(chrom, keep, deg0)
	return(deg0)


def deg1_analysis(entry, TSS):
	HiChIP_dict, output_dict, output_list, name = entry[0], entry[1], entry[2], entry[3]
	for chrom, value in HiChIP_dict.items():
		if chrom in TSS:
			for item in value:
				loop = item[:6]
				target = [int(item[11]), int(item[12])]
				for line in TSS[chrom]:
					feature = [line[2], line[3]]
					check = DistalConnectCheck(feature, target, loop)
					if check:
						keep = line[:]
						keep.append('loop_count')
						keep.extend(item[6:14])
						output_dict = write2dict(chrom, keep, output_dict)
						output_list.add(tuple(item[9:14]))
	count = countUniqueGene(output_dict)
	print('# Number of', gene_name, 'Directly Looped to', name, '(i.e. 1°', name, ') =', count)
	return(output_dict, output_list)


def deg2_analysis(entry, TSS):
	HiChIP_dict, element, deg1_dict, g_e_deg1 = entry[0], entry[1], entry[2], entry[3]
	deg2_dict, e1_name, e2_name = entry[4], entry[5], entry[6]
	for chrom, value in HiChIP_dict.items():
		if chrom in element:
			for item in value:
				if tuple(item[9:14]) in g_e_deg1:  # only proceed with cohesin loops targeted in third elements connected with a TSS
					loop = item[:6]
					target = [int(item[11]), int(item[12])]
					for line in element[chrom]:
						feature = [line[2], line[3]]
						check0 = DistalConnectCheck(feature, target, loop)
						if check0:
							for i in deg1_dict[chrom]:
								if item[10:13] == i[10:13]:
									keep = i[:]
									keep.append('loop_count')
									keep.extend(item[6:9])
									keep.extend(line)
									deg2_dict = write2dict(chrom, keep, deg2_dict)
	return(deg2_dict)


def deg3_analysis(entry, HiChIP_target, deg3):
	for chrom, value in entry.items():
		if chrom in target_dict:
			for item in value:
				e0 = [item[1], item[2], item[3]]
				e1 = [item[10], item[11], item[12]]
				e2 = [item[19], item[20], item[21]]
				confirmation = determineConfirmation(e0, e1, e2, HiChIP_target)
				if confirmation:
					keep = item[:]
					keep.append('loop_count')
					keep.extend(confirmation)
					deg3 = write2dict(chrom, keep, deg3)
	return(deg3)


def uniqueGeneDict(*arg_dicts):
# make a chr dictionary in which the values only contain info about the gene and each gene is a single entry
	result = {}
	for dictionary in arg_dicts:
		for key, value in dictionary.items():
			for item in value:
				check = item[:5]
				result = write2dict(key, check, result)
	return(result)


def commonGenes(dictionary0, dictionary1):
# returns list of entries in common in value lists belonging to the same key between two dictionaries
	result = []
	for key, value in dictionary0.items():
		if key in dictionary1:
			for item in value:
				gene0 = item[:5]
				for entry in dictionary1[key]:
					gene1 = entry[:5]
					if gene0 == gene1:
						if tuple(gene0) not in result:
							result.append(tuple(gene0))
	return(result)


def commonEntries(list0, list1): # returns new list of items in common between two lists
	result = [item for item in list0 if item in list1]
	return(result)


def removeDuplicates(return_list, *arg_list):
# remove first occuarnce of *arg_dicts entry in value list from return_dictvalue's list
	for entry in arg_list:
		for item in entry:
			if item in return_list:
				return_list.remove(item)
	return(return_list)


def determineConfirmation(e0, e1, e2, HiChIP_e3_dict):
	chrom = e0[0]
	e0_start, e0_stop = int(e0[1]), int(e0[2])
	e1_start, e1_stop = int(e1[1]), int(e1[2])
	e2_start, e2_stop = int(e2[1]), int(e2[2])
	e2_e3 = 'no'

	for item in HiChIP_e3_dict[chrom]:
		loop1 = [int(item[1]), int(item[2])]
		loop2 = [int(item[4]), int(item[5])]
		keep = item[6:14]
		target_start, target_stop = int(item[11]), int(item[12])
		target_check = BinChecker(target_start, target_stop, loop1)
		if target_check:
			check0 = BinChecker(e0_start, e0_stop, loop2)
			check1 = BinChecker(e1_start, e1_stop, loop2)
			check2 = BinChecker(e2_start, e2_stop, loop2)
			if check0 or check1:
				return(False)
			if check2:
				e2_e3 = 'yes'
		else:  # target is in bin 2 and check if feature is in bin 1
			check0 = BinChecker(e0_start, e0_stop, loop1)
			check1 = BinChecker(e1_start, e1_stop, loop1)
			check2 = BinChecker(e2_start, e2_stop, loop1)
			if check0 or check1:
				return(False)
			if check2:
				e2_e3 = 'yes'
	if e2_e3 == 'yes':
		return(keep)
	else:
		return(False)

with open(gene_file, 'r') as file:
	gene = {}
	for line in file:
		line = line.rstrip('\r\n').split('\t')
		chrom, line[1], line[2] = line[0], int(line[1]), int(line[2])
		keep = [gene_name]
		keep.extend(line[:5])
		gene = write2dict(chrom, keep, gene)
	file.close()

for item in unpack:  # write input files to dictionary with chrom as key and a list of the
	file, dictionary, name = item[0], item[1], item[2]
	with open(file, 'r') as file:
		for line in file:
			line = line.rstrip('\r\n').split('\t')
			chrom, line[1], line[2] = line[0], int(line[1]), int(line[2])
			keep = [name]
			keep.extend(line[:4])
			dictionary = write2dict(chrom, keep, dictionary)
	file.close()

for item in unpack2:  # write input files to dictionary with chrom as key and a list of the
	file, dictionary = item[0], item[1]
	with open(file, 'r') as file:
		for line in file:
				line = line.rstrip('\r\n').split('\t')
				chrom, line[1], line[2] = line[0], int(line[1]), int(line[2])
				dictionary = write2dict(chrom, line, dictionary)

for chrom, value in HiChIP_target.items():  # write coordinates for targets involved in looping to chr dict
	for item in value:
		keep = item[10:13]
		target_loop_dict = write2dict(chrom, keep, target_loop_dict)

TSS = getTSS(gene, promoter_dist)  # establish coordinates for TSS

deg0 = deg0_analysis(TSS, target_dict)  # find overlap between TSSs and target coordinates; verified by bedtools intersect
count = countUniqueGene(deg0)
print('# Number of', gene_name, 'Directly Bound to', target_name, '(i.e. 0°', target_name, ') =', count)

# find all TSSs and targets that are directly connected by looping - store info in chr dict and a list containing target info
deg1_analysis_list = [[HiChIP_target, deg1, target_deg1_list, target_name], \
[HiChIP_element1, g_e1, e1_deg1_list, element1_name], [HiChIP_element2, g_e2, e2_deg1_list, element2_name]]
for entry in deg1_analysis_list:
	entry[1], entry[2] = deg1_analysis(entry, TSS)

# identifies TSSs and targets connected by looping via a third element and stores info in chr dict
deg2_analysis_list = [[HiChIP_element1, target_dict, g_e1, e1_deg1_list, deg2, element1_name, target_name], \
[HiChIP_element2, target_dict, g_e2, e2_deg1_list, deg2, element2_name, target_name], \
[HiChIP_element1, element2, g_e1, e1_deg1_list, g_e1_e2, element1_name, element2_name], \
[HiChIP_element2, element1, g_e2, e2_deg1_list, g_e2_e1, element2_name, element1_name], \
[HiChIP_element1, element1, g_e1, e1_deg1_list, g_e1_e1, element1_name, element1_name], \
[HiChIP_element2, element2, g_e2, e2_deg1_list, g_e2_e2, element2_name, element2_name]]
for entry in deg2_analysis_list:
	entry[4] = deg2_analysis(entry, TSS)
count = countUniqueGene(deg2)
print('# Number of', gene_name, 'Looped to', target_name, 'via', element1_name, 'or', element2_name, '(i.e. 2°', target_name, ') =', count)

# identifies TSSs and targets connected by looping via a third and fourth element and stores info in chr dict
deg3_analysis_list = [g_e1_e2, g_e2_e1, g_e1_e1, g_e2_e2]
for entry in deg3_analysis_list:
	deg3 = deg3_analysis(entry, HiChIP_target, deg3)
count = countUniqueGene(deg3)
print('# Number of', gene_name, 'with 3° connection with', target_name, 'via', element1_name, 'and', element2_name, '=', count)

unique_genes = uniqueGeneDict(deg0, deg1, deg2, deg3)  # store all genes whose TSS is connected to achor in some way in chr dict

deg0_deg1 = commonGenes(deg0, deg1)  # find genes whose connected to the anchor via multiple methods
deg0_deg2 = commonGenes(deg0, deg2)
deg0_deg3 = commonGenes(deg0, deg3)
deg1_deg2 = commonGenes(deg1, deg2)
deg1_deg3 = commonGenes(deg1, deg3)
deg2_deg3 = commonGenes(deg2, deg3)
deg0_deg1_deg2 = commonEntries(deg0_deg1, deg0_deg2)
deg0_deg2_deg3 = commonEntries(deg0_deg2, deg0_deg3)
deg0_deg1_deg3 = commonEntries(deg0_deg1, deg0_deg3)
deg1_deg2_deg3 = commonEntries(deg1_deg2, deg1_deg3)
deg0_deg1_deg2_deg3 = commonEntries(deg0_deg1_deg2, deg1_deg2_deg3)

deg0_deg1_deg2 = removeDuplicates(deg0_deg1_deg2, deg0_deg1_deg2_deg3)  # eliminate duplicates between multiple confirmation lists
deg0_deg2_deg3 = removeDuplicates(deg0_deg2_deg3, deg0_deg1_deg2_deg3)
deg0_deg1_deg3 = removeDuplicates(deg0_deg1_deg3, deg0_deg1_deg2_deg3)
deg1_deg2_deg3 = removeDuplicates(deg1_deg2_deg3, deg0_deg1_deg2_deg3)
deg0_deg1 = removeDuplicates(deg0_deg1, deg0_deg1_deg2, deg0_deg1_deg3, deg0_deg1_deg2_deg3)
deg0_deg2 = removeDuplicates(deg0_deg2, deg0_deg2_deg3, deg0_deg1_deg2, deg0_deg1_deg2_deg3)
deg0_deg3 = removeDuplicates(deg0_deg3, deg0_deg1_deg3, deg0_deg2_deg3, deg0_deg1_deg2_deg3)
deg1_deg2 = removeDuplicates(deg1_deg2, deg1_deg2_deg3, deg0_deg1_deg2, deg0_deg1_deg2_deg3)
deg1_deg3 = removeDuplicates(deg1_deg3, deg1_deg2_deg3, deg0_deg1_deg3, deg0_deg1_deg2_deg3)
deg2_deg3 = removeDuplicates(deg2_deg3, deg1_deg2_deg3, deg0_deg2_deg3, deg0_deg1_deg2_deg3)

count = countUniqueGene(unique_genes)
print('# Final Unique Counts for 0°, 1°, 2° and 3° connections between', gene_name, 'and', target_name, '=', count)
print('# Number of', gene_name, 'with 0° and 1° connections with', target_name, '=', len(deg0_deg1))
print('# Number of', gene_name, 'with 0° and 2° connections with', target_name, '=', len(deg0_deg2))
print('# Number of', gene_name, 'with 0° and 3° connections with', target_name, '=', len(deg0_deg3))
print('# Number of', gene_name, 'with 1° and 2° connections with', target_name, '=', len(deg1_deg2))
print('# Number of', gene_name, 'with 1° and 3° connections with', target_name, '=', len(deg1_deg3))
print('# Number of', gene_name, 'with 2° and 3° connections with', target_name, '=', len(deg2_deg3))
print('# Number of', gene_name, 'with 0°, 1°, and 2° connections with', target_name, '=', len(deg0_deg1_deg2))
print('# Number of', gene_name, 'with 0°, 1°, and 3° connections with', target_name, '=', len(deg0_deg1_deg3))
print('# Number of', gene_name, 'with 0°, 2°, and 3° connections with', target_name, '=', len(deg0_deg2_deg3))
print('# Number of', gene_name, 'with 1°, 2°, and 3° connections with', target_name, '=', len(deg1_deg2_deg3))
print('# Number of', gene_name, 'with 0°, 1°, 2°, and 3° connections with', target_name, '=', len(deg0_deg1_deg2_deg3))
count = sum([len(deg0_deg1), len(deg0_deg2), len(deg0_deg3), len(deg1_deg2), len(deg1_deg3), len(deg2_deg3),\
 len(deg0_deg1_deg2), len(deg0_deg1_deg3), len(deg0_deg2_deg3), len(deg1_deg2_deg3),len(deg0_deg1_deg2_deg3)])
print('# Number of', gene_name, 'with mutiple mixed connections (0°, 1°, 2°, and/or 3°) with', target_name, '=', count)

deg0_sort = OrderChrDict(deg0)  # order output dicts
deg1_sort = OrderChrDict(deg1)
deg2_sort = OrderChrDict(deg2)
deg3_sort = OrderChrDict(deg3)

output_dicts = [(deg0_output_file, deg0_sort), (deg1_output_file, deg1_sort),\
(deg2_output_file, deg2_sort), (deg3_output_file, deg3_sort)]

for item in output_dicts:
	file, dictionary = item[0], item[1]
	with open(file, 'w') as file:
		for chrom, value in dictionary.items():
			for item in value:
				line = []
				for entry in item:
					entry = str(entry)
					line.append(entry)
				file.write(('\t').join(line) + '\n')
print(timeit.default_timer() - start_time)
