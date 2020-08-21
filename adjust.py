import os
import sys
import csv

def op():
	with open("nlp.csv", newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	for e in data:
		if e[0] == 'key':
			continue
		if not e[2]:
			print("Adjusting",e[3])
			e[5] = e[4]
			e[4] = ''
			e[6] = e[7]
			e[7] = ''
		for i in range(4,8):
			if e[i]:
				if int(e[i]) <= 0:
					e[i] = str(abs(int(e[i]))) + " BC"
				else:
					e[i] = str(abs(int(e[i]))) + " AD"
	f = open("nlp-out.csv", "w")
	for e in data:
		for i in range(len(e)):
			if i == len(e) - 1:
				f.write(str(e[i]))
			else:
				f.write(str(e[i])+",")
		f.write("\n")
	f.close()

def main():
	op()
main()
