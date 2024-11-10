import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import requests

# List of Tandfonline URLs
tandfonline_urls = [
    "https://www.tandfonline.com/doi/full/10.1080/09064710.2024.2396972?src=exp-la",
    "https://www.tandfonline.com/doi/full/10.1080/09064710.2024.2396973?src=exp-la",
    "https://www.tandfonline.com/doi/full/10.1080/09064710.2024.2392525?src=exp-la"
]

# Function to download PDF
def download_pdf(pdf_url, file_name):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        with open(file_name, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {file_name}")
    else:
        print(f"Failed to download PDF from {pdf_url}")

# Set up Chrome options
options = uc.ChromeOptions()
# options.add_argument('--headless')  # Uncomment if you want to run in headless mode
driver = uc.Chrome(options=options)

# Loop through Tandfonline URLs and download PDFs
for url in tandfonline_urls:
    try:
        driver.get(url)
        time.sleep(2)  # wait for the page to load
        
        if "tandfonline.com" in driver.current_url:
            # Find the PDF link on the page
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a.showpdf").get_attribute('href')
            print(f"PDF Link: {pdf_link}")
            
            # Generate file name for PDF
            pdf_name = f"{url.split('/')[-1].split('?')[0]}.pdf"
            
            # Download the PDF
            download_pdf(pdf_link, pdf_name)
        else:
            print(f"No Tandfonline content found at {url}")
    except Exception as e:
        print(f"Error processing {url}: {e}")

driver.quit()
