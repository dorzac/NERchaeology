"""High Priority"""
# TODO: four date columns
# TODO: Handle prehistoric case >> Rough fix, use umbrella bag
# TODO: Handle Toyah issue where we compare the dates
"""Low Priority"""
# TODO: Write custom sort for periodo terms that's safer than zipping
# TODO: Use dates as a refinement mechanism
# TODO: Instead of looking for TRI + TERM + DATE, look for TRI + TERM 
#		and TRI + DATE separately

import os
import re
import csv
import sys
import glob
import json
import codecs
import datetime
from nltk import tokenize
from operator import itemgetter
from subprocess import check_output
from record import *

"""
Useful Global Variables, Expressions, etc
"""

#Sentence Splitting
alphabets = "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = ("(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|"
			"We\s|But\s|However\s|That\s|This\s|Wherever)")
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

#Constants
timeExclude = ["late", "early", "the past", "once", "falls", \
				"previously", "now", "fall", "recently", "time", \
				"present", "past", "current", "currently"]
countycodes = re.compile("\s([A-Z]{2})[\s,\.,\,]")
trinomial_regex = re.compile("41[a-zA-Z]{2}[0-9]{1,4}")
#bp_dates = re.compile("\d+ B\.?[P]\.?") #only BP
bp_dates = re.compile("\d+(\s?b\.?[p,c]\.?)?\s?(.|to|and)?\s?\d+\s?(b\.?[p,c]\.?)")
pub_date = re.compile("((19|20)[0-9]{2})")		
cents = re.compile("(((beginning|middle|end|early|mid|late|[0-9a-z]*(st|[^a]nd|rd|th)\s)[a-z ]*)?(([a-z]*(\-|\s))?[a-z]*)[0-9]{0,2}?(st|nd|rd|th)\s(century|millenia)(\s(b\.?c\.?e\.?|c\.?e\.?|b\.?c\.?|a\.?d\.?))?)")

NEGATIVES = [" none ", " not ", " no "] #CONSIDER: 'yet to find'

#Globals
human_readable = False
input_file = ""
date = 0
relevant_trinomials = []
set_of_vals = []
counties = []
periodo = []

SEARCH_SIZE = 3 # size 3 seems to be about optimal

#Set up s.t. dictionary can translate county codes into names
cnames = []
ccodes = []
for item in counties:
	cnames.append(item[0])
	ccodes.append(item[1])
cmap = dict(zip(ccodes, cnames))

#NOTE: Based on date choose name vs name Phase
#NOTE: For these, only include the latest one before pub date
interchangeable_terms = ['Archaic', 'Historic', 'Early Archaic',\
		'Late Archaic', 'Late Paleoindian', 'Late Prehistoric', \
		'Middle Archaic', 'Paleoindian',]

def harvest():
	"""
	Method called first.
	Reads in vocabulary files and stores them.
	"""

	#get relevant trinomials from csv
	relevant_trinomials = []
	with open('vocabularies/relevantTrinomials.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	for sublist in data:
		if sublist[0] != '':
			relevant_trinomials.append(sublist[0])

	#get counties from csv
	with open('vocabularies/relevantCounties.csv', newline='') as f:
		reader = csv.reader(f)
		counties = list(reader)

	#get periodo vocabs from all periodo csvs
	periodo = []
	periodo.extend([[] for col in range(9)])
	for filename in glob.glob('vocabularies/periodo*'):
		with open(filename, newline='') as f:
			reader = csv.reader(f)
			data = list(reader)

			if int(data[1][8]) >= date:
				print("Not including", filename)
				continue
			print("Including",filename)

			#Transpose columns and rows of the CSV,
			#ignoring the labels, for convenience
			for row in range(1, len(data)):
				for column in range(len(data[row])):
					if data[row][column] is not '':
						periodo[column].append(data[row][column])

	periodo[0], periodo[1], periodo[4], periodo[5], periodo[8] = \
		(list(t) for t in zip(*sorted( \
		zip(periodo[0], periodo[1], periodo[4], periodo[5], periodo[8]), \
		key=lambda l1:l1[1])))
	print("NAGA START")
	for e in range(len(periodo[1])):
		print(periodo[1][e], periodo[4][e], periodo[5][e], periodo[8][e])
	print("NAGA END")

	# TODO: This only sorts 5 columns in parallel. Maybe write
	# custom sort to clean this up
	periodo[0], periodo[1], periodo[4], periodo[5], periodo[8] = \
		(list(t) for t in zip(*sorted( \
		zip(periodo[0], periodo[1], periodo[4], periodo[5], periodo[8]), \
		key=lambda l1:len(l1[1]), reverse=True)))

	print("NAGA START")
	for e in range(len(periodo[1])):
		print(periodo[1][e], periodo[4][e], periodo[5][e], periodo[8][e])
	print("NAGA END")


	return relevant_trinomials, counties, periodo


def find_terms(line, line_num, found_list):
	"""
	@param line is the string of text which to parse
	@param line_num is the line number, used for output and checking
		   relationship between term location and site location
	@param human_readable is a boolean used for output
	@param found_list is a list of lists with entries of the form
		   [term, line_num] (must remain mutable)
	Checks a line of text against the defined vocabularies.
	Grabs everything relevant, nondiscretely.
	"""
	#TODO: If we find a term, compare pub date with periodo[8]
	#line = re.sub(r"\s+", ' ', line)
	terms = set_of_vals
	for term in terms:
		if term.casefold() in line:
			for negator in NEGATIVES:
				if negator.casefold() in line:
					return
			line = line.replace(term.casefold(), '')
			found_list.append([term, line_num])


def find_times(line, line_num, found_list):

	#Look for BP dates (tend to get lost) w regex
	bp_check = bp_dates.findall(line)
	if bp_check is not None:
			for item in bp_check:
				found_list.append(item[0])

	century_check = cents.findall(line)
	if century_check is not None:
			for item in century_check:
				found_list.append(item[0])


def parse_content(content):
	#TODO: Docstring

	freqs = {}
	records = set()
	for line_num in range(len(content)):
		tris_in_line = trinomial_regex.findall(content[line_num])
		if tris_in_line is None:
			continue
		for trinomial in tris_in_line:
			if trinomial in relevant_trinomials:
				if trinomial in freqs:
					freqs[trinomial] = freqs[trinomial] + 1
				else:
					freqs[trinomial] = 1
				r = Record(site_name = trinomial, site_name_line = line_num)

				sentences, local_trin_count = get_search_space(content, r)
				possible_pairs = get_possible_pairs(sentences, r)



				#If there are other terms nearby, extract carefully
				if local_trin_count > 1:
					optimal_term = get_optimal_term(
							possible_pairs, r.site_name_line,
							sentences, trinomial)
					if optimal_term is not None:
						r.period_term = optimal_term	
						records.add(r)

				#Otherwise, grab everything useful
				else:
					for pair in possible_pairs:
						tmp = Record( \
							site_name = r.site_name, \
							site_name_line = line_num, \
							period_term = pair[0], \
							dates = r.dates)
						records.add(tmp)

				r.site_name_line = line_num

	implement_freqs(freqs, records)
	return records


def get_date(content):
	now = datetime.datetime.now()
	dates = pub_date.findall(input_file)
	if dates:
		return int(dates[0][0])
	for i in range(len(content)):
		if i > 20:
			break
		dates = pub_date.findall(content[i])
		if dates:
			return int(dates[0][0])
	return int(now.year)


def implement_freqs(freqs, records):
	"""
	@param freqs is a dictionary mapping a trinomial to its in
		   document frequency
	@param records is a set of record objects
	Calculates the frenquency as a percentage of a trinomial in a doc
	"""	
	total = 0
	for e in freqs:
		total += freqs[e]
	for record in records:
		record.freq = round(freqs[record.site_name] / total, 3)


def display_hr(records):
	"""
	@param records is an array of record objects.
	Prints data to console
	"""
	print("======"+str(len(records))+" Records Stored======")
	for record in records:
		print("SITE:", record.site_name, "line", record.site_name_line)
		print("PERIOD:", record.period_term)
		if record.dates:
			print("EXPLICIT DATES:", record.dates)
		print("\n")


def get_possible_pairs(sentences, rec):
	"""
	@param sentences is an array of sentences to scan for terma
	@param rec is a record object for a single site
	@return an array of pairings between site and term
	"""
	possible_pairs = []
	for sen_index in range(len(sentences)):
		if rec.site_name in sentences[sen_index]:
			rec.site_name_line = sen_index

		find_terms(
				sentences[sen_index].casefold(),
				sen_index, possible_pairs)

		found_times = []
		find_times(sentences[sen_index].casefold(), sen_index, found_times)
	rec.dates = found_times
	return possible_pairs


def get_search_space(content, rec):
	"""
	@param line_num is the line number with regard to the document
	@param content is a list of lines representing the document
	@param trinomial is the trinomial the search space is being built around.
	@return a tuple of the form (list of sentences, number of trinomials in
			those sentences.
	Loops over lines surrounding the trinomial in question and appends those
	lines to a string, ignoring lines that are a line-break away from the
	trinomial (i.e., in a different paragraph.) After developing the search
	space, it is tokenized into sentences.
	"""
	search_space = ''
	flag = False
	for line in range(rec.site_name_line - SEARCH_SIZE, 
		rec.site_name_line + SEARCH_SIZE + 1):
		if line >= 0 and line < len(content):
			search_space += content[line]
			if rec.site_name in content[line]:
				flag = True
			if content[line].strip() == "":
				if not flag:
					search_space = ""
				else:
					break

	search_space = re.sub(r"\s+", ' ', search_space)
	local_trin_count = len(set(trinomial_regex.findall(search_space)))
	#TODO: For some reason this fails, so use tokenize
	#sentences = split_into_sentences(search_space)
	sentences = tokenize.sent_tokenize(search_space)

	#Parsing regex fails for image captioning, workaround
	if not sentences:
		sentences.append(search_space)

	return sentences, local_trin_count


def write_record(f, r):
	"""
	@param f a file to write to
	@param t a Record dataclass
	Writes the file in CSV form.
	"""
	f.write(r.site_name)
	f.write("," + r.period_term)
	index = periodo[1].index(r.period_term)
	f.write("," + str(periodo[4][index])) #Write periodo[4], in time
	f.write("," + str(periodo[5][index])) #Write periodo[5], out time
	f.write("," + str(periodo[0][index])) #Write periodo[0], URI
	f.write("," + str(r.freq))
	f.write("," + input_file) #Write filename
	f.write("\n")


def get_optimal_term(matches, key_index, sentences, trin):
	"""
	Finds the sentence(s) closest to the relevant trinomial
	that contain terms. If there are multiple closest terms,
	return the one that is closest in terms of words.
	@param matches is a list of size 2 lists "tuples" of form 
		   (term, sentence_index)
	@param key_index is sentence index of trinomial
	@param sentences is list of sentences containing results
	@param trin is the trinomial
	@return a tuple of the form (trinomial, period_term)
	"""

	#Only keep values in the nearest sentence(s)
	closest_val = None
	best_term = None
	if matches:
		for tpl in matches:
			tpl[1] = abs(key_index - tpl[1])
		matches.sort(key=lambda tpl:tpl[1])
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
		agg_sentence = re.sub(r"\s+", ' ', agg_sentence)

		#Run distances through in order of longest tpl[0] to shortest
		#This is to prevent terms that are substrings of other terms
		#causing problems
		matches.sort(key=lambda tpl:len(tpl[0]))
		matches = list(reversed(matches))

		min_distance = len(agg_sentence) + 1
		best_term = None
		dist = 1000
		for tpl in matches:
			while tpl[0].casefold() in agg_sentence:
				dist = distance(agg_sentence.casefold(), tpl[0].casefold(), trin.casefold())
				agg_sentence = agg_sentence.replace(tpl[0].casefold(), '', 1)
			if dist <= min_distance:
				min_distance = dist
				best_term = tpl

	if best_term != None:
		return best_term[0]
	return None


def distance(s, w1, w2):
	"""
	Really basic way of defining a distance between two words
	based on counting number of whitespace between them.
	@param s is the parent string 
	@param w1 and @param w2 are words to find distance between
	"""

	#Get index of w1
	i1 = s.index(w1)
	#Get index of w2
	i2 = s.index(w2)
	#Should never happen
	if i1 < 0 or i2 < 0:
		return -1
	i1, i2 = min(i1, i2), max(i1, i2)
	#Count occurances of white space in between
	s_copy = s[i1:i2+1]
	spaces = re.findall("\s+", s_copy)
	#Return number of whitespace
	return len(spaces)


#iso8601Date: YYYY-MM-DDTHH:MM:SS
def nlpGetEntities(text, host='localhost', iso8601Date='', labelLst=['DATE', 'LOCATION']):
	"""
	Interfaces with Stanford's NER platform
	via socket.
	@param labelLst accounts for term types
	"""

	labelLst = set(labelLst)
	iso8601Date = iso8601Date.strip()
	if len(iso8601Date) != 0:
		iso8601Date = ',"date":"' + iso8601Date + '"'

	request = host + ':9000/?properties={"annotators":"entitymentions","outputFormat":"json"' + iso8601Date + '}'
	entities = []
	dedupSet = set()

	try:
		output = check_output(['wget', '-q', '-O', '-', '--post-data', text, request])
		parsed = json.loads(output.decode('utf-8'))

		if 'sentences' not in parsed:
			return []

		for sent in parsed['sentences']:

			if 'entitymentions' not in sent:
				continue

			for entity in sent['entitymentions']:

				#text is entity, ner is entity class
				dedupKey = entity['text'] + entity['ner']

				if dedupKey in dedupSet or entity['ner'] not in labelLst:
					continue

				if len(entity['text']) != 0:
					entities.append([entity['text'], entity['ner']])
					dedupSet.add(dedupKey)
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		errorMessage = fname + ', ' + str(exc_tb.tb_lineno)  + ', ' + str(sys.exc_info())
		print('\tERROR:', errorMessage)

	return entities


#Credit to D Greenberg on Github
def split_into_sentences(text):
	"""
	Powerful regex that splits a text into strings.
	"""

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


def main():
	"""
	TODO: Docstring
	"""
	global human_readable
	global relevant_trinomials
	global counties
	global periodo
	global set_of_vals
	global input_file
	global date

	input_file = str(sys.argv[1])
	human_readable_input = str(sys.argv[2]).lower()
	#human_readable = False
	if human_readable_input == 'y' or human_readable_input == 'yes':
		human_readable = True

	with codecs.open(input_file, "r", encoding="utf-8", \
			errors="ignore") as f:
		content = f.readlines()

	input_file = os.path.basename(input_file)
	date = max(1981, get_date(content))

	l = []
	for line in content:
		find_times(line, 0, l)
	print("Found in this document:")
	print(l)
	print("\n")

	relevant_trinomials, counties, periodo = harvest()
	set_of_vals = periodo[1]
	records = parse_content(content)

	o = open("out.csv", "a+")
	for r in records:
		write_record(o, r)
	o.close()

	if human_readable:
		display_hr(records)

main()


"""
Here be monsters
"""


def find_more_stuff(line, line_num, human_readable, found_list):
	#Looks for county codes and ensures we count them as counties (ha)
	cc = countycodes.findall(line)
	if cc is not None:
		for item in cc:
			if item in ccodes:
				if(human_readable):
					print("LOCATION " + str(cmap[item]) + " County, line " + str(line_num))
				found_list[1].append(cmap[item])

	#Look for BP dates (tend to get lost) w regex
	bp_check = bp_dates.findall(line)
	if bp_check is not None:
			for item in bp_check:
				if(human_readable):
					print("DATE " + str(item.upper()) + ", line " + str(line_num))
				found_list[1].append(item)
	#Stanford NER Method, goes in and finds dates and spelled out
	#counties
	ents = nlpGetEntities(line)
	if len(ents) is not 0:
		for item in ents:
			#Grab date
			if item[1] == 'DATE' and item[0].lower() not in timeExclude:
				if(human_readable):
					print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(line_num))
				found_list[1].append(item[0])
			#Grab county
			if item[1] == 'LOCATION':
				if item[0] in cnames:
					if(human_readable):
						print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(line_num))
					found_list[1].append(item[0])
				elif ' ' in item[0] and item[0].split(' ',1)[1].upper() == 'COUNTY':
					if item[0].split(' ',1)[0] in cnames:
						if(human_readable):
							print(str(item[1].upper()) +" "+ str(item[0].upper()) + ", line " + str(lineNum))
						found_list[1].append(item[0])
