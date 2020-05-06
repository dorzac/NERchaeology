# NERchaeology
<b>Dependencies:</b>  python3.7, nltk, abiword

Running script.sh should handle everything. Make sure it has relevant permissions, as it needs to execute and write. 


## /** Background info **/

Current configuration is organized to convert pdfs to plaintext if there 
is already an /ascii directory present to save time, but this will likely 
be modified later to check explicitly for pdfs that haven't been 
converted. I was originally converting everything using the \*NIX utility
`pdftotext`, but I found that couldn't handle pdfs with multiple columns.
I found that the program `abiword` handles this nicely, albeit at the cost
of the plaintext file's readability to an extent. However, this doesn't
interrupt the parsing. 

I was using a Docker container that interfaced against Stanford's Core
NLP suite, but I found that it was far too slow and doing too much for
what was necessary, so I rewrote the useful tools myself. This is when
the driver script is called (it is important that it is called with 
Python 3.7 or later, due to library issues).

The driver script grabs all the periodo data it thinks will be useful for
the given file, then searches line by line for trinomials. When it finds
a trinomial, it tries to pick out which nearby period terms are relevant
in association with it. After parsing the whole file, it will write the
relevant data found to `out.csv`, and then dump a lot of human readable
data into an /output directory. 

I had high hopes to do a lot of my tokenization purely in regular
expressions, but I started coming up against cases in which the pdf to 
text conversion hurt the grammatical formatting on a lot of phrases, which
confused my regex. This is why I'm using Python's nltk library, as it 
handles the job excellently. The drawback is speed-- it slows the program
down a hundredfold, so it might be prudent to return to the regex solution
once everything else is good to go.


## /** Misc **/

The /vocabularies directory currently holds all useful csvs to be handled. All periodo csvs should begin with `periodo` in their filename to be considered. 

The /misc_scripts directory contains various programs that were used in preprocessing to manage and manipulate data that were useful for preparing information but are not actively needed.
