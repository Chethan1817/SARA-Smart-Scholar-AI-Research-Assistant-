import os
import csv
import time
import random
import logging
import sys
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re

logging.basicConfig(filename='mdpi_downloader.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        driver = uc.Chrome(version_main=128, options=options)
        print("Browser setup complete.")
        return driver
    except Exception as e:
        print(f"Error setting up ChromeDriver: {e}")
        return None

def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename = filename.replace(" ", "_")
    return filename

def download_pdf(pdf_url, output_dir):
    try:
        response = requests.get(pdf_url)
        if response.status_code == 200:
            article_number = pdf_url.split('/')[-2]
            file_name = sanitize_filename(f"{article_number}.pdf")
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"Downloaded: {file_path}")
            print(f"Downloaded: {file_path}")
            return True
        else:
            logging.error(f"Failed to download PDF from {pdf_url}. Status code: {response.status_code}")
            print(f"Failed to download PDF from {pdf_url}")
            return False
    except Exception as e:
        logging.error(f"Error downloading PDF from {pdf_url}: {e}")
        print(f"Error downloading PDF from {pdf_url}: {e}")
        return False

def process_mdpi_url(driver, url, output_dir):
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 5))
        try:
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.UD_ArticlePDF").get_attribute('href')
            print(f"PDF Link: {pdf_link}")
            success = download_pdf(pdf_link, output_dir)
            if success:
                logging.info(f"Successfully downloaded PDF from {url}")
                return True
            else:
                logging.warning(f"Failed to download PDF from {url}")
                return False
        except NoSuchElementException:
            logging.warning(f"No PDF link found for {url}")
            print(f"No PDF link found for {url}")
            return False
    except Exception as e:
        logging.error(f"Error processing MDPI URL {url}: {e}")
        print(f"Error processing MDPI URL {url}: {e}")
        return False

def main(output_dir, mdpi_csv):
    print(f"Output directory: {output_dir}")
    print(f"CSV file: {mdpi_csv}")

    os.makedirs(output_dir, exist_ok=True)

    driver = setup_driver()
    if not driver:
        print("Failed to set up the browser. Exiting.")
        return

    try:
        with open(mdpi_csv, 'r') as file:
            reader = csv.reader(file)
            mdpi_urls = [row[0] for row in reader]

        print(f"Found {len(mdpi_urls)} MDPI URLs to process.")
        
        successful_downloads = 0
        for i, url in enumerate(mdpi_urls, 1):
            print(f"Processing URL {i}/{len(mdpi_urls)}: {url}")
            if "mdpi.com" in url:
                success = process_mdpi_url(driver, url, output_dir)
                if success:
                    successful_downloads += 1
            else:
                logging.warning(f"Skipping non-MDPI URL: {url}")
                print(f"Skipping non-MDPI URL: {url}")
            
            time.sleep(random.uniform(5, 10))

        print(f"Successfully downloaded {successful_downloads} out of {len(mdpi_urls)} PDFs.")

        with open(mdpi_csv, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([])
        print("Cleared MDPI URLs CSV file after processing.")

    except FileNotFoundError:
        logging.error(f"CSV file not found: {mdpi_csv}")
        print(f"CSV file not found: {mdpi_csv}")
    except Exception as e:
        logging.error(f"Error processing MDPI URLs: {e}")
        print(f"Error processing MDPI URLs: {e}")
    finally:
        if driver:
            driver.quit()
            print("Closing browser...")

    logging.info("MDPI download process completed.")
    print("MDPI download process completed.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 mdpi_downloader.py <output_directory> <mdpi_csv_file>")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    mdpi_csv = sys.argv[2]
    main(output_dir, mdpi_csv)