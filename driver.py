#TODO: Maybe work on a fix for duplicate rows in csv?

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
	"""
	cc = countycodes.findall(line)
	if cc is not None:
		for item in cc:
			if item in ccodes:
				if(human_readable):
					print("LOCATION " + str(cmap[item]) + " County, line " + str(lineNum))
				found_list[1].append(cmap[item])

	"""
	#Look for NER terms
	for term in set_of_vals:
		if term.casefold() in line:
			if(human_readable):
				print("TERM " + str(term.upper()) + ", line " + str(lineNum))
			#found_list[0].append(term)
			found_list.append([term, lineNum])

	"""
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
	"""

#Driver method
def main():

	#How far above and below the line we should look
	SEARCH_SIZE = 5

	#Map Artifact(Trinomial?)-> Array of terms to be printed
	result = {}

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
		tris_in_line = trinomial_regex.findall(content[line_num])
		if tris_in_line is None:
			continue
		for trinomial in tris_in_line:
			if trinomial in RELEVANT_TRINOMIALS:
				#item->period terms, list of str
				#i0 -> periods, #i1 -> other data
				if trinomial not in result:
					result[trinomial] = [[],[]]
				if(human_readable):
					print("***TRINOMIAL " + str(trinomial.upper()) + ", line " + str(line_num))
				search_space = ''
				for line in range(line_num - SEARCH_SIZE, line_num + SEARCH_SIZE + 1):
					if line >= 0 and line < len(content):
						search_space += content[line]

				local_trin_count = len(trinomial_regex.findall(search_space))
				sentences = split_into_sentences(search_space)
				
				#Parsing regex fails for image captioning
				if len(sentences) == 0:
					sentences.append(search_space)

				possible_pairs = []
				trinomial_sentence_location = -1;
				for sen_index in range(len(sentences)):
					if trinomial in sentences[sen_index]:
						trinomial_sentence_location = sen_index
					find_entries(sentences[sen_index].casefold(), sen_index, human_readable, possible_pairs)

				#If there are other terms nearby, extract carefully
				if local_trin_count > 1:
					optimal_term = get_optimal_term(possible_pairs, trinomial_sentence_location, sentences, trinomial)
					if optimal_term is not None:
						result[trinomial][0] = optimal_term[0]
						write_out(output, (trinomial, optimal_term[0]))
				#Otherwise, grab everything useful
				else:
					print(sen_index)
					find_entries(sentences[sen_index].casefold(), sen_index, human_readable, result[trinomial])

				#No need to store result with no found terms
				if result[trinomial][0] == None:
					del result[trinomial]

				if(human_readable):
					print("\n")

	output.close()

def write_out(f, t):
	trinomial = t[0]
	period = t[1]
	f.write(str(trinomial))
	f.write("," + str(period))
	index = periodo[1].index(period)
	f.write("," + str(periodo[4][index])) #Write periodo[4], in time
	f.write("," + str(periodo[5][index])) #Write periodo[5], out time
	f.write("\n")

#Find the term that is most likely to match up with the trinomial
#@param matches is a list of size 2 lists "tuples" of form (term, sentence_index)
#@param key_index is sentence index of trinomial
#@param sentences is list of sentences containing results
#@param trin is the trinomial
def get_optimal_term(matches, key_index, sentences, trin):

	#Only keep values in the nearest sentence(s)
	matches.sort(key = lambda tpl : abs(key_index - tpl[1]))
	closest_val = None
	best_term = None
	if len(matches) != 0:
		for tpl in matches:
			tpl[1] = abs(key_index - tpl[1])
		matches.sort(key = lambda tpl : tpl[1])
		closest_val = matches[0][1]
		result = []
		for tpl in matches:
			if tpl[1] == closest_val:
				result.append(tpl)
		matches = result
		best_term = matches[0]

	#Within the nearest sentences, figure out which one is closest
	if len(matches) > 1:
		agg_sentence = ""
		#Make all sentences one String for convenience
		for si in range(key_index - closest_val, key_index + closest_val + 1):
			if si >= 0 and si < len(sentences):
				agg_sentence += sentences[si]
		#Everything is on the sentence at key_index
		if agg_sentence == "":
			agg_sentence = sentences[key_index]

		#Run distances through in order of longest tpl[0] to shortest
		#This is to prevent terms that are substrings of other terms
		#causing problems
		matches.sort(key = lambda tpl : len(tpl[0]))
		matches = list(reversed(matches))
		
		min_distance = len(agg_sentence) + 1;
		best_term = None
		for tpl in matches:
			dist = distance(agg_sentence.casefold(), tpl[0].casefold(), trin.casefold())
			if dist <= min_distance:
				min_distance = dist
				best_term = tpl

	return best_term



#Really basic way of defining a distance between two words
#based on counting number of whitespace between them.
#@param s is the parent string
#@param w1 and @param w2 are words to find distance between
def distance(s, w1, w2):
	#Get index of w1
	print("the stuff is ",w1, "SENTNECE", s)
	print("nagatoro ", w1 in s)
	i1 = s.index(w1)
	#Get index of w2
	i2 = s.index(w2)
	#Should never happen
	if i1 < 0 or i2 < 0:
		return -1
	i1, i2 = min(i1, i2), max(i1, i2)
	#Count occurances of white space in between
	s_copy = s[i1:i2+1]
	spaces = re.findall('\s+', s_copy)
	#Return number of whitespace
	return len(spaces)

def write_dictionary(f, d):
	for artifact in d.keys():
		for period in set(d[artifact][0]):
			f.write(str(artifact))
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

#Credit to D Greenberg on Github
def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences


"""
Useful Global Variables, setup
"""

#Sentence Splitting
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

#Constants
timeExclude = ["late", "early", "the past", "once", "falls", "previously", "now", "fall", "recently", "time", "present", "past", "current", "currently"]
countycodes = re.compile("\s([A-Z]{2})[\s,\.,\,]")
trinomial_regex = re.compile("41[a-zA-Z]{2}[0-9]{1,4}")
bp_dates = re.compile("\d+ B\.?[P]\.?") #only BP
#bp_dates = re.compile("\d+ B\.?[P,C]\.?") #inc. BC

#Harvest vocabs from files
RELEVANT_TRINOMIALS, counties, periodo = harvest()

#set_of_vals = set(periodo[1] + periodo[4] + periodo[5])
set_of_vals = set(periodo[1])

#x = list(set_of_vals)
#x.sort(key = lambda s : len(s))

#Set up s.t. dictionary can translate county codes into names
cnames = []
ccodes = []
for item in counties:
	cnames.append(item[0])
	ccodes.append(item[1])
cmap = dict(zip(ccodes, cnames))

main()
