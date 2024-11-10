import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import csv
import sys
import re

# Set up logging
logging.basicConfig(filename='sciencedirect_downloader.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver(output_dir):
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    prefs = {
        "download.default_directory": output_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return uc.Chrome(version_main=128, options=chrome_options) 

def wait_for_download_complete(expected_filename, output_dir, timeout=300):
    """Wait for the download to complete, checking every 5 seconds"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(os.path.join(output_dir, expected_filename)):
            return True
        time.sleep(5)
    return False

def random_delay(min_seconds, max_seconds):
    time.sleep(random.uniform(min_seconds, max_seconds))

def split_urls(url):
    """Split concatenated URLs"""
    return re.findall(r'https?://[^\s]+', url)

def download_sciencedirect_pdfs(driver, output_dir, sciencedirect_csv):
    if not os.path.exists(sciencedirect_csv):
        print("No ScienceDirect URLs found in CSV file.")
        return

    with open(sciencedirect_csv, 'r') as file:
        reader = csv.reader(file)
        urls = [url for row in reader for url in split_urls(row[0])]  # Split and flatten URLs

    print(f"Found {len(urls)} unique ScienceDirect URLs to process.")

    for index, url in enumerate(urls, 1):
        try:
            print(f"Processing article {index}/{len(urls)}: {url}")
            driver.get(url)
            
            # Wait for and click the "View PDF" button
            view_pdf_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.link-button-primary[aria-label='View PDF. Opens in a new window.']"))
            )
            view_pdf_button.click()
            print("Clicked View PDF button")
            
            # Switch to the new tab
            WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(2))
            driver.switch_to.window(driver.window_handles[-1])
            
            # Wait for the download button in the PDF viewer to be clickable
            download_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Download PDF']"))
            )
            
            # Click the download button
            download_button.click()
            print("Clicked download button in PDF viewer")
            
            # Wait for the download to complete
            expected_filename = f"{url.split('/')[-1]}.pdf"
            if wait_for_download_complete(expected_filename, output_dir):
                print(f"Download completed successfully: {expected_filename}")
            else:
                print(f"Download timed out or failed for: {expected_filename}")

        except Exception as e:
            print(f"Error during ScienceDirect PDF download for {url}: {e}")

        finally:
            # Safely close tabs and switch back
            try:
                if len(driver.window_handles) > 1:
                    driver.close()  # Close the current tab (PDF viewer)
                driver.switch_to.window(driver.window_handles[0])  # Switch back to the main tab
            except Exception as e:
                print(f"Error while closing tab or switching: {e}")

        random_delay(10, 20)

    # Clear the CSV file after processing all URLs
    open(sciencedirect_csv, 'w').close()
    print("Cleared ScienceDirect URLs CSV file after processing.")

def main():
    if len(sys.argv) != 3:
        print("Usage: python sciencedirect_downloader.py <output_directory> <csv_file>")
        sys.exit(1)

    output_dir = sys.argv[1]
    sciencedirect_csv = sys.argv[2]

    print(f"Output directory: {output_dir}")
    print(f"CSV file: {sciencedirect_csv}")

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    driver = setup_driver(output_dir)
    print("Browser setup complete.")

    try:
        download_sciencedirect_pdfs(driver, output_dir, sciencedirect_csv)
    except Exception as e:
        print(f"An error occurred during the download process: {e}")
    finally:
        print("Closing browser...")
        driver.quit()

    print("ScienceDirect download process completed.")

if __name__ == "__main__":
    main()