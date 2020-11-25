import re
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
import time
import threading
PATH = "C:\Program Files (x86)\chromedriver.exe"
driver = webdriver.Chrome(PATH)

DEFAULT_URL = "http://web.mst.edu/~chaman/"
SITES_TO_AVOID = ['twitter','youtube','facebook','amazon']
MAX_SITES = 5
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
init_semaphore = threading.BoundedSemaphore()  # Binary Semaphore
dict_assignment_sem = threading.Semaphore()  # General Semaphore
scraping_sem = threading.Semaphore() # General Semaphore
new_urls_sem = threading.Semaphore() # General Semaphore

website_dict = {}
sites_visited = 0

class myThread(threading.Thread):
    def __init__(self, threadID, name):
        super().__init__()
        self.threadID = threadID
        self.name = name
        self.num_sites = 0
        self.sites_visited = {}

    def run(self):
        print ("Starting " + self.name)
        web_scraper()

def main(thread_count, url):
    start_time = time.time()
    num_threads = thread_count
    threads = []
    global website_dict
    website_dict = convert(initialization(url))
    print("Initializing dict")
    print(website_dict)
    for new_thread in range(1,num_threads + 1):
        thread = myThread(new_thread, "Thread " + str(new_thread))
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print("Websites Found:" + str(len(website_dict)))
    print(website_dict)
    print("Exiting Main Thread")
    print("--- %s seconds ---" % (time.time() - start_time))

def web_scraper():
    global website_dict
    global sites_visited
    # Todo calculate the time it took to execute

    #print(threading.current_thread().name + " : Starting Loop\n")
    while sites_visited < MAX_SITES:
        #print("SITES VISITED: " + str(sites_visited) + "\n")

        # Find site that hasn't been visited
        dict_assignment_sem.acquire()
        next_site = find_next_site(website_dict)
        #print(threading.current_thread().name + " : Next site is " + str(next_site) + "\n")
        website_dict[next_site] = True
        dict_assignment_sem.release()
        if next_site is None:
            break

        # Web scrape all urls and return them
        scraping_sem.acquire()
        newly_scraped_sites = get_links(next_site)
        scraping_sem.release()

        # Store remaining sites into a dictionary
        new_urls_sem.acquire()
        new_urls = vet_new_urls(newly_scraped_sites, website_dict)
        new_urls_sem.release()

        dict_assignment_sem.acquire()
        if new_urls is not None:
            website_dict.update(convert(new_urls))
        sites_visited += 1
        dict_assignment_sem.release()

        # Sleep for an amount of time as not to spam the website with request
        time.sleep(1)

def initialization(url):
    return get_links(url)

def get_links(url):
    passed_regex_urls = []
    driver.get(url)

    search = driver.find_elements_by_tag_name('a')

    for link in search:
        try:
            url = link.get_attribute('href')
        except StaleElementReferenceException:  # ignore this error
            print(threading.current_thread().name + " : Exception occurred trying to access " + str(url) + "\n")
            break
        regex_urls = (url_regex(url))
        if regex_urls is not None:
            passed_regex_urls += regex_urls
    return passed_regex_urls

def vet_new_urls(new_urls_lst, website_dict):
    new_urls = []
    for link in new_urls_lst:
        if link not in website_dict:
            new_urls.append(link)
    if len(new_urls) > 0:
        return new_urls
    return None

def find_next_site(website_dict):
    for key in website_dict:
        if website_dict[key] is False:
            return key
    return None

def url_regex(url):
    if url is not None:
        if 'http' in url:
            for avoided_site in SITES_TO_AVOID:
                if avoided_site in url:
                    return None
            valid_url = re.findall(URL_REGEX, url)
            return [x[0] for x in valid_url]
    return None

def convert(lst):
    new_dict = {lst[index]: False for index in range(len(lst))}
    return new_dict

if __name__ == '__main__':
    invalid_input = True
    thread_count = 1
    url = DEFAULT_URL
    #  Below is a bunch of input cleansing guarantee valid parameters
    print("Welcome User")
    while invalid_input:
        multi_thread = input("Would you like to run multi-threaded? (Y/N) : ")
        if type(multi_thread) is not type(""):
            print("Incorrect input...")
            break
        if multi_thread.lower() == 'y':
            thread_count = int(input("How many threads would you like to run? : "))
            if type(thread_count) is not type(1):
                print("Incorrect input...")
                break
        invalid_input = False

    url_input = input("Enter the a valid URL you wish to scrape: ")
    #  Validates that the URL is formatted properly using a regex
    if url_regex(url_input) is not None:
        url = url_input
    else:
        print("Invalid URL using 'DEFAULT URL' instead...")

    main(thread_count, url)