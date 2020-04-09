#TODO: Fix bug re aiobe
#TODO: archaic late archaic issue
import os
import re
import csv
import sys
import glob
import json	
import codecs
from subprocess import check_output


#Harvest NER vocabulary from relevant files
def harvest():

	#get relevant trinomials from csv
	relevantTrinomials = []
	with open('vocabularies/relevantTrinomials.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	for sublist in data:
		if sublist[0] is not '':
			relevantTrinomials.append(sublist[0])

	#get counties from csv
	relevantCounties = []
	with open('vocabularies/relevantCounties.csv', newline='') as f:
		reader = csv.reader(f)
		counties = list(reader)

	#get periodo vocabs from all periodo csvs
	label = []
	periodo = []
	for i in range(10):
		periodo.append([])
	for filename in glob.glob('vocabularies/periodo*'):
		with open(filename, newline='') as f:
			reader = csv.reader(f)
			data = list(reader)

			#Transpose columns and rows of the CSV,
			#ignoring the labels, for convenience
			for row in range(1, len(data)):
				for column in range(len(data[row])):
					#if row != 0:
					if data[row][column] is not '':
						periodo[column].append(data[row][column])


	return relevantTrinomials, counties, periodo


#Once we find a trinomial, we call find_entries to look for useful neighboring
#vocabulary terms that might be associated with it
def find_entries(line, lineNum, human_readable, found_list):
	#Looks for county codes and ensures we count them as counties (ha)
	cc = countycodes.findall(line)
	if cc is not None:
		for item in cc:
			if item in ccodes:
				if(human_readable):
					print("LOCATION " + str(cmap[item]) + " County, line " + str(lineNum))
				found_list[1].append(cmap[item])
	#Look for NER terms
	for term in set_of_vals:
		if term in line:
			if(human_readable):
				print("TERM " + str(term.upper()) + ", line " + str(lineNum))
			found_list[0].append(term)

	#Look for BP dates (tend to get lost) w regex
	bp_check = bp_dates.findall(line)
	if bp_check is not None:
			for item in bp_check:
				if(human_readable):
					print("DATE " + str(item.upper()) + ", line " + str(lineNum))
				found_list[1].append(item)
	#Stanford NER Method, goes in and finds dates and spelled out
	#counties
	ents = nlpGetEntities(line)
	if len(ents) is not 0:
		for item in ents:
			#Grab date
			if item[1] == 'DATE' and item[0].lower() not in timeExclude:
				if(human_readable):
					print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(lineNum))
				found_list[1].append(item[0])
			#Grab county
			if item[1] == 'LOCATION':
				if item[0] in cnames:
					if(human_readable):
						print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(lineNum))
					found_list[1].append(item[0])
				elif ' ' in item[0] and item[0].split(' ',1)[1].upper() == 'COUNTY':
					if item[0].split(' ',1)[0] in cnames:
						if(human_readable):
							print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(lineNum))
						found_list[1].append(item[0])

#Driver method
def main():

	#How far above and below the line we should look
	SEARCH_SIZE = 2

	#Map Artifact(Trinomial?)-> Array of terms to be printed
	artifacts = {}

	asciiFile = str(sys.argv[1])
	human_readable_input = str(sys.argv[2]).lower()
	human_readable = False
	if human_readable_input == 'y' or human_readable_input == 'yes':
		human_readable = True

	output = open("out.csv", "a+")

	with codecs.open(asciiFile, 'r', encoding = 'utf-8', errors='ignore') as f:
		content = f.readlines()

	#for line in f:
	for line_num in range(len(content)):

		#Look for Trinomials using regex
		trin = trinomials.findall(content[line_num])
		if trin is not None:
				for item in trin:
					if item in relevantTrinomials:
						#item->period terms, list of str
						#i0 -> periods, #i1 -> other data
						artifacts[item] = [[],[]]
						if(human_readable):
							print("***ARTIFACT " + str(item.upper()) + ", line " + str(line_num))
						search_space = ''
						for i in range(line_num - SEARCH_SIZE, line_num + SEARCH_SIZE):
							if i >= 0 and i < len(content):
								search_space += content[i]

						entries = find_entries(search_space, i, human_readable, artifacts[item])
						if(human_readable):
							print("\n")
	#TODO: Call method to fill in blanks for the artifacts.get(Trinomial)s
	#Then, write to output
	write_dictionary(output, artifacts)
	output.close()

def write_dictionary(f, d):
	for artifact in d.keys():
		f.write(str(artifact))
		for period in d[artifact][0]:
			f.write("," + str(period))
			index = periodo[1].index(period)
			f.write("," + str(periodo[4][index])) #Write periodo[4], in time
			f.write("," + str(periodo[5][index])) #Write periodo[5], out time
		f.write("\n")


#iso8601Date: YYYY-MM-DDTHH:MM:SS
def nlpGetEntities(text, host='localhost', iso8601Date='', labelLst=['DATE','LOCATION']):

	labelLst = set(labelLst)
	iso8601Date = iso8601Date.strip()
	if( len(iso8601Date) != 0 ):
		iso8601Date = ',"date":"' + iso8601Date + '"'

	request = host + ':9000/?properties={"annotators":"entitymentions","outputFormat":"json"' + iso8601Date + '}'
	entities = []
	dedupSet = set()

	try:
		output = check_output(['wget', '-q', '-O', '-', '--post-data', text, request])
		parsed = json.loads(output.decode('utf-8'))

		if( 'sentences' not in parsed ):
			return []

		for sent in parsed['sentences']:
			
			if( 'entitymentions' not in sent ):
				continue

			for entity in sent['entitymentions']:

				#text is entity, ner is entity class
				dedupKey = entity['text'] + entity['ner']
				
				if( dedupKey in dedupSet or entity['ner'] not in labelLst ):
					continue

				if( len(entity['text']) != 0 ):
					entities.append( [entity['text'], entity['ner']] )
					dedupSet.add(dedupKey)
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		errorMessage = fname + ', ' + str(exc_tb.tb_lineno)  + ', ' + str(sys.exc_info())
		print('\tERROR:', errorMessage)

	return entities


"""
Useful Global Variables, setup
"""
#Constants
timeExclude = ["late", "early", "the past", "once", "falls", "previously", "now", "fall", "recently", "time", "present", "past", "current", "currently"]
countycodes = re.compile("\s([A-Z]{2})[\s,\.,\,]")
trinomials = re.compile("41[a-zA-Z]{2}[0-9]{1,4}")
bp_dates = re.compile("\d+ B\.?[P]\.?") #only BP
#bp_dates = re.compile("\d+ B\.?[P,C]\.?") #inc. BC

#Harvest vocabs from files
relevantTrinomials, counties, periodo = harvest()

set_of_vals = set(periodo[1] + periodo[4] + periodo[5])

#Set up s.t. dictionary can translate county codes into names
cnames = []
ccodes = []
for item in counties:
	cnames.append(item[0])
	ccodes.append(item[1])
cmap = dict(zip(ccodes, cnames))

main()
