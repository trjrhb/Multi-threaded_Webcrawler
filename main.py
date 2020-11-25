import re
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
import time
import threading

PATH = "C:\Program Files (x86)\chromedriver.exe"
driver = webdriver.Chrome(PATH)
DEFAULT_URL = "http://web.mst.edu/~chaman/"
SITES_TO_AVOID = ['twitter', 'youtube', 'facebook', 'amazon']
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
init_semaphore = threading.BoundedSemaphore()  # Binary Semaphore
dict_assignment_sem = threading.Semaphore()  # General Semaphore
scraping_sem = threading.Semaphore()  # General Semaphore
new_urls_sem = threading.Semaphore()  # General Semaphore

website_dict = {}
sites_visited = 0
max_sites_to_visit = 0

class myThread(threading.Thread):
    def __init__(self, threadID, name):
        super().__init__()
        self.threadID = threadID
        self.name = name

    def run(self):
        print("Starting " + self.name)
        web_scraper()


def main(thread_count, url):
    global website_dict
    start_time = time.time()
    num_threads = thread_count
    threads = []
    website_dict = convert(initialization(url))

    # Starts each thread
    for new_thread in range(1, num_threads + 1):
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

    while sites_visited < max_sites_to_visit:

        # Find site that hasn't been visited
        dict_assignment_sem.acquire()
        next_site = find_next_site()
        if sites_visited < max_sites_to_visit:
            website_dict[next_site] = True

        if next_site is None:
            break

        # Web scrape all urls and return them
        scraping_sem.acquire()
        newly_scraped_sites = get_links(next_site)
        dict_assignment_sem.release()

        # Store remaining sites into a dictionary
        new_urls_sem.acquire()
        new_urls = vet_new_urls(newly_scraped_sites)
        scraping_sem.release()

        dict_assignment_sem.acquire()
        if new_urls is not None and sites_visited < max_sites_to_visit:
            website_dict.update(convert(new_urls))
        new_urls_sem.release()
        sites_visited += 1
        dict_assignment_sem.release()

        # Sleep for an amount of time as not to spam the website with request
        time.sleep(1)


# Initializes the dictionary with all URLs found on the starting url
def initialization(starting_url):
    return get_links(starting_url)


# Returns a list of urls that were found and validated using a regex
def get_links(url):
    passed_regex_urls = []
    driver.get(url)
    search = driver.find_elements_by_tag_name('a')
    # Loops through all webpage elements that are tagged with 'a' to determine if it is a url
    for link in search:
        # Exception handling in case something goes awry
        try:
            url = link.get_attribute('href')
        except StaleElementReferenceException:  # Ignore this error
            # print(threading.current_thread().name + " : Exception occurred trying to access " + str(url) + "\n")
            break
        regex_urls = (url_regex(url))
        if regex_urls is not None:
            passed_regex_urls += regex_urls
    return passed_regex_urls


# Filters out any URLs from sources that should be avoided or already existing in the dictionary
def vet_new_urls(new_urls_lst):
    new_urls = []
    for link in new_urls_lst:
        if link not in website_dict:
            new_urls.append(link)
    if len(new_urls) > 0:
        return new_urls
    return None


# Finds the next site that hasn't been visited in the dictionary
def find_next_site():
    for key in website_dict:
        if website_dict[key] is False:
            return key
    return None


# Returns the url if it matches the regex 'URL REGEX'
def url_regex(url):
    if url is not None:
        if 'http' in url:
            for avoided_site in SITES_TO_AVOID:
                if avoided_site in url:
                    return None
            valid_url = re.findall(URL_REGEX, url)
            return [x[0] for x in valid_url]
    return None


# A simple helper function to convert a list to a dictionary
def convert(lst):
    new_dict = {lst[index]: False for index in range(len(lst))}
    return new_dict


# Start of program and get user input for main()
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
            try:
                thread_count = int(input("How many threads would you like to run? : "))
                num_sites_to_visit = int(input("How many sites would you like to visit? : "))
                max_sites_to_visit = num_sites_to_visit
            except():
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
