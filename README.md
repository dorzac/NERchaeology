**Dependencies: python3, Docker, Linux (at least a subsystem)

Running script.sh should handle everything. Make sure it has relevant permissions, as it needs to execute and write. 
script.sh must also be run as root, since opening and closing the docker container modifies system state. Therefore in terminal, run
```
chmod +x script.sh #gives the script executable permission
sudo ./script.sh #runs script as root
```


/** Background info **/
script.sh first reads in the files in the pdf directory, which ideally should be symbollically linked to the location where all files are stored (due to the difficulty of interfacing directly to the Windows fileshare on Linux, this is probably on a ssd or something.) The script will proceed to read OCR-ed PDFs and convert them into simple ASCII text files, which will be placed in the /temp_ascii directory with a .txt extension. This completes the preprocessing.

Now for the NER aspect.
The most helpful library here is going to be Stanford's NER program, but the entire library is so bulky and difficult to wrap that the simplest solution I could come up with is through docker. Stanford's CoreNLP package is launched in a docker container and laced to port 9000, and all requests are handled this way. By doing this, one avoids the local libraries and can simply use Python to web handling to interface directly.
The script's biggest job is calling the driver.py program on every file in the /temp_ascii directory and dumping output into the /temp_output directory. The driver program will read in the ascii file line by line, call Stanford's NER methods on it to look for relevant artifacts, and then also manually parse the line for other mandated vocabulary (Smithsonian trinomials, etc) usually with regular expressions but also by running against predefined vocabulary lists, located in the /vocabularies dir. 


/** Misc **/
The /misc_scripts directory contains various programs that were used in preprocessing to manage and manipulate data that were useful for preparing information but are not actively needed.
