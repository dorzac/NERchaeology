import re
import sys
import codecs
from sutime import SUTime

# 41WM1234
asciiFile = str(sys.argv[1])
trinomials = re.compile("41[a-zA-Z]{2}[0-9]{1,4}")
lineNum = 0
with codecs.open(asciiFile, 'r', encoding = 'utf-8', errors='ignore') as f:
	for line in f:
		#result = trinomials.search(line)
		result = trinomials.findall(line)
		if result is not None:
				for item in result:
					print("Site " + str(item) + ", line " + str(lineNum))
		print(SUTime.parse(line, reference_date=''))
		lineNum+=1


