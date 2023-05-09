import os, sqlite3

# contains the code to read the database from spidey.py
# function to print scraping results to a .txt file called spider_results.txt 
# the form of the output is as follows:
# Page title
# URL
# Last modification date, size of page
# Keyword1 freq1; Keyword2 freq2; Keyword3 freq3; ... ...
# Child Link1
# Child Link2 ... ...
# ——————————————————————————————
# next page
# Note: the first 10 child links are those printed
# and top 10 most common keywords and their frequencies are printed in descending order

def outputDatabase():
    conn = sqlite3.connect('spidey.sqlite')
    cur = conn.cursor()

    outputTarget = 'spider_results.txt'
    if os.path.exists(outputTarget):
        os.remove(outputTarget)

    # Get all pages from the database
    cur.execute('SELECT * FROM Page')
    pages = cur.fetchall()

    # initialize the pageOutput string
    pageOutput = ''

    # Loop through all pages and print their information to the output file
    for page in pages:
        # Print the page title, URL, and last modified date and size
        pageOutput += f'{page[2]}\n{page[1]}\n{page[5]}, {page[6]} bytes\n'

        # Get the top 10 most common keywords for this page and their frequencies
        cur.execute('''
            SELECT Term.term, TermFrequency.frequency
            FROM TermFrequency JOIN Term ON TermFrequency.term_id = Term.term_id
            WHERE page_id = ?
            ORDER BY frequency DESC
            LIMIT 10
        ''', (page[0],))
        keywords = cur.fetchall()

        # Append the keywords and their frequencies
        keyword_str = '; '.join([f'{kw[0]} {kw[1]}' for kw in keywords])
        pageOutput += f'{keyword_str}\n'

        # Get the first 10 child links for this page
        cur.execute('SELECT child_url FROM ChildLink WHERE page_id = ? LIMIT 10', (page[0],))
        links = cur.fetchall()

        # Append the child links
        link_str = '\n'.join([link[0] for link in links])
        pageOutput += f'{link_str}\n'

        # Append the separator
        pageOutput += '——————————————————————————————\n'

    # make sure the output is in utf-8 encodable
    try:
        pageOutput.encode('utf-8')
    except UnicodeEncodeError:
        # Replace unencodable characters with "?"
        pageOutput = pageOutput.encode('utf-8', 'replace').decode('utf-8')

    # Write the pageOutput string to the output file
    with open(outputTarget, 'w', encoding='utf-8') as f:
        f.write(pageOutput)
    
    # Close the database connection
    cur.close()
    conn.close()

def main(): # the file is only run directly for testing purposes after phase 1
    # output the database to spider_results.txt, if it exists (if not, print an error message)

    os.chdir('Spidey') # change the working directory to the Spidey folder for debugging in VSC

    if os.path.exists('spidey.sqlite'):
        outputDatabase()
    else:
        print("Database file does not exist. Please run spidey.exe first.")

if __name__ == '__main__':
    main()
