#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from bs4 import BeautifulSoup
import html5lib
import urllib2
import csv
from datetime import datetime, date
import re


url = "https://www.whitehouse.gov/the-press-office/2016/11/17/remarks-president-obama-and-chancellor-merkel-germany-joint-press"


"""
This gets the location, time and (eventually will) download the full text. Basically this function dives into each 
individual page (versus the blog directory pages from which the other items are scraped).
"""
page = urllib2.urlopen(url)
pagesoup = BeautifulSoup(page.read(), "html5lib")

full_page_contents = pagesoup.find('div', {"id":'content-start'}).get_text()

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
	print ("Ooops. Error in the fulltext portion")

print('time start: ', time_start)
print('time finish: ', time_finish)