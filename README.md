# SearchEngine-Website
Repo for the Search Engine project I'm working on, with its accompnaying website & spider

## Instructions for Usage of Spidey V1 - Files within finalized_Phase1
1. spideyTest.exe
Running the executable will, in the current directory, create a file called spider_results.txt. This file contains the results of the spidering process, as per the requirements given.

2. spidey.exe
Running the executable will, in the current directory, run the spidering process with the given parameters, and generate a new spideydb.json file. The format of the command is as follows:
spidey <seedUrl> <pageCount>
The resulting database can be read by spideyTest

The source code files have been built into these executables, and are the .py files in the src folder.

Note that the spidey.exe file will need to have stopwords.txt in the same directory as it in order to run, and that the spideyTest.exe file will need to have spideydb.json in the same directory as it, or will return an error message. This spider is Spidey V1, and has been rewritten.

## Future Improvements
Spidey
___
1. ~The spider may be swapped to use a tool like selenium to allow for javascript to be executed on the page, and for the spider to be able to access the full content of the page.~ **DONE**
2. ~Fixing SSL errors, which are currently ignored and unsafe~ **DONE**
3. ~Adding URL cannonicalization to the spider, to ensure that the same page is not crawled multiple times~ **DONE**
4. ~Handle redirects and other such errors with page hash comparison~ **DONE instead with switch to selenium**
5. Convert the spider into a flask app that can be run on a server
6. Dockerize & Setup the flask app for deployment as a backend with an API

The Site
___
1. We'll be finishing the initial site first