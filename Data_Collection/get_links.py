import re
from bs4 import BeautifulSoup
import requests
from bs4 import SoupStrainer


def extract_link(url):
	"""
	Creates a BeautifulSoup object from the link
	:param url: the link
	:return: a BeautifulSoup object equivalent of the url
	"""
	headers = {"Host": "www.zomato.com",
	       "User-Agent": "rawUa: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
	       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
	       "Accept-Language": "en-US,en;q=0.5",
	       "Accept-Encoding": "gzip, deflate, br",
	       "Referer": "https://www.zomato.com/",
	       "Connection": "keep-alive"}

	r = requests.get(url, headers=headers)
	if r.status_code == 404:
		return None
	page_source = r.text

	page_source = re.sub('<br>', '', page_source)
	page_source = re.sub('<br />', '', page_source)
	page_source = re.sub('<br/>', '', page_source)
	soup = BeautifulSoup(page_source, 'html.parser')

	return soup
	
#rest_links - Stores links of restaurants, go_to_links - stores links of restaurant chains to be scraped again for all outlets
rest_links = set()
go_to_links = set()

main_link = 'https://www.zomato.com/kolkata/restaurants?page='

#434 pages at the time of scraping data
for j in range(1,50):
	for i in range(1, 435):
		print('Page: {}'.format(i),'Round:',j)
		link = main_link + str(i)

		soup = extract_link(link)
		
		'''with open('Soup_7.txt','a') as f1:
			f1.write(str(i)+'>>>>>>>>>>>>>>>>>>PAGE NO')
			f1.write(soup.prettify())'''
		
		restaurant_cards = soup.find_all('div', class_=re.compile('card search-snippet-card'))
		chain_link = soup.find_all('a', class_=re.compile('ui col-l-16 search_chain_bottom_snippet'))
		g_link = soup.find_all('a', class_=re.compile('ui ta-right pt10 fontsize3 zred pb10 pr10'))
		
		for cll in chain_link:
			rest_links.add(cll.get('href'))
			#print(cll.get('href'))
		
		for cll in g_link:
			go_to_links.add(cll.get('href'))
			#print(cll.get('href'))
			
		
		for rc in restaurant_cards:
			mylink = rc.find('a', class_=re.compile('result-title hover_feedback zred bold ln24')).attrs['href']
			rest_links.add(mylink)
			#print(mylink)

for mylink in go_to_links:
	mylink = 'https://www.zomato.com'+mylink
	#print(mylink)
	soup = extract_link(mylink)
	restaurant_cards = soup.find_all('div', class_=re.compile('card search-snippet-card'))

	for rc in restaurant_cards:
		mylink1 = rc.find('a', class_=re.compile('result-title hover_feedback zred bold ln24')).attrs['href']
		rest_links.add(mylink1)


#writing to output file
with open('restaurant_links_kolkata_1.txt', "w") as f:
	for ul in rest_links:
		f.write(ul+'\n')

	
