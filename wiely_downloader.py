import csv
import undetected_chromedriver as uc
import time
import os
import sys
from selenium.webdriver.common.by import By

def setup_driver(output_dir):
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--disable-popup-blocking')
    prefs = {
        "download.default_directory": output_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return uc.Chrome(options=chrome_options)

def download_pdf(driver, pdf_url):
    try:
        driver.get(pdf_url)
        time.sleep(5)
        download_button = driver.find_element(By.CSS_SELECTOR, 'a.navbar-download')
        download_button.click()
        print(f"PDF download initiated for {pdf_url}")
        time.sleep(30)
    except Exception as e:
        print(f"Error processing {pdf_url}: {e}")

def main(output_dir, csv_file):
    driver = setup_driver(output_dir)
    try:
        with open(csv_file, newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                pdf_url = row[0]
                download_pdf(driver, pdf_url)
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python wiley_downloader.py <output_directory> <csv_file>")
        sys.exit(1)
    output_dir = sys.argv[1]
    csv_file = sys.argv[2]
    main(output_dir, csv_file)