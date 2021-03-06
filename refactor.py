"""
Last updated 21 Aug 2020.
Code written by Zach Dorf.
Contact at dorzac0@utexas.edu.
"""

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

#Constants
TRINOMIAL_REGEX = re.compile("41[a-zA-Z]{2}[0-9]{1,4}")
bp_dates = re.compile("\d+(\s?b\.?[p,c]\.?)?\s?(.|to|and)?\s?\d+\s?(b\.?[p,c]\.?)")
pub_date = re.compile("((19|20)[0-9]{2})")		
cents = re.compile("(((beginning|middle|end|early|mid|late|[0-9a-z]*(st|[^a]nd|rd|th)" +
		"\s)[a-z ]*)?(([a-z]*(\-|\s))?[a-z]*)[0-9]{0,2}?(st|nd|rd|th)\s(century|millenia)" +
		"(\s(b\.?c\.?e\.?|c\.?e\.?|b\.?c\.?|a\.?d\.?))?)")
NEGATIVES = [" none ", " not ", " no "] 
SEARCH_SIZE = 3 # size 3 seems to be about optimal
PLACES = ['Austin', 'San Marcos', 'Jarrell', 'Round Rock', 'Uvalde']
HIST_EXCLUDE = ['Historian', 'Historically', 'Historic Places', 'Historic Overlay', 'Historical Commission']

#Globals
human_readable = False
input_file = ""
date = 0
relevant_trinomials = []
relevant_counties = []
periodo = []
artifacts = []
coords = {}


def harvest():
	"""
	@return relevant trinomials, a list of trinomials to consider in the output
	@return periodo, global matrix representation of the csv data
	Method called first, all preprocessing work.
	Reads in vocabulary files and stores them.
	"""
	global relevant_trinomials
	global relevant_counties
	global coords
	
	with open('vocabularies/coord.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	for line in data:
		coords[line[0]] = (line[1], line[2])

	#get relevant trinomials from csv
	relevant_trinomials = []
	with open('vocabularies/relevantTrinomials.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	for sublist in data:
		if sublist[0] != '':
			relevant_trinomials.append(sublist[0])

	relevant_trinomials = []
	with open('vocabularies/relevantCounties.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	for sublist in data:
		if sublist[1] != '':
			relevant_counties.append(sublist[1])

	#get periodo vocabs from all periodo csvs
	periodo = []
	periodo.extend([[] for col in range(12)])
	for filename in glob.glob('vocabularies/periodo*'):
		if filename == 'vocabularies/periodo-non-phases.csv':
			if date < 1983:
				continue
		if filename == 'vocabularies/periodo-phases.csv':
			if date >= 1983:
				continue
		with open(filename, newline='') as f:
			reader = csv.reader(f)
			data = list(reader)

			if filename == 'vocabularies/periodo-phases.csv':
				for row in range(1, len(data)):
					if data[row][1] is not '':
						data[row][1] = data[row][1].split('Phase',1)[0]

			#Transpose columns and rows of the CSV, ignoring labels
			for row in range(1, len(data)):
				for column in range(len(data[row])):
					#Fix the 'Austin city vs Austin Period' bug
					if data[row][1] in PLACES:
						temp = data[row][1]
						data[row][1] += ' Phase' 
						periodo[column].append(data[row][column])
						data[row][1] = temp
						data[row][1] += ' Period' 
						periodo[column].append(data[row][column])
					else:
						periodo[column].append(data[row][column])

	global artifacts
	artifacts.extend([[] for col in range(15)])
	with open('vocabularies/dinaa.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)

		#Transpose columns and rows of the CSV, ignoring labels
		for row in range(1, len(data)):
			for column in range(len(data[row])):
				artifacts[column].append(data[row][column])
				wordsplit = data[row][0].split()
				for word in wordsplit:
					if word == wordsplit[0]:
						continue
					if word == 'Projectile':
						break
					wordsplit[0] += ' ' + word
				ARTIFACT_SUBS = [" Point", " Dart", " Projectile"]
				#ARTIFACT_SUBS = [" Projectile Point"]
				if wordsplit and 'Projectile' in wordsplit:
					for term in ARTIFACT_SUBS:
						temp = data[row][0]
						data[row][0] = wordsplit[0] + term
						artifacts[column].append(data[row][column])
						data[row][0] = temp

	# Fixes '123 BC' terms
	for i, v in enumerate(artifacts[2]):
		if v:
			ugh = re.compile("(\d+)\s+([A-Za-z]+)")
			vals = ugh.findall(v)
			v = vals[0][0]
			if vals[0][1] == 'BCE':
				artifacts[2][i] = -1 * int(v)
				#artifacts[2][i] = int(v) + 1949
			if vals[0][1] == 'CE':
				artifacts[2][i] = int(v)
				#artifacts[2][i] = 1950 - int(v)

	for i, v in enumerate(artifacts[3]):
		if v:
			ugh = re.compile("(\d+)\s+([A-Za-z]+)")
			vals = ugh.findall(v)
			v = vals[0][0]
			if vals[0][1] == 'BCE':
				artifacts[3][i] = -1 * int(v)
				#artifacts[3][i] = int(v) + 1949
			if vals[0][1] == 'CE':
				artifacts[3][i] = int(v)
				#artifacts[3][i] = 1950 - int(v)

	# Sort terms alphabetically
	periodo[0], periodo[1], periodo[4], periodo[5], periodo[8], periodo[10], periodo[11] = \
		(list(t) for t in zip(*sorted( \
		zip(periodo[0], periodo[1], periodo[4], periodo[5], periodo[8], \
		periodo[10], periodo[11]), \
		key=lambda l1:l1[1])))

	# Sort terms by descending string len
	# TODO: This only sorts 7 columns in parallel. Write
	# custom sort to clean this up
	periodo[0], periodo[1], periodo[4], periodo[5], periodo[8], \
		periodo[10], periodo[11] = \
		(list(t) for t in zip(*sorted( \
		zip(periodo[0], periodo[1], periodo[4], periodo[5], periodo[8], \
		periodo[10], periodo[11]), \
		key=lambda l1:len(l1[1]), reverse=True)))


	return relevant_trinomials, periodo


def get_multi_terms(terms):
	"""
	@param terms is a list of terms to find multiple instances of in the periodo data.
	@return multi_terms a list of terms with multiple isntances in periodo data.
	This method populates the multi_terms global list, which is hugely important to 
	pinpointing which date range to use based on a document's publication year.
	"""

	multi_terms = []
	freqs = {}
	for term in terms:
		if term in freqs:
			freqs[term] += 1
		else:
			freqs[term] = 1
	for term in freqs:
		if freqs[term] > 1:
			multi_terms.append(term)
	return multi_terms


def find_terms(line, line_num, found_list):
	"""
	@param line is the string of text which to parse
	@param line_num is the line number, used for output and checking
		   relationship between term location and site location
	@param found_list is a list of lists with entries of the form
		   [term, line_num] (must remain mutable)
	Checks a line of text against the defined vocabularies.
	Grabs everything relevant, nondiscretely.
	"""

	# Reduce chance of false positives
	for e in HIST_EXCLUDE:
		if e.casefold() in line.casefold():
			line = line.casefold().replace(e.casefold(), '')

	for term in periodo[1]:
		if term.casefold() in line:
			for negator in NEGATIVES:
				if negator.casefold() in line:
					return
			print("FOUND",term)
			print("$$",line)
			line = line.replace(term.casefold(), '')
			found_list.append([term, line_num])


def find_artifacts(line, line_num, found_list):
	"""
	@param line is the string of text which to parse
	@param line_num is the line number, used for output and checking
		   relationship between term location and site location
	@param found_list is a list of lists with entries of the form
		   [term, line_num] (must remain mutable)
	Checks a line of text against the defined vocabularies.
	Grabs everything relevant, nondiscretely.
	"""

	for term in artifacts[0]:
		if not term.casefold():
			continue
		if term.casefold() in line:
			print("FOUND",term)
			print("&&",line)
			line = line.replace(term.casefold(), '')
			found_list.append(term)


def find_times(line, line_num, found_list):
	"""
	@param line is the string of text which to parse
	@param line_num is the line number, used for output and checking
		   relationship between date location and site location
	@param found_list is a list of lists with entries of the form
		   [term, line_num] (must remain mutable)
	Checks a line of text against some regex.
	Grabs everything relevant, nondiscretely.
	"""

	#Look for BP dates
	bp_check = bp_dates.findall(line)
	if bp_check is not None:
			for item in bp_check:
				found_list.append(item[0])

	#Look for centuries
	century_check = cents.findall(line)
	if century_check is not None:
			for item in century_check:
				found_list.append(item[0])


def parse_content(content):
	"""
	@param content is the content of the document to parse.
	@return records, a set of record data structs representing site/term
			pairings.
	Heavy lifting method. Checks each line for trinomials, and then looks for
	nearby terms that might be related. Builds record datastruct along the way
	to store data for each site/term pairing.
	"""

	freqs = {}
	records = set()
	for line_num in range(len(content)):
		tris_in_line = TRINOMIAL_REGEX.findall(content[line_num])
		if tris_in_line is None:
			continue
		for trinomial in tris_in_line:
			if trinomial[2:4] in relevant_counties:
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
					elif r.artifacts:
						r.period_term = ""
						records.add(r)

				#Otherwise, grab everything useful
				else:
					for pair in possible_pairs:
						tmp = Record( \
							site_name = r.site_name, \
							site_name_line = line_num, \
							period_term = pair[0], \
							artifacts = r.artifacts, \
							dates = r.dates)
						records.add(tmp)

				r.site_name_line = line_num

	old = records
	records = split_artifacts(records)
	implement_freqs(freqs, records)
	return records


def split_artifacts(records):
	"""
	@param records is a set of records.
	@return the modified version of this set.
	Actually a method more for saving programmer time than
	efficiency, goes through and makes a separate record for
	each artifact associated with a site, for printing purposes.
	"""
	
	to_add = []
	to_remove = []
	for r in records:
		if r.artifacts:
			for a in r.artifacts:
				tmp = Record( \
					site_name = r.site_name, \
					site_name_line = r.site_name_line, \
					period_term = "", \
					artifacts = r.artifacts, \
					artifact = a, \
					dates = r.dates)
				to_add.append(tmp)

				if r.period_term:
					tmp = Record( \
						site_name = r.site_name, \
						site_name_line = r.site_name_line, \
						period_term = r.period_term, \
						artifacts = r.artifacts, \
						artifact = "", \
						dates = r.dates)
					to_add.append(tmp)
		else:
			tmp = Record( \
				site_name = r.site_name, \
				site_name_line = r.site_name_line, \
				period_term = r.period_term, \
				artifacts = r.artifacts, \
				artifact = "", \
				dates = r.dates)
			to_add.append(tmp)

	records = set(to_add)
	return records


def get_date(content):
	"""
	@param content is the text of the document.
	Checks the first 20 lines of text, as well as the document name,
	to try and guess what the date the document was published in.
	If nothing can be found, just return the current year.
	"""

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
		record.count = freqs[record.site_name]


def display_hr(records):
	"""
	@param records is an array of record objects.
	Prints data to console
	"""
	if not len(records):
		return
	print("======"+str(len(records))+" Records Stored======")
	for record in records:
		print("SITE:", record.site_name, "line", record.site_name_line)
		print("PERIOD:", record.period_term)
		if record.dates:
			print("EXPLICIT dates:", record.dates)
		if record.artifacts:
			print("Artifact List:", record.artifacts)
			print("Key Artifact:", record.artifact)
		print("\n")


def get_possible_pairs(sentences, rec):
	"""
	@param sentences is an array of sentences to scan for terms
	@param rec is a record object for a single site
	@return an array of pairings between site and term
	"""
	possible_pairs = []
	found_times = []
	found_art = []
	for sen_index in range(len(sentences)):
		if rec.site_name in sentences[sen_index]:
			rec.site_name_line = sen_index

		find_terms(
				sentences[sen_index].casefold(),
				sen_index, possible_pairs)

		find_times(sentences[sen_index].casefold(), sen_index, found_times)

		find_artifacts(sentences[sen_index].casefold(), sen_index, found_art)

	rec.dates = found_times
	rec.artifacts = found_art
	return possible_pairs


def get_search_space(content, rec):
	"""
	@param content is a list of lines representing the document
	@param rec is the record with the trinomial the search space 
	is being built around.
	@return a tuple of the form (list of sentences, number of trinomials in
			those sentences.
	Loops over lines surrounding the trinomial in question and appends those
	lines to a string, ignoring lines that are a line-break away from the
	trinomial (i.e., in a different paragraph.) After developing the search
	space, it is tokenized into sentences.
	"""
	search_space = ''
	key_line = ''
	key_line_num = -1
	found = False
	
	for line in range(rec.site_name_line - SEARCH_SIZE, 
		rec.site_name_line + SEARCH_SIZE + 1):
		if line >= 0 and line < len(content):
			search_space += content[line]
			if rec.site_name in content[line] and not found:
				key_line = content[line]
				key_line_num = line
				found = True

	# If a trinomial is a heading, the search space should be the entire section
	if len(key_line.split()) < 4:
		if key_line_num + 1 < len(content) and \
				len(content[key_line_num + 1].split()) > 4:
			line = key_line_num + 1
			search_space = content[key_line_num]
			while len(content[line].split()) >= 4:# or \
					#content[line] != '\n':
				search_space += content[line]
				line += 1
				if line > key_line_num + 20:
					break
			search_space = re.sub(r"\s+", ' ', search_space)
			sentences = tokenize.sent_tokenize(search_space)
			local_trin_count = 1
			if not sentences:
				sentences.append(search_space)

			return sentences, local_trin_count
		
	search_space = re.sub(r"\s+", ' ', search_space)
	local_trin_count = len(set(TRINOMIAL_REGEX.findall(search_space)))
	sentences = tokenize.sent_tokenize(search_space)

	while rec.site_name.casefold() not in sentences[0].casefold():
		del sentences[0]

	temp = []
	for s in sentences:
		temp += s.split(',')
	sentences = temp

	#Parsing fails for image captioning, workaround
	if not sentences:
		sentences.append(search_space)

	return sentences, local_trin_count


def write_record(f, r):
	"""
	@param f, a file to write to.
	@param t, a Record dataclass.
	Writes the file in CSV form.
	"""
	f.write(r.site_name)
	f.write(",")
	if r.period_term:
		f.write(r.period_term)
		index = periodo[1].index(r.period_term)
		uri = periodo[0][index]
		f.write(",")
		late_start, early_end, early_start, late_end = fix_dates(r, index)
	else:
		f.write("," + r.artifact)
		late_start, early_end = ('', '')
		index = artifacts[0].index(r.artifact)
		early_start, late_end = (artifacts[2][index], artifacts[3][index])
		uri = ""


	f.write("," + str(early_start))
	f.write("," + str(late_start))
	f.write("," + str(early_end))
	f.write("," + str(late_end))
	f.write("," + str(uri))
	f.write("," + str(r.count))
	f.write("," + str(r.freq))
	try:
		f.write("," + str(coords[r.site_name][0]))
		f.write("," + str(coords[r.site_name][1]))
	except:
		f.write(",,")
	f.write(",\"" + input_file) #Write filename
	f.write("\"\n")


def fix_dates(r, index):
	"""
	@param r is the record object the date is being retrieved for
	@param index is the first index found for the period term in the set
	@return a tuple containing a min date and max date
	Basically, if a term shows up in the periodo data more than once, then
	choose the one with the most recent publication date before the date
	of publication from the source document.
	"""
	multi_terms = get_multi_terms(periodo[1])	
	only_two = False
	if r.period_term not in multi_terms:
		if only_two and not (periodo[10][index] and periodo[11][index]):
			return periodo[4][index], periodo[5][index], '', ''
		return periodo[4][index], periodo[5][index], \
			periodo[10][index], periodo[11][index]
	matches = []
	for i in range(len(periodo[1])):
		if periodo[1][i] == r.period_term:
			if not periodo[8][i]:
				periodo[8][i] = -1
			matches.append((i, int(periodo[8][i])))
	best_index = index;
	best_pubtime = 0;
	for e in matches:
		if e[1] > best_pubtime and e[1] <= date:
			best_index = e[0]
			best_pubtime = e[1]
	if only_two and not \
		(periodo[10][best_index] and periodo[11][best_index]):
		return periodo[4][best_index], periodo[5][best_index], '', ''
	return periodo[4][best_index], periodo[5][best_index], \
		periodo[10][best_index], periodo[11][best_index]
	

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
		for m in matches[:]:
			if not m[0]:
				matches.remove(m)
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


def handle_site_file(input_file):
	"""
	Site files are formatted as CSVs instead of plaintext, so they
	warrant special treatment. Each line in a SiteFile seems to cover
	a single site, so we want to restrict searching for terms to just
	that line. SiteFiles often have newlines embedded in them, which
	throws off the script, so this method removes newlines from within
	quoted text.
	@param input_file is the site file being handled.
	@return input_file, the reformatted siteFile
	"""

	if os.path.exists(input_file + ".rf"):
		os.remove(input_file + ".rf")
	with codecs.open(input_file, "rb", encoding="utf-8", errors="ignore") as ip, \
			codecs.open(input_file + ".rf", "wb", encoding="utf-8", errors="ignore") as op:
		w = csv.writer(op)
		for record in csv.reader(ip):
			w.writerow(tuple(s.replace("\n",'') for s in record))
	input_file = input_file + ".rf"
	return input_file
	

def main():

	global human_readable
	global relevant_trinomials
	global periodo
	global input_file
	global date
	global SEARCH_SIZE
	global site_file

	input_file = str(sys.argv[1])
	human_readable_input = str(sys.argv[2]).lower()
	if human_readable_input == 'y' or human_readable_input == 'yes':
		human_readable = True

	#Preprocessing to handle SiteFiles
	if input_file.endswith('.csv'):
		input_file = handle_site_file(input_file)
		SEARCH_SIZE = 0

	with codecs.open(input_file, "r", encoding="utf-8", errors="ignore") as f:
		content = f.readlines()

	input_file = os.path.basename(input_file)
	date = max(1981, get_date(content))

	l = []
	for line in content:
		find_times(line, 0, l)

	relevant_trinomials, periodo = harvest()
	records = parse_content(content)

	o = open("out.csv", "a+")
	for r in records:
		write_record(o, r)
	o.close()

	if human_readable:
		display_hr(records)

main()
