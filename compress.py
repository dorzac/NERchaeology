import os
import sys
import csv

def write(dic, val):
	f = open("out-" + str(val) + ".csv", "a+")
	for e in dic:
		if val == 2:
			f.write(e[0])
			if e[1][0] == '1':
				f.write(',' + e[1][1:] + ',')
			else:
				f.write(',,' + e[1][1:])
		else:
			f.write(e)
		info = dic[e]
		for v in info:
			if v != e:
				f.write(',' + str(v))
		f.write("\n")
	f.close()


def half_compress():

	dic = {}
	counts = {}
	with open('out.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	del data[0]
	for e in data:
		count = e[8]
		if e[1]:
			key = (e[0], '1'+e[1])
		else:
			key = (e[0], '2'+e[2])
		if key in counts:
			counts[key] += int(count)
		else:
			counts[key] = int(count)

		info = [e[3], e[4], e[5], e[6], e[7], counts[key], e[10], e[11]]
		dic[key] = info

	write(dic, 2)


def full_compress():

	dic = {}
	dates = {}
	with open('out-2.csv', newline='') as f:
		reader = csv.reader(f)
		data = list(reader)
	for e in data:
		key = e[0]
		if key in dates:
			if e[3]:
				dates[key][0].append(int(e[3]))
			if e[4]:
				dates[key][1].append(int(e[4]))
			if e[5]:
				dates[key][2].append(int(e[5]))
			if e[6]:
				dates[key][3].append(int(e[6]))
		else:
			l1 = []
			l2 = []
			l3 = []
			l4 = []
			if e[3]:
				l1.append(int(e[3]))
			if e[4]:
				l2.append(int(e[4]))
			if e[5]:
				l3.append(int(e[5]))
			if e[6]:
				l4.append(int(e[6]))
			dates[key] = [l1, l2, l3, l4]

		info = [e[0], '', '', '', '', e[9], e[10]]
		dic[key] = info
	
	for key in dic:
		if dates[key][0]:
			dic[key][1] = min(dates[key][0])
			print("1",dic[key][1])
		else:
			dic[key][1] = ''
		if dates[key][1]:
			dic[key][2] = min(dates[key][1])
		else:
			dic[key][2] = ''
		if dates[key][2]:
			dic[key][3] = max(dates[key][2])
		else:
			dic[key][3] = ''
		if dates[key][3]:
			dic[key][4] = max(dates[key][3])
		else:
			dic[key][4] = ''
		print("2",dic[key][1])


		if dic[key][1] != '':
			if dic[key][2]:
				if dic[key][1] == 0 or dic[key][1] == '0':
					print("Fix:",dic[key][1],dic[key][2])
				if dic[key][1] > dic[key][2]:
					dic[key][1] = ''
		if dic[key][3]:
			if dic[key][4]:
				if dic[key][4] < dic[key][3]:
					dic[key][4] = ''

	write(dic, 3)


def main():
	half_compress()
	full_compress()
main()
