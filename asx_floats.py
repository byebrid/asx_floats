"""This script does a few things:
    1) Gets lxml from ASX upcoming floats web page and parses that into a python set.
    2) Reads the floats that were added the last time the script was run (i.e.
       floats that were on ASX website yesterday) and parses them into a python set.
    3) Compares the currently upcoming floats with the previously upcoming floats.
    4) If any new floats have been added, the user will be alerted via applescript.
       (any floats that have been removed are ignored).
"""
import subprocess
import csv
import os
import requests
from bs4 import BeautifulSoup as BS

# Change path to that of script
os.chdir(os.path.dirname(__file__))

# Getting lxml from asx page on upcoming floats
asx_floats_url = requests.get('https://www.asx.com.au/prices/upcoming.htm').text
asx_floats_soup = BS(asx_floats_url, 'lxml')

# Gets table of info on upcoming floats
floats_table = asx_floats_soup.find_all('tr')[1:]

# Creates set of tuples of info on companies with upcoming floats
current_floats = set()
for row in floats_table:
    # Finds all cells in current row
    cells = row.find_all('td')
    cells = map(lambda cell: cell.string, cells)
    company, proposed_code, proposed_date = cells
    # Link to ASX profile of company
    website_link = 'https://www.asx.com.au' + row.find('a').get('href')
    current_floats.add((company, proposed_code, proposed_date, website_link))

# csv file containing list of upcoming floats
filename = "asx_floats.csv"

# Getting list of upcoming floats from csv file to see if any changes have occured
old_floats = set()
with open(filename, 'r', newline='') as csvfile:
    reader = csv.reader(csvfile, dialect='excel')
    for row in reader:
        old_floats.add(tuple(row))

# Comparing current and old floats to find any newly added floats
recently_added_floats = current_floats.difference(old_floats)

# If any new floats, add them to the csv file
if len(recently_added_floats) > 0:
    print("Found new floats:", recently_added_floats)
    # Writing to csv file for use next time script is executed
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='excel')
        for row in current_floats:
            writer.writerow(row)

    # Getting tickers/listing dates of newly added floats for use in applescript dialog
    new_floats = '\n'.join([f[1] + f' ({f[2]})' for f in recently_added_floats])

    applescript = f"""
    set theURL to "https://www.asx.com.au/prices/upcoming.htm"
    try
        display dialog "New floats: Ticker (Proposed listing date)\n{new_floats}.\nWould you like to check the ASX website for more info?" ¬
        with title "Found new upcoming floats on ASX" ¬
        buttons {{"No thanks.", "Sure!"}} default button "Sure!"
        if button returned of result is "Sure!" then
            open location theURL
        end if
    end try
    """

    subprocess.call("osascript -e '{}'".format(applescript), shell=True)
