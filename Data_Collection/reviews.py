import re
from bs4 import BeautifulSoup
import requests
from bs4 import SoupStrainer
from selenium import webdriver
from time import sleep, time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import networkx as nx
from datetime import datetime
from sys import argv
import csv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import os
import zipfile

PROXY = 'proxy_ip_address' # YOUR PROXY IP ADDRESS
port = '1234' # YOUR PORT NUMBER
user = 'User Name' # YOUR USER NAME
passw = 'User Password' # YOUR PASSWORD
manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""
background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY, port, user, passw)

css_sel = {'all_revs': '#selectors > a.item.default-section-title.everyone.empty',
           'load_more': '#reviews-container > div.notifications-content > div.res-reviews-container.res-reviews-area > div > div > div.mt0.ui.segment.res-page-load-more.zs-load-more > div.load-more.bold.ttupper.tac.cursor-pointer.fontsize2'}

def get_chromedriver(use_proxy=True, user_agent=None): #set use_proxy to False if you don't using a network with proxy
    #path = os.path.dirname(os.path.abspath(__file__))
    chrome_options = webdriver.ChromeOptions()
    if use_proxy:
        pluginfile = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        chrome_options.add_extension(pluginfile)
    if user_agent:
        chrome_options.add_argument('--user-agent=%s' % user_agent)
    prefs = {"profile.managed_default_content_settings.images": 2, "profile.default_content_settings.state.flash": 0}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(os.path.join('/usr/bin/', 'chromedriver'),chrome_options=chrome_options)
    return driver


class Restaurant:
    def __init__(self, link=None):
        self.link = link
        self.name = None
        self.entity_id = None
        self.cuisines = None
        self.review_count = None
        self.geo_loc = None
        self.rating = None
        self.number_of_ratings = None
        self.cost_for_two = None
        self.get_info()
        self.reviews = self.get_reviews()
        # self.get_reviews2()


    def __repr__(self):
        return '{} | {} | {} |'.format(self.name, self.entity_id, self.link)

    def __str__(self):
        return '{} | {} | {} | {} ratings | {} reviews | {} | {} | {} | \n'.format(self.name, self.entity_id, self.rating, self.number_of_ratings, self.review_count, self.geo_loc, self.link, self.cuisines)

    def get_reviews(self, start=0):
        """
        Get all the reviews of a restaurant
        :return: List of Review objects
        """
        filename = self.link.split('/')[-1]

        contents = check_file(filename, 1)

        if contents is None:
            start = time()
            driver = get_chromedriver(use_proxy=True)
            # driver = init_firefox()
            driver.get(self.link + r'/reviews')
            print('There are {} reviews'.format(self.review_count))
            # click on the button 'All reviews'
            sleep(2)

            try:
                el = driver.find_element_by_css_selector('#selectors > a.item.default-section-title.everyone.empty')
                webdriver.ActionChains(driver).move_to_element(el).click(el).perform()
            except NoSuchElementException:
                pass

            sleep(2)
            load_more = '#reviews-container > div.notifications-content > div.res-reviews-container.res-reviews-area > div > div > div.mt0.ui.segment.res-page-load-more.zs-load-more > div.load-more.bold.ttupper.tac.cursor-pointer.fontsize2'
            while element_present(driver, load_more):
                try:
                    el2 = driver.find_element_by_css_selector(load_more)
                    driver.execute_script("return arguments[0].scrollIntoView();", el2)
                    driver.execute_script("window.scrollBy(0, -275);")
                    sleep(0.5)
                    webdriver.ActionChains(driver).move_to_element(el2).click(el2).perform()
                    source = get_source(driver)
                    write_to_file(source, filename, 1)
                except (StaleElementReferenceException, NoSuchElementException):
                    break
            source = get_source(driver)
            write_to_file(source, filename, 1)  # 1 for Resto
            print('{} reviews are loaded in {} secs'.format(self.review_count, time() - start))

        else:
            print('Using cached page')
            source = contents

        soup = source_to_soup(source)
        review_blocks = soup.find_all('div', class_=re.compile('ui segments res-review-body'))

        # review_blocks = (soup.find_all('div', class_='ui segment clearfix  brtop '))
        if len(review_blocks) == 0 or self.review_count == 0:
            print('Error in parsing reviews...\n')
            return
        print('Loaded {} reviews'.format(len(review_blocks)))


        with open('reviews_csv_all.csv', 'a', encoding='utf-8') as f:
            spamwriter = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            #spamwriter.writerow(['Restaurant Name','Restaurant Id','User Name','User Id','User Link','User Rating','Review Time','Review Text'])

            reviews = []
            i = start
            for review in review_blocks:
                name_and_link = review.find('div', class_='header nowrap ui left')
                # print(name_and_link.contents)
                u_link = name_and_link.contents[1].attrs['href']
                u_entity_id = int(name_and_link.contents[1].attrs['data-entity_id'])
                u_name = name_and_link.contents[1].contents[0].strip()
                # print(u_name)
                rating_and_rev_text = review.find('div', text='Rated')

                r = Review()
                # r.user = User(u_link, u_entity_id)
                # if r.user.name is None:
                #     print('Invalid review, skipping')
                #     continue
                # r.user_link = u_link
                #
                r.restaurant = self
                r.time = review.find('time').attrs['datetime']
                r.rating = float(rating_and_rev_text.attrs['aria-label'].split()[-1])
                r.review_text = rating_and_rev_text.parent.contents[2].strip()
                reviews.append(r)
                #
                # print(f'{i + 1} {u_name}', end=' ')
                # # f.write('{} | {} | {} | {} | {} | {}\n'.format(self.name, self.entity_id, r.user.name, r.user.entity_id, r.rating, r.time))
                # # f.write('{} | {} | {} | {}\n'.format(r.user.name, r.user.entity_id, r.user.followers_count, r.user.reviews_count))
                spamwriter.writerow([self.name, self.entity_id,u_name, u_entity_id, u_link, r.rating, r.time, r.review_text])
                i += 1
        #print()
        return reviews


    def get_info(self):
        """
        Populates the name, cuisines, entity_id,....
        :return: list of cuisines (str)
        """

        soup = extract_link(self.link)

        if soup is None:
            return

        try:

            self.name = soup.find('div', attrs={"class":"col-l-12"}).find('a').get('title')
            print('Visiting ', self.name)

            self.entity_id = int(soup.find(id='resinfo-wtt').attrs['data-entity-id'])
            #print(self.entity_id)
            # review_count = soup.find('a', {'href': '{}/reviews'.format(self.link), 'class': 'item respageMenu-item '}).text
            # reviews_count = list(soup.find('div', class_='review-sorting text-tabs selectors ui secondary pointing menu mt0').children)
            try:
                rev_count_block = soup.find_all('a', {'data-sort': 'reviews-dd'})[0]
                self.review_count = int(rev_count_block.contents[1].text)
            except IndexError:
                rev_count = 0

            print('{} reviews'.format(self.review_count))

            cuisine_block = soup.find('div', class_='res-info-cuisines clearfix')
            list_of_cuisines = []
            for cuisine in cuisine_block.find_all('a', class_='zred'):
                list_of_cuisines.append(cuisine.text.strip())

            self.cuisines = ','.join(list_of_cuisines)
            #print(self.cuisines)

            self.rating = soup.find('div',attrs={"class":"rating_hover_popup res-rating pos-relative clearfix mb5"}).find('div').get('aria-label')
            #print(self.rating)

            # geo location
            try:

                loc_text = soup.find(id='res-map-canvas').next_sibling.next_sibling.text.strip()
                lat, long = loc_text[loc_text.find('{') + 1: loc_text.find('}')].split(',')
                lat = float(lat[lat.find(':') + 2:])
                long = float(long[long.find(':') + 2:])
                self.geo_loc = (lat, long)
                #print(self.geo_loc)
            except AttributeError:
                self.geo_loc = None  # restaurant's GPS location is not available

            number_of_ratings_block = soup.find('span', class_=re.compile('mt2 mb0 rating-votes-div rrw-votes grey-text fontsize5 ta-right'))
            self.number_of_ratings = int(number_of_ratings_block.find('span', {'itemprop': 'ratingCount'}).contents[0])
            #print(self.number_of_ratings)


        except:
            pass


class Review:
    def __init__(self):
        self.user = None
        self.user_link = None
        self.restaurant = None
        self.time = None
        self.rating = None
        self.review_text = None

    def __repr__(self):
        return '{} | Rating: {} | {} | '.format(self.restaurant.name, self.rating, self.time)

    def __str__(self):
        return '{} | {} | {} | {} | {} | {} | {} |\n '.format(self.restaurant.name, self.user.name, self.user_link,
                                                              self.user.entity_id, self.rating, self.time,
                                                              self.review_text)


def source_to_soup(page_source):
    """
    takes in page source, removes br tags and makes a Beautiful Soup object
    """
    page_source = re.sub('<br>', '', page_source)
    page_source = re.sub('<br/', '', page_source)
    page_source = re.sub('<br />', '', page_source)
    return BeautifulSoup(page_source, 'html.parser', parse_only=SoupStrainer('div'))


def extract_link(url):
    """
    Creates a BeautifulSoup object from the link
    :param url: the link
    :return: a BeautifulSoup object equivalent of the url
    """
    headers = {"Host": "www.zomato.com",
               "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0",
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "en-US,en;q=0.5",
               "Accept-Encoding": "gzip, deflate, br",
               "Referer": "https://www.zomato.com/",
               "Connection": "keep-alive"}

    if url.startswith('file'):
        with open(url.replace('file:\\\\', ''), encoding='utf-8') as fp:
            page_source = fp.read()

    else:
        r = requests.get(url, headers=headers)
        if r.status_code == 404:
            return None
        page_source = r.text

    page_source = re.sub('<br>', '', page_source)
    page_source = re.sub('<br />', '', page_source)
    page_source = re.sub('<br/>', '', page_source)
    soup = BeautifulSoup(page_source, 'html.parser')

    return soup


def init_firefox():
    firefox_profile = webdriver.FirefoxProfile()
    # firefox_profile.set_preference('permissions.default.stylesheet', 2)
    firefox_profile.set_preference('permissions.default.image', 2)
    firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
    

    return webdriver.Firefox(firefox_profile=firefox_profile)


def element_present(driver, sel):
    try:
        driver.find_element_by_css_selector(sel)
        return True
    except (NoSuchElementException, StaleElementReferenceException):
        return False


def get_source(driver):
    """
    Returns the page source - waits until it detects <html> tag
    :param driver:
    :return: the page source
    """
    sleep(5)
    while True:
        source = driver.page_source
        if '<html' in source:
            return source
        else:
            print('Waiting for page to load')
            sleep(5)


def write_to_file(source, filename, type):
    """
    Writes the source to a file.
    Type = 1 for Restaurant review, 2 for user follower,
    3 for user review
    """
    path = '/home/suman/labSmn/project/data'
    if type == 1:
        path += '/Restaurants/' + filename
    elif type == 2:
        path += '/Users/Followers/' + filename
    elif type == 3:
        path += '/Users/Reviews/' + filename

    with open(path, 'w') as f:
        f.write(source)

    print('Source saved for {}'.format(filename))


def check_file(filename, type):
    """
    Checks if a webpage has already been cached in the disk, if so, return the contents
    otherwise return None
    type 1 for restaurant review, 2 for user follower, 3 for user reviews
    """
    path = '/home/suman/labSmn/project/data'
    if type == 1:
        path += '/Restaurants/' + filename
    elif type == 2:
        path += '/Users/Followers/' + filename
    elif type == 3:
        path += '/Users/Reviews/' + filename

    contents = None
    try:
        with open(path, 'r') as f:
            contents = f.read()
    except FileNotFoundError:
        print('File not in cache, loading the page')
    return contents


def test_review():

    urls = []
    with open('restaurant_info_kolkata.csv') as csv_file:
        resto_reader = csv.DictReader(csv_file)
        for row in resto_reader:
            #print(row['Link'])
            urls.append(row['Link'].split('/')[-1])

    for i in range(0,7926):
        url = 'https://www.zomato.com/kolkata/' + urls[i]
        print(i+1,' : ',url)
        try:
           r = Restaurant(url)
        except:
           continue
def main():
    with open('reviews_csv_all.csv', 'a', encoding='utf-8') as f:
            spamwriter = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            spamwriter.writerow(['Restaurant Name','Restaurant Id','User Name','User Id','User Link','User Rating','Review Time','Review Text'])
    test_review()
    


if __name__ == '__main__':
    main()
