#!/bin/bash

echo "Create output folder of human readable data per file?"
read -p "Enter y/n: " -n 1 -r $REPLY
echo
hr=false
if [[ $REPLY =~ ^[Yy]$ ]]
then
	hr=true
fi


#set up structures
regen=true
if [[ -d "./ascii" ]]
then
	regen=false
	#rm -r ./ascii
	echo "Ascii files already present."
	echo "Do you want to regenerate? This may take some time."
	read -p "Enter y/n: " -n 1 -r $REPLY2
	echo
	if [[ $REPLY2 =~ "^[Yy]$" ]]
	then
		echo "Requested regen..."
		regen=true
		#rm -r ./ascii
	fi
	regen=false
	echo $regen
fi

if [[ $regen == "true" ]]
then
#Convert all pdfs to ascii text
	echo "Regenerating ascii"
	mkdir ./ascii
	chmod 777 ascii

	#for FILE in ./pdfs/*.pdf ./pdfs/**/*.pdf;
	#for FILE in $(find ./pdfs/ -name '*.pdf');
	for FILE in ./pdfs/*.pdf
	do
		basename "$FILE"
		f=$(basename "$FILE" .pdf)
		#abiword --to=text pdfs/"$f.pdf" -o ./ascii/"$f.txt"
		abiword --to=text "$FILE" -o ./ascii/"$f.txt"

	done
echo "*** Finished Conversions"
fi

if [[ -d "./output" ]]
then
	rm -r ./output
fi
if [[ hr ]]
then
	mkdir ./output
	chmod 777 output
fi

echo "*** Finished preprocessing"


#Open docker container to hold stanford server on port 9000
#docker pull anwala/stanfordcorenlp
#docker run --rm -d -p 9000:9000 --name stanfordcorenlp anwala/stanfordcorenlp

#create the csv for output
if [[ -f "out.csv" ]]
then
	rm out.csv
fi
touch out.csv

#Parse for smithsonian trinomials, dates
#for FILE in $(find ./ascii -name '*.txt');
for FILE in ./ascii/*.txt
do
	basename "$FILE"
	#f="$(basename -- $FILE)"
	f=$(basename "$FILE" .txt)
	if [[ hr ]]
	then
		python3.7 refactor.py ascii/"$f.txt" "$REPLY" > ./output/"$f.output"
	else
		python3.7 refactor.py ascii/"$f.txt" "$REPLY"
	fi
done
echo "*** Finished parsing"

#python3 csv_cleanup.py out.csv temp.csv
#mv temp.csv out.csv
#sort out.csv -o out.csv
sed -i '1s/^/trinomial,dcterms:coverage_temporal,artifact,xsd:gDate_earliestStart,xsd:gDate_latestStart,xsd:gDate_earliestEnd,xsd:gDate_latestEnd,skos:CloseMatch,count,significance,lat,long,source_name\n/' out.csv

#close container
#docker rm -f stanfordcorenlp

#Delete files with no useful data
#Set permissions so all users can access (hack to fix root creation)
if [[ -d "./output" ]]
then
	touch ./output/deleted.txt
	find ./output -size 0 -print -delete > ./output/deleted.txt
	find ./output/ -type f -exec chmod 777 {} \;
fi
touch ./ascii/deleted.txt
find ./ascii -size 0 -print -delete > ./ascii/deleted.txt
find ./ascii/ -type f -exec chmod 777 {} \;

echo "*** Finished setting permissions"
