import re
import csv
import sys
import codecs
import json	
import os
import glob
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
def find_entries(line, lineNum):
	#Looks for county codes and ensures we count them as counties (ha)
	cc = countycodes.findall(line)
	if cc is not None:
		for item in cc:
			if item in ccodes:
				print("LOCATION " + str(cmap[item]) + " County, line " + str(lineNum))
	#Look for NER terms
	#TODO: This is probably where we should declare a list of the terms 
	#for the CSV, and filling them in below. We wouldn't even need to do 
	#10 different for loops, we could just do a doubly nested over the 
	#periodo list. At the very end, we could take each empty field in the
	#list and abstract in the values from the periodo list.
	#TODO: maybe the optimal setup would be a map of trinomial->array
	for term in set_of_vals:
		if term in line:
			print("TERM " + str(term.upper()) + ", line " + str(lineNum))

	#Look for BP dates (tend to get lost) w regex
	bp_check = bp_dates.findall(line)
	if bp_check is not None:
			for item in bp_check:
				print("DATE " + str(item.upper()) + ", line " + str(lineNum))
	#Stanford NER Method, goes in and finds dates and spelled out
	#counties
	ents = nlpGetEntities(line)
	if len(ents) is not 0:
		for item in ents:
			#Grab date
			if item[1] == 'DATE' and item[0].lower() not in timeExclude:
				print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(lineNum))
			#Grab county
			if item[1] == 'LOCATION':
				if item[0] in cnames:
					print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(lineNum))
				elif ' ' in item[0] and item[0].split(' ',1)[1].upper() == 'COUNTY':
					if item[0].split(' ',1)[0] in cnames:
						print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(lineNum))

#Driver method
def main():

	#How far above and below the line we should look
	SEARCH_SIZE = 2
	asciiFile = str(sys.argv[1])
	lineNum = 0
	with codecs.open(asciiFile, 'r', encoding = 'utf-8', errors='ignore') as f:
		content = f.readlines()

	#for line in f:
	for line_num in range(len(content)):

		#Look for Trinomials using regex
		trin = trinomials.findall(content[line_num])
		if trin is not None:
				for item in trin:
					if item not in relevantTrinomials or item in relevantTrinomials:
						print("***ARTIFACT " + str(item.upper()) + ", line " + str(line_num))
						search_space = ''
						for i in range(line_num - SEARCH_SIZE, line_num + SEARCH_SIZE):
							if i >= 0 and i < len(content):
								search_space += content[i]

						entries = find_entries(search_space, i)
						print("\n")


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
Useful Global Variables
"""
#Constants
timeExclude = ["late", "early", "the past", "once", "falls", "previously", "now", "fall", "recently", "time", "present", "past", "current", "currently"]
countycodes = re.compile("\s([A-Z]{2})[\s,\.,\,]")
trinomials = re.compile("41[a-zA-Z]{2}[0-9]{1,4}")
bp_dates = re.compile("\d+ B\.?[P]\.?") #only BP
#bp_dates = re.compile("\d+ B\.?[P,C]\.?") #inc. BC

#Harvest vocabs from files
relevantTrinomials, counties, periodo = harvest()

#Separate periodo data to make it more programmer friendly
#TODO get this operating in terms of periodo list, so can
#delete this shit
period = periodo[0]
"""
label = periodo[1]
spatial_coverage = periodo[2]
gazetteer_links = periodo[3]
start = periodo[4]
stop = periodo[5]
authority = periodo[6]
source = periodo[7]
publication_year = periodo[8]
derived_periods = periodo[9]
"""

set_of_vals = set(periodo[1] + periodo[4] + periodo[5])

#Set up s.t. dictionary can translate county codes into names
cnames = []
ccodes = []
for item in counties:
	cnames.append(item[0])
	ccodes.append(item[1])
cmap = dict(zip(ccodes, cnames))
main()
