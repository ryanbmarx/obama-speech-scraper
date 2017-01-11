#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from bs4 import BeautifulSoup
import html5lib
import urllib2
import csv
from datetime import datetime, date
import re

def cleanTime(time):
	"""
	Takes a string representing a time and removes the crud from it. Included in this cleanup is an attempt to
	rempove all spaces (including &NBSP;s ) then reinsert them around the AM and PM elements
	"""
	return time.replace('0xC3 0x82',"").replace("\t","").replace("\n","").replace("\r","").replace('END', "").replace(' ','').replace('P.M.', ' P.M. ').replace('A.M.', ' A.M. ')

def getRemarksPageContents(url):
	"""
	This gets the location, time and (eventually will) download the full text. Basically this function dives into each 
	individual page (versus the blog directory pages from which the other items are scraped).
	"""
	page = urllib2.urlopen(url)
	pagesoup = BeautifulSoup(page.read(), "html5lib")

	full_page_contents = pagesoup.find('div', {"id":'content-start'}).get_text()

	# Get the place. It usually is found inside this class to center the text, though sometimes is in a traditional dateline format
	try:
		place = pagesoup.find('p', {"class":'rtecenter'}).get_text()
	except Exception:
		place = "TK"

	# Get the time 
	"""
		There is no HTML-element-based way of finding the times, so we just need to search the paragraphs one by one
		until we find an A.M. or P.M. Then we need to clean up some of the crud with a helper function. Sometimes 
		there are two times ... one  at the beginning and one at the end. The second seems to always be accompanied
		by "END" so we will make that a base assumption
	"""
	time_start = "time_start not found"
	time_finish = "time_finish not found"
	try:
		temp = pagesoup.find('div', {"class":'field-item'})('p')

		# We'll assume any p with the substring AM/PM or the like 
		for p in temp:
			text_to_test = p.get_text().upper()
			search_obj = re.search('\d:\d\d\s\w.\w.|\d\d:\d\d\s\w.\w.', text_to_test)
			if search_obj != None:
				time_start = search_obj.group(0)
				# time_start = datetime.strptime(time_start, 'I:%M%p')
				break
		
		# The end time is preceded by "END"
		for p in reversed(temp):
			text_to_test = p.get_text().upper()
			if "END" in text_to_test:
				end_search_obj = re.search('\d:\d\d\s\w.\w.|\d\d:\d\d\s\w.\w.', text_to_test)
				if search_obj != None:
					time_finish = end_search_obj.group(0)
					break

	except Exception:
		print ("Ooops. Error in the fulltext portion of the time findin'")

	ret_val = {
		"place":place,
		"time_start":time_start,
		"time_finish":time_finish,
		"duration":getDuration(time_start,time_finish)
	}
	return ret_val

def convertToDatetime(time_str):
	# Sometimes the time strings are error messages or otherwise not compatible with strptime. 
	#  We'll use this function to do that conversion or return a detectable -1
	try:
		return datetime.strptime(time_str.replace('.',""), '%I:%M %p')
	except Exception:
		return -1

def getDuration(time1_str, time2_str):
	# If we have two datetimes, then we should calculate the duration.
	time1_dt = convertToDatetime(time1_str)
	time2_dt = convertToDatetime(time2_str)
	if (type(time1_dt) == datetime and type(time2_dt) == datetime):
		return time2_dt - time1_dt

def checkForSpeaker(headline, official):
	"""
	This function takes a string (in this case, a blog headline) and checks it for keywords. It 
	will be used to determine if a referenced speech/remarks included Barack, Michelle and/or Joe Biden
	"""

	# These are the search terms used for each official. If one of them is present, 
	# then we will assume he/she was speaking. This includes the weekly address (in english and spanish) which
	# are assumed to be the prez.
	keywords = {
		"vpotus":['vice president', 'joe biden'],
		"potus":['barack', 'barack obama', 'the president', 'president obama', 'weekly', 'SEMANAL'],
		"flotus":['Michelle Obama', 'first lady', 'flotus'],
		"jill":['Jill Biden']
	}

	# Go through the keywords and quit once there is a match. I've user upper() to avoid inconsistency in 
	#  the capitalization of "First Lady" or other such titles.
	for keyword in keywords[official]:
		if keyword.upper() in headline.upper():
			return "1"
	return "0"




#Base URL to the wh.gov remarks directory in the media room.
base_url = 'https://www.whitehouse.gov/briefing-room/speeches-and-remarks?term_node_tid_depth=31&page='

#First row of the CSV will be descriptions of each column. This List of Dicts will be written to CSV
output = [{
	"date":"Date remarks were given",
	"potus":"If remarks included Obama",
	"vpotus":"If remarks included Biden",
	"flotus":"If remarks included Michelle Obama",
	"jill_biden":"If remarks included Jill Biden",
	"link":"Link to remarks on wh.gov",
	"place":"Where were the remarks delivered",
	"time_start":"When the remarks began",
	"time_finish":"When the remarks finished",
	"duration":"how long was the speech",
	"text":"Link text/post headline"
}]


# CYCLE THROUGH ALL 471+ PAGES OF POSTS ON WH.GOV AND GRAB THE DESIRED ELEMENTS
for i in range(0,5):
	url = "{}{}".format(base_url, i)
	page = urllib2.urlopen(url)
	soup = BeautifulSoup(page.read(), "html5lib")
	print("Now pulling from {}".format(url))
	
	# Each blog post in the directory is contained in a "views-row" class
	remarks = soup.find_all('div',{"class":"views-row"})
	for remark in remarks:


		link = "https://www.whitehouse.gov{}".format(remark('a')[0]['href'])
		text = remark.find('h3',{"class":"field-content"})('a')[0].contents[0]
		date = remark.find('span',{"class":"field-content"}).contents[0]
		
		# This if statement will skip items in Spanish. They are duplicates, and we don't want to double count
		if ("DECLARACIONES" in text.upper() or "MENSAJE SEMANAL" in text.upper()):
			print (' not valid')
		else:
			# There are a few elements which must plucked from the actual remarks page. 
			# Those will be contained in this dict
			page_contents = getRemarksPageContents(link)

			# Scan the headline for keywords to determine who was speaking. Could be some or all 
			# of these people. 1 = (s)he spoke. Anything else means no.
			potus = checkForSpeaker(text, 'potus')
			vpotus = checkForSpeaker(text, 'vpotus')
			flotus = checkForSpeaker(text, 'flotus')
			jill_biden = checkForSpeaker(text, 'jill')

			# The temporary object which gets pushed into the output.
			temp = {
				"date":date.encode('utf-8'),
				"potus":potus,
				"vpotus":vpotus,
				"flotus":flotus,
				"jill_biden":jill_biden,
				"link":link.encode('utf-8'),
				"place":page_contents['place'].encode('utf-8'),
				"time_start":page_contents['time_start'].encode('utf-8'),
				"time_finish":page_contents['time_finish'].encode('utf-8'),
				"duration":page_contents['duration'],
				"text":text.encode('utf-8')
			}
			output.append(temp)
			print('valid')


# WRITE THE OUTPUT TO A CSV

csv.register_dialect(
    'mydialect',
    delimiter = ',',
    quotechar = '"',
    doublequote = True,
    skipinitialspace = True,
    lineterminator = '\r\n',
    quoting = csv.QUOTE_MINIMAL)

keys = output[0].keys()
try:
	
	with open('remarks.csv', 'wb') as output_file:
	    dict_writer = csv.DictWriter(output_file, keys)
	    dict_writer.writeheader()
	    dict_writer.writerows(output)
	# print(output)

except Exception, e:
	print (e)
		
