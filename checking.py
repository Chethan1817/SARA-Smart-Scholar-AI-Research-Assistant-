import time
import random
import logging
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Logging setup
logging.basicConfig(filename='pdf_url_scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

ACADEMIC_DOMAINS = {
    "mdpi.com": "MDPI",
    "onlinelibrary.wiley.com": "Wiley",
    "tandfonline.com": "Taylor and Francis",
    "brill.com": "Brill",
    "link.springer.com": "Springer",
    "ieee.org": "IEEE",
    "researchgate.net": "ResearchGate",
    "heinonline.org": "HeinOnline",
    "cambridge.org": "Cambridge",
    "iopscience.iop.org": "IOP Science",
    "jstor.org": "JSTOR",
    "geoscienceworld.org": "Geoscience World"
}

def setup_driver():
    """Sets up and returns the Chrome WebDriver."""
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return uc.Chrome(options=chrome_options)

def choose_search_engine():
    """Prompts user to choose between Google or Google Scholar for searching PDFs."""
    print("Where would you like to search for PDFs?")
    print("1. Google")
    print("2. Google Scholar")
    choice = input("Enter your choice (1 or 2): ").strip()
    return 'google' if choice == '1' else 'scholar' if choice == '2' else None

def get_keywords():
    """Prompts user for search keywords."""
    return input("Enter Key Word: ")

def search_google_scholar(driver, keywords):
    """Searches Google Scholar for articles based on the given keywords."""
    driver.get("https://scholar.google.com/")
    random_delay(10, 20)

    search_bar = driver.find_element(By.NAME, 'q')
    search_bar.send_keys(keywords)
    search_bar.send_keys(Keys.RETURN)
    random_delay(10, 20)

    max_pages = 2
    for page in range(max_pages):
        logging.info(f"Processing page {page + 1}...")
        print(f"Processing page {page + 1}...")

        start = page * 10
        search_url = f"https://scholar.google.com/scholar?q={keywords.replace(' ', '+')}&start={start}"
        driver.get(search_url)
        random_delay(10, 20)

        if "captcha" in driver.current_url.lower():
            logging.warning("CAPTCHA detected. Stopping script.")
            print("CAPTCHA detected. Stopping script.")
            return

        wait = WebDriverWait(driver, 20)
        article_links = []

        try:
            articles = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.gs_rt a")))
            for article in articles:
                article_links.append(article.get_attribute('href'))

            process_article_links(driver, article_links)

        except Exception as e:
            logging.error(f"Error processing page: {e}")
            print(f"Error processing page: {e}")

def process_article_links(driver, article_links):
    """Processes each article link, looking for PDF URLs."""
    for index, article_link in enumerate(article_links):
        print(f"Processing article {index + 1}/{len(article_links)}")
        driver.get(article_link)
        random_delay(10, 20)

        pdf_link = find_pdf_link(driver)
        if pdf_link:
            print(f"Found PDF: {pdf_link}")
        else:
            print(f"No PDF link found for article: {article_link}")

def find_pdf_link(driver):
    """Locate a PDF link on the current page based on the website structure."""
    try:
        current_url = driver.current_url.lower()
        pdf_link = None

        if "mdpi.com" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.UD_ArticlePDF").get_attribute('href')
        elif "onlinelibrary.wiley.com" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.pdf-download").get_attribute('href')
        elif "tandfonline.com" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.show-pdf").get_attribute('href')
        elif "link.springer.com" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.c-pdf-download__link").get_attribute('href')
        elif "brill.com" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a[data-datatype='pdf']").get_attribute('href')
        elif "ieee.org" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.stats-document-lh-action-downloadPdf").get_attribute('href')
        elif "researchgate.net" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.js-target-download-btn").get_attribute('href')
        elif "iopscience.iop.org" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.wd-jnl-art-pdf-button-main").get_attribute('href')
        elif "geoscienceworld.org" in current_url:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.article-pdfLink").get_attribute('href')
        else:
            # Fallback to general PDF link search
            pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
            if pdf_links:
                pdf_link = pdf_links[0].get_attribute('href')

        return pdf_link

    except NoSuchElementException:
        logging.warning(f"PDF link element not found on {driver.current_url}")
        return None
    except Exception as e:
        logging.error(f"Error while finding PDF link: {e}")
        return None

def random_delay(min_seconds, max_seconds):
    """Pauses execution for a random period between min_seconds and max_seconds."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def main():
    """Main function to drive the script."""
    driver = setup_driver()
    search_engine = choose_search_engine()
    if not search_engine:
        logging.error("Invalid choice. Exiting script.")
        print("Invalid choice. Exiting script.")
        driver.quit()
        return
    keywords = get_keywords()

    if search_engine == 'scholar':
        search_google_scholar(driver, keywords)
    else:
        print("Google search not implemented in this version.")
        logging.warning("Google search not implemented in this version.")

    driver.quit()
    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()
