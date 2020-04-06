import re
import codecs
import csv

def extract_trinoms():
	site = re.compile("41[A-Z]{2}\d{1,3}")
	with codecs.open("relevantTrinomials.old", 'r', encoding = 'utf-8', errors='ignore') as f:
		for line in f:
			t = site.findall(line)
			if t is not None:
				for s in t:
					print(s)

def get_trinom_list():
	with open('relevantTrinomials.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	print(type(data[0]))
	relevantTrinomials = []
	for sublist in data:
		if sublist[0] is not '':
			relevantTrinomials.append(sublist[0])
	print(relevantTrinomials)
	print(len(relevantTrinomials))

def match_counties():
	store = []
	with open('allCounties.csv', newline='') as f:
		reader = csv.reader(f)
		allCounties = list(reader)
	with open('relevantCounties.old', newline='') as f:
		reader = csv.reader(f)
		usefulCounties = list(reader)	
	for county in usefulCounties:
		store.append(county[0])
	
	result = []
	for item in allCounties:
		if item[0] in store:
			result.append(item)
	for item in result:
		print(item[0] + "," + item[1])
	
match_counties()
