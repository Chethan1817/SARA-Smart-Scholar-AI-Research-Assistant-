import csv
import time
import sys
import undetected_chromedriver as uc

def setup_driver(output_dir):
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    prefs = {
        "download.default_directory": output_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)
    try:
        driver = uc.Chrome(version_main=128, options=options)
        print("Browser setup complete.")
        return driver
    except Exception as e:
        print(f"Error setting up ChromeDriver: {e}")
        raise

def open_pdf_urls(csv_file, output_dir):
    driver = setup_driver(output_dir)
    try:
        with open(csv_file, 'r') as file:
            csv_reader = csv.reader(file)
            for idx, row in enumerate(csv_reader, start=1):
                if row:
                    url = row[0].strip()
                    if not url.startswith('http'):
                        print(f"Skipping invalid URL at row {idx}: {url}")
                        continue
                    print(f"Opening URL at row {idx}: {url}")
                    driver.get(url)
                    time.sleep(8)
    except Exception as e:
        print(f"An error occurred while processing URLs: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python heinonline_downloader.py <output_directory> <path_to_csv_file>")
        sys.exit(1)

    output_dir = sys.argv[1]
    csv_file = sys.argv[2]
    open_pdf_urls(csv_file, output_dir)