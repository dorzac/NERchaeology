import sys
with open(sys.argv[1], 'r') as in_f, open(sys.argv[2], 'w') as out_f:
	seen = set()
	for line in in_f:
		if line in seen: continue
		seen.add(line)
		out_f.write(line)
