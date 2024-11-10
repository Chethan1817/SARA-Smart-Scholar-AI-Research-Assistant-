import os
import time
import random
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import re
import csv
import subprocess

# Set up logging
logging.basicConfig(filename='pdf_downloader.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return uc.Chrome(version_main=128, options=chrome_options)  # Specify your Chrome version

def choose_search_engine():
    print("Where would you like to search for PDFs?")
    print("1. Google")
    print("2. Google Scholar")
    choice = input("Enter your choice (1 or 2): ").strip()
    return 'google' if choice == '1' else 'scholar' if choice == '2' else None

def get_keywords():
    return input("Enter Key Word: ")

def setup_output_directory(keywords):
    output_dir = f"./pdf/{keywords.replace(' ', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def is_direct_pdf_link(url):
    return url.lower().endswith('.pdf')

def download_pdf(pdf_link, output_dir):
    try:
        response = requests.get(pdf_link, stream=True)
        if response.status_code == 200:
            file_name = pdf_link.split("/")[-1]
            pdf_path = os.path.join(output_dir, file_name)
            with open(pdf_path, 'wb') as pdf_file:
                for data in response.iter_content(1024):
                    pdf_file.write(data)
            logging.info(f"Downloaded PDF: {pdf_path}")
            return True
        else:
            logging.warning(f"Failed to download {pdf_link}: Invalid response status {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Failed to download {pdf_link}: {e}")
        return False

def store_sciencedirect_url(url, csv_file):
    match = re.search(r'(pii/\w+)', url)
    if match:
        article_id = match.group(1)
        clean_url = f"https://www.sciencedirect.com/science/article/abs/{article_id}"
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([clean_url])
        logging.info(f"Stored ScienceDirect URL in CSV: {clean_url}")
        print(f"Stored ScienceDirect URL: {clean_url}")
    else:
        logging.warning(f"Could not extract article identifier from URL: {url}")
        print(f"Warning: Could not extract article identifier from URL: {url}")

def store_mdpi_url(url, csv_file):
    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url])
    logging.info(f"Stored MDPI URL in CSV: {url}")
    print(f"Stored MDPI URL: {url}")

def store_wiley_url(driver, url, csv_file):
    try:
        # Navigate to the URL
        driver.get(url)
        random_delay(5, 10)  # Add a delay to allow the page to load

        # Extract the PDF link from Wiley page
        pdf_link = driver.find_element(By.CSS_SELECTOR, "a.pdf-download").get_attribute('href')

        if pdf_link:
            with open(csv_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([pdf_link])
            logging.info(f"Stored Wiley PDF URL in CSV: {pdf_link}")
            print(f"Stored Wiley PDF URL: {pdf_link}")
        else:
            logging.warning(f"No PDF link found for Wiley URL: {url}")
            print(f"No PDF link found for Wiley URL: {url}")
    except Exception as e:
        logging.error(f"Failed to extract PDF link from Wiley URL {url}: {e}")
        print(f"Failed to extract PDF link from Wiley URL {url}: {e}")

def store_tandfonline_url(driver, url, csv_file):
    try:
        # Navigate to the URL
        driver.get(url)
        random_delay(5, 10)  # Allow page to fully load
        
        # Extract the PDF link from Tandfonline page
        pdf_link = driver.find_element(By.CSS_SELECTOR, "a.show-pdf").get_attribute('href')

        if pdf_link:
            with open(csv_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([pdf_link])
            logging.info(f"Stored Tandfonline PDF URL in CSV: {pdf_link}")
            print(f"Stored Tandfonline PDF URL: {pdf_link}")
        else:
            logging.warning(f"No PDF link found for Tandfonline URL: {url}")
            print(f"No PDF link found for Tandfonline URL: {url}")
    except Exception as e:
        logging.error(f"Failed to extract PDF link from Tandfonline URL {url}: {e}")
        print(f"Failed to extract PDF link from Tandfonline URL {url}: {e}")

def get_heinonline_pdf_href(driver, url):
    try:
        # Navigate to the URL
        driver.get(url)
        random_delay(5, 10)  # Add a delay to allow the page to load

        # Locate the <a> tag inside the div with class "btn-group" and extract the href
        a_tag = driver.find_element(By.CSS_SELECTOR, "div.btn-group a")
        href = a_tag.get_attribute("href")

        # Print the URL and href for debugging
        print(f"URL: {url}\nHref: {href}\n")
        return href
    except Exception as e:
        logging.error(f"Failed to extract PDF href from HeinOnline URL {url}: {e}")
        print(f"Failed to extract PDF href from HeinOnline URL {url}: {e}")
        return None

def store_heinonline_url(driver, url, csv_file):
    pdf_href = get_heinonline_pdf_href(driver, url)
    if pdf_href:
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([pdf_href])
        logging.info(f"Stored HeinOnline PDF href in CSV: {pdf_href}")
        print(f"Stored HeinOnline PDF href: {pdf_href}")
    else:
        logging.warning(f"Could not extract PDF href from HeinOnline URL: {url}")
        print(f"Warning: Could not extract PDF href from HeinOnline URL: {url}")

def process_pdf_link(pdf_link, output_dir):
    print(f"Found PDF link: {pdf_link}")
    success = download_pdf(pdf_link, output_dir)
    if success:
        print(f"Successfully downloaded: {pdf_link}")
    else:
        print(f"Failed to download: {pdf_link}")
    random_delay(5, 10)

def search_google(driver, keywords, output_dir, sciencedirect_csv, mdpi_csv, heinonline_csv, wiley_csv, tandfonline_csv):
    driver.get("https://www.google.com/")
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
        search_url = f"https://www.google.com/search?q={keywords.replace(' ', '+')}+filetype:pdf&start={start}"
        driver.get(search_url)
        random_delay(10, 20)
        wait = WebDriverWait(driver, 20)
        pdf_links = []
        try:
            results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a")))
            for result in results:
                link = result.get_attribute('href')
                if link:
                    if is_direct_pdf_link(link):
                        process_pdf_link(link, output_dir)
                    elif 'sciencedirect.com' in link:
                        store_sciencedirect_url(link, sciencedirect_csv)
                    elif 'mdpi.com' in link:
                        store_mdpi_url(link, mdpi_csv)
                    elif 'heinonline.org' in link:
                        store_heinonline_url(driver, link, heinonline_csv)
                    elif 'onlinelibrary.wiley.com' in link:
                        store_wiley_url(driver, link, wiley_csv)
                    elif 'tandfonline.com' in link:
                        store_tandfonline_url(driver, link, tandfonline_csv)
                    elif link.endswith('.pdf'):
                        pdf_links.append(link)
        finally:
            for pdf_link in pdf_links:
                process_pdf_link(pdf_link, output_dir)

def search_google_scholar(driver, keywords, output_dir, sciencedirect_csv, mdpi_csv, heinonline_csv, wiley_csv, tandfonline_csv):
    driver.get("https://scholar.google.com/")
    random_delay(10, 20)
    search_bar = driver.find_element(By.NAME, 'q')
    search_bar.send_keys(keywords)
    search_bar.send_keys(Keys.RETURN)
    random_delay(10, 20)
    max_pages = 1  # You can increase this if you want to process more pages
    for page in range(max_pages):
        logging.info(f"Processing page {page + 1}...")
        print(f"Processing page {page + 1}...")
        
        start = page * 10
        search_url = f"https://scholar.google.com/scholar?q={keywords.replace(' ', '+')}&start={start}"
        driver.get(search_url)
        random_delay(10, 20)
        
        if "captcha" in driver.current_url.lower():
            logging.warning("CAPTCHA detected. Stopping script to avoid further issues.")
            print("CAPTCHA detected. Stopping script to avoid further issues.")
            return
        
        wait = WebDriverWait(driver, 20)
        article_links = []
        
        try:
            articles = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.gs_rt a")))
            for article in articles:
                article_links.append(article.get_attribute('href'))
            
            for index, article_link in enumerate(article_links):
                print(f"Processing article {index + 1}/{len(article_links)}")
                
                if is_direct_pdf_link(article_link):
                    process_pdf_link(article_link, output_dir)
                    continue
                
                driver.get(article_link)
                random_delay(10, 20)
                
                if 'sciencedirect.com' in driver.current_url:
                    store_sciencedirect_url(driver.current_url, sciencedirect_csv)
                    continue
                elif 'mdpi.com' in driver.current_url:
                    store_mdpi_url(driver.current_url, mdpi_csv)
                    continue
                elif 'heinonline.org' in driver.current_url:
                    store_heinonline_url(driver, driver.current_url, heinonline_csv)
                    continue
                elif 'onlinelibrary.wiley.com' in driver.current_url:
                    store_wiley_url(driver, driver.current_url, wiley_csv)
                    continue
                elif 'tandfonline.com' in driver.current_url:
                    store_tandfonline_url(driver, driver.current_url, tandfonline_csv)
                    continue
                
                pdf_link = None
                
                direct_pdfs = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
                if direct_pdfs:
                    pdf_link = direct_pdfs[0].get_attribute('href')
                
                if not pdf_link:
                    download_links = driver.find_elements(By.CSS_SELECTOR, "a.pdf-download-link")
                    if download_links:
                        pdf_link = download_links[0].get_attribute('href')
                
                if pdf_link:
                    process_pdf_link(pdf_link, output_dir)
                else:
                    print(f"No PDF link found for article: {article_link}")
        
        except Exception as e:
            logging.error(f"Error processing page: {e}")
            print(f"Error processing page: {e}")

def random_delay(min_seconds, max_seconds):
    time.sleep(random.uniform(min_seconds, max_seconds))

def cleanup_pdf_files(output_dir):
    for filename in os.listdir(output_dir):
        if filename.endswith('.pdf'):
            if re.search(r'\(\d+\)\.pdf$', filename):
                file_path = os.path.join(output_dir, filename)
                os.remove(file_path)
                logging.info(f"Deleted duplicate file: {filename}")
                print(f"Deleted duplicate file: {filename}")

def main():
    driver = setup_driver()
    search_engine = choose_search_engine()
    if not search_engine:
        logging.error("Invalid choice. Exiting script.")
        print("Invalid choice. Exiting script.")
        driver.quit()
        return
    keywords = get_keywords()
    output_dir = setup_output_directory(keywords)
    sciencedirect_csv = "sciencedirect_urls.csv"
    mdpi_csv = "mdpi_urls.csv"
    heinonline_csv = "heinonline_urls.csv"
    wiley_csv = "wiley_pdf_urls.csv"
    tandfonline_csv = "tandfonline_pdf_urls.csv"
    
    if search_engine == 'google':
        search_google(driver, keywords, output_dir, sciencedirect_csv, mdpi_csv, heinonline_csv, wiley_csv, tandfonline_csv)
    else:
        search_google_scholar(driver, keywords, output_dir, sciencedirect_csv, mdpi_csv, heinonline_csv, wiley_csv, tandfonline_csv)
    
    driver.quit()
    cleanup_pdf_files(output_dir)
    logging.info(f"PDFs have been downloaded and cleaned up in: {output_dir}")
    print(f"PDFs have been downloaded and cleaned up in: {output_dir}")
    
    # Subprocess calls for other downloading scripts
    try:
        print("Starting ScienceDirect download process...")
        subprocess.run(["python3", "sciencedirect_downloader.py", output_dir, sciencedirect_csv], check=True)
        print("ScienceDirect download process completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running sciencedirect_downloader.py: {e}")
        print(f"Error running sciencedirect_downloader.py: {e}")
    except FileNotFoundError:
        logging.error("python3 command not found. Please ensure Python 3 is installed and in your PATH.")
        print("python3 command not found. Please ensure Python 3 is installed and in your PATH.")

    try:
        print("Starting MDPI download process...")
        subprocess.run(["python3", "mdpi_downloader.py", output_dir, mdpi_csv], check=True)
        print("MDPI download process completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running mdpi_downloader.py: {e}")
        print(f"Error running mdpi_downloader.py: {e}")
    except FileNotFoundError:
        logging.error("python3 command not found. Please ensure Python 3 is installed and in your PATH.")
        print("python3 command not found. Please ensure Python 3 is installed and in your PATH.")

    try:
        print("Starting HeinOnline download process...")
        subprocess.run(["python3", "heinonline_downloader.py", output_dir, heinonline_csv], check=True)
        print("HeinOnline download process completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running heinonline_downloader.py: {e}")
        print(f"Error running heinonline_downloader.py: {e}")
    except FileNotFoundError:
        logging.error("python3 command not found. Please ensure Python 3 is installed and in your PATH.")
        print("python3 command not found. Please ensure Python 3 is installed and in your PATH.")

    try:
        print("Starting Wiley download process...")
        subprocess.run(["python3", "wiley_downloader.py", output_dir, wiley_csv], check=True)
        print("Wiley download process completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running wiley_downloader.py: {e}")
        print(f"Error running wiley_downloader.py: {e}")
    except FileNotFoundError:
        logging.error("python3 command not found. Please ensure Python 3 is installed and in your PATH.")
        print("python3 command not found. Please ensure Python 3 is installed and in your PATH.")

    try:
        print("Starting Tandfonline download process...")
        subprocess.run(["python3", "tandfonline_downloader.py", output_dir, tandfonline_csv], check=True)
        print("Tandfonline download process completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running tandfonline_downloader.py: {e}")
        print(f"Error running tandfonline_downloader.py: {e}")
    except FileNotFoundError:
        logging.error("python3 command not found. Please ensure Python 3 is installed and in your PATH.")
        print("python3 command not found. Please ensure Python 3 is installed and in your PATH.")

if __name__ == "__main__":
    main()
