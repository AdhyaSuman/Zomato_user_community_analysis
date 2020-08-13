import re
from bs4 import BeautifulSoup
import requests
from bs4 import SoupStrainer
import csv


def extract_link(url):
	"""
	Creates a BeautifulSoup object from the link
	:param url: the link
	:return: a BeautifulSoup object equivalent of the url
	"""
	headers = {"Host": "www.zomato.com",
	       "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
	       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
	       "Accept-Language": "en-US,en;q=0.5",
	       "Accept-Encoding": "gzip, deflate, br",
	       "Referer": "https://www.zomato.com/",
	       "Connection": "keep-alive"}

	r = requests.get(url, headers=headers)
	print(r.status_code)
	if r.status_code == 404:
		return None
	page_source = r.text

	page_source = re.sub('<br>', '', page_source)
	page_source = re.sub('<br />', '', page_source)
	page_source = re.sub('<br/>', '', page_source)
	soup = BeautifulSoup(page_source, 'html.parser')

	return soup

spamWriter = csv.writer(open('restaurant_info.csv', 'a'))
spamWriter.writerow(['Link','Name','Restaurant ID','Rating','No. of Votes','Address','Cuisine','Cost for Two'])

ctr = 0
with open('restaurant_links_kolkata.txt', "r") as myfile:
	for link in myfile.readlines():
		link = link.strip()
		print(link)
		
		soup = extract_link(link)
		
		#LINK
		l = link	
		
		#Name
		name = soup.find('div', attrs={"class":"col-l-12"}).find('a').get('title')
		#print(name)		
		
		#Restaurant id
		rest_id_block = soup.find('div', attrs={"class":"left mr10 mb10"})
		rest_id = rest_id_block.find('div',attrs={"aria-label":"Add to bookmark"}).get('data-entity-id')
		#print(rest_id)
		
		#Rating
		rating_block = soup.find('div', attrs={"class":re.compile("^rating_hover_popup")})	
		rating = 'NEW'
		if rating_block is not None:
			rating = rating_block.text.strip()
			if(len(rating)>3):
				rating = rating[0:3]
		#print("Rating = "+rating)
		
		#No. of Votes
		voting_block=soup.find('span',attrs={"itemprop":"ratingCount"})
		voting= '0'
		if voting_block is not None:
			print('voting_block.text : ',voting_block.text)
			voting = voting_block.text.strip()

		#Address
		address_block = soup.find('div', attrs={"class":"borderless res-main-address"})
		address = ''
		if address_block is not None:
			address = address_block.text.strip()
		#print(address)
		
		#Cuisine
		cuisine_block = soup.find('div', attrs={"class":"res-info-cuisines"})
		cuisine = ''
		if cuisine_block is not None:
			cuisine = cuisine_block.text
		#print (cuisine)
		
		#Cost For Two
		cost_for_two_block = soup.find('div', attrs={"class":"res-info-detail"})
		cost_for_two = '-'
		
		if cost_for_two_block is not None and cost_for_two_block.text.find('Cash') == -1: 
			average_cost = cost_for_two_block.text.strip().split('\n')[2:]
			avg_cost = ''.join(average_cost)
			if avg_cost[19] is 'f':
				cost_for_two = avg_cost[14:19]
			else: 
				cost_for_two = avg_cost[14:20]
		#print(cost_for_two)
		
		ctr = ctr+1
		print(ctr)
		
		#Write to csv file
		spamWriter = csv.writer(open('restaurant_info.csv', 'a'))
		spamWriter.writerow([l,name,rest_id,rating,voting,address,cuisine,cost_for_two])

