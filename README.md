# COMP4321X-SearchEngine
Repo for classwork in COMP4321X, working on the class's search engine project

## Instructions for Usage - Files within finalized_Phase1
1. spideyTest.exe
Running the executable will, in the current directory, create a file called spider_results.txt. This file contains the results of the spidering process, as per the requirements given.

2. spidey.exe
Running the executable will, in the current directory, run the spidering process with the given parameters, and generate a new spideydb.json file. The format of the command is as follows:
spidey <seedUrl> <pageCount>
The resulting database can be read by spideyTest

The source code files have been built into these executables, and are the .py files in the src folder.

Note that the spidey.exe file will need to have stopwords.txt in the same directory as it in order to run, and that the spideyTest.exe file will need to have spideydb.json in the same directory as it, or will return an error message.

## Possible Improvements
1. The spider may be swapped to use a tool like selenium to allow for javascript to be executed on the page, and for the spider to be able to access the full content of the page.
2. ~Fixing SSL errors, which are currently ignored and unsafe~ **DONE**
3. ~Adding URL cannonicalization to the spider, to ensure that the same page is not crawled multiple times~ **DONE**
4. Handle redirects and other such errors with page hash comparison
5. More to come
