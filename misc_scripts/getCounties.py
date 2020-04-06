import re
import codecs

def main():
	cline = re.compile("\d\.\s+(\w+\s?\w*)\s*\.*\s*([A-Z]{2})")
	with codecs.open("counties.txt", 'r', encoding = 'utf-8', errors='ignore') as f:
		for line in f:
			counties = cline.findall(line)
			if counties is not None:
				for county in counties:
					print(county[0].strip() + "," + county[1])

main()
