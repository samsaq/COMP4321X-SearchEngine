# SearchEngine-Website
Repo for the Search Engine project I'm working on, with its accompnaying website & spider

## Instructions for Testing of Both site and spider together
1. Get the Files
2. Install the requirements - Website
You can do this by installing npm and running npm install in the root of the website (sweatysvelting)
3. Install the requirements - Spider
You can do this by installing python and pip, and then doing a pip install <Pckage Name> (without the <>) for each of the packages imported within the spidey.py file
4. Run the spider
Make sure the stopwords file is where it is supposed to be (next to the spidey.py file) and then run the spidey.py file with python - do a python spidey.py in the directory where the spidey.py file is located, which should boot the server up and start the spider
5. Run the website
Run the website by doing a npm run dev in the root of the website (sweatysvelting) and then go to localhost:5173 in your browser to see the website (or whatever port it tells you to)
6. Test away! (The history function does not currently work, but everything else should do)

Side note: If you want to make the spider crawl, you'll need run the script in VSC with its run python file command (top right of screen with the correct file selected) with the folder searchengine-website as the base for the environment, and with debug and debugrefreshdata set to true at the top of the file. You can then set the seedUrl and targetVisited at the bottom of the file in the debug execution.
You will need to set those booleans back once you've done the scrape as well, and shouldn't keep the server running when running the code in VSC.

## Project Explanation: Abridged

Overall Design: 
The system overall uses space-vector methods to use selenium webdriver (why the browser pops up, its slow to fully load JS in the same way as a user would via chrome to make sure all the page content loads - I wanted the better data as I figured not many database rewrites would occur) to scrape the data of the pages encountered into an sqlite3 database managed with sqlalchemy. This python code is part of a flask backend (hence the use of flask_sqalchemy to make sqlalchemy compatible) that can be dockerized in future in a linux vm or the like for cloud deployment (which was something I aimed to do but was unable as of yet). The front end of the site uses a website written with sveltekit, using typescript, skeletonUI, and tsparticles for the type checking, base UI elements, and particle animation respectively. The site is able to be hosted onto vercel as is, provided the urls used within are redirected to wherever the backend is deployed.

As for the structure of the database and design decisions invovled, I opted to use as many smaller tables such as for vectors, terms, bigrams, trigams, and indexes as I could so that I could take advantage of sql joins to keep execution quick (ish). I decided to opt for slower scrape times when
the choice was there - so I precalculate vectors and other such metadata so that searches are quicker,
at a tradeoff for scrape speed. I had overcomplicated my favoring and weighting systems at first, but
had to untangle them so as to get everything actually working with any degree of speed (it used to take almost an hour to scrape, which was horrendous) - as such I use simple tf-idf for vectors, and do weigthing by multiplying vectors into a composite with the weight vector function to weight towards titles in favor of content. Beyond that, I also simply check for phrase match within the query vs documents to be checked against, and apply modifers to scores as such, instead of opting for some system of combining vectors, remaking them, etc - which might've provided more accuracy.

Installation procedures are detailed above, so I won't cover them again here.

Unique features would be mostly the website and use of selenium for webdriving - the website was a core focus for me that took up almost half the project time as I had little to no experience with web development beforehand, and I wanted the UI to look appealing and tie into the meaning and purpose of the site (eg: the search page is about connections, and has various vectors flowing dynamically in the background, as an imagining of what the backend is doing to put togehter your search result). It is also why I focused so much on nice aniamtions and smooth movement within the pages themselves, as well as defining a specific color scheme and font to use throughout the site. The use of selenium was also a unique feature, as it allowed me to wait for JS to load fully on the sites I scraped, for better data (though I admit that the sites we were to scrape were kept simple, and likely did not need such heavy measures as the sites we were given in phase 1).

Testing was done with traditional methods for the most part - I wrote dummy JSON files for the input and output of various functions and tested on a per function level as I worked my way through the project, finalizing in end to end tests with the whole site and backend deployed on the local machine. I did have plans to use playwright and vitetest to write out formalized end to end and unit tests, as well as use pytest for testing of view functions within flask, but that ultimately ended up being more effort than it was worth, and I opted for simpler testing methods instead.