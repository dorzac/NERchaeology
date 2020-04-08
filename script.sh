#!/bin/bash

#set up structures
if [[ -d "./ascii" ]]
then
	rm -r ./ascii
fi
if [[ -d "./output" ]]
then
	rm -r ./output
fi
mkdir ./ascii
mkdir ./output
chmod 777 ascii
chmod 777 output
echo "*** Finished preprocessing"

#Convert all pdfs to ascii text
for FILE in ./pdfs/*.pdf
do
	basename "$FILE"
	#f="$(basename -- $FILE)"
	f=$(basename "$FILE" .pdf)
	#pdftotext -layout pdfs/"$f" ./ascii/"${f%.pdf}.txt"
	pdftotext -layout pdfs/"$f.pdf" ./ascii/"$f.txt"
done

echo "In 4000 BC, I lost my 2019 manga collection. This was about 300 years ago, if I remember. Perhaps 65 AD." > ./ascii/check.txt
echo "*** Finished Conversions"

#Open docker container to hold stanford server on port 9000
#docker pull anwala/stanfordcorenlp
#docker run --rm -d -p 9000:9000 --name stanfordcorenlp anwala/stanfordcorenlp

#create the csv for output
touch out.csv

#Parse for smithsonian trinomials, dates
for FILE in ./ascii/*.txt
do
	basename "$FILE"
	#f="$(basename -- $FILE)"
	f=$(basename "$FILE" .txt)
	#python3 driver.py ascii/"$f" > ./output/"${f%.txt}.output"
	python3 driver.py ascii/"$f.txt" 'y' > ./output/"$f.output"
done
echo "*** Finished parsing"

#close container
#docker rm -f stanfordcorenlp

#Delete files with no useful data
find ./output -size 0 -print -delete > ./output/deleted.txt
find ./ascii -size 0 -print -delete > ./ascii/deleted.txt

#Set permissions so all users can access (hack to fix root creation)
find ./ascii/ -type f -exec chmod 777 {} \;
find ./output/ -type f -exec chmod 777 {} \;
echo "*** Finished setting permissions"
