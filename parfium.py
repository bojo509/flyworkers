import requests
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# TODO: fix getting the size elements

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the WebDriver service
service = ChromeService(ChromeDriverManager().install())

def fetch_urls(endpoint):
    try:
        response = requests.get(endpoint)
        while response.status_code != 200:
            response = requests.get(endpoint)
            logging.info("Retrying to fetch data")
        response.raise_for_status()
        perfumes = response.json()

        urls = [{"link": perfume["link"], "title": perfume["title"], "shortid": perfume["shortid"]} for perfume in perfumes]
        return urls

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def create_driver(headless):
    logging.info("Creating new WebDriver instance")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    return webdriver.Chrome(service=service, options=chrome_options)

def send_discord_message(content):
    data = {"content": content}
    response = requests.post(webhook['url'], json=data)
    if response.status_code == 204:
        logging.info("Webhook message sent successfully!")
    else:
        logging.error(f"Failed to send webhook message. Status code: {response.status_code}")

def check_price_pbg(driver, urls):
    for item in urls:
        try:
            logging.info(f"Navigating to {item["title"]}")
            driver.get(item["link"])
            logging.info("Page loaded successfully")

            # Wait for the page to load completely
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Scroll down the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for any lazy-loaded elements

            try:
                # Wait for the elements to be present
                price_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".variant-price"))
                )

                availability_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".js-product-availability"))
                )

                if price_elements:
                    logging.info(f"Found {len(price_elements)} price elements")

                # Get the price for the biggest available size
                price_to_pay = price_elements[-1].text if price_elements else "N/A"

                # Check if availability text exists
                availability_text = availability_element.text[2:] if availability_element else ""
                
                # Construct the message
                message = f"{item['title']}: {price_to_pay}"
                if availability_text:
                    message += f" {availability_text}"

                message += f" - {url}{item['shortid']}"
                logging.info(f"Price found: {price_to_pay}")
                send_discord_message(f"Price of {message}")

            except TimeoutException:
                logging.error("Timeout waiting for price elements to load")
                send_discord_message(f"No price found for {item['title']}")
            except NoSuchElementException:
                logging.error("Price elements not found on the page")
            except Exception as e:
                logging.error(f"Error while processing price elements: {str(e)}")

        except WebDriverException as e:
            logging.error(f"WebDriver error: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Error during page load or processing: {str(e)}")
            return False
        
    return True

def main():
    time.sleep(5)
    try:
        driver = create_driver(True)
        if not check_price_pbg(driver, urls):
            logging.info("check_price_pbg failed, recreating WebDriver")
            driver.quit()
            driver = create_driver(True)
        driver.quit()
    except KeyboardInterrupt:
        logging.info("Closing WebDriver")
        driver.quit()
    finally:
        logging.info("Script finished")

if __name__ == "__main__":
    try:
        logging.info("Starting the script")
        endpoint = os.getenv('ENDPOINT')

        shortIdResponse = requests.get(endpoint + "/shortidendpoint")
        shortIdResponse.raise_for_status()
        shortIdData = shortIdResponse.json()
        url = shortIdData["url"]

        webhook = requests.get(endpoint + "/webhook")
        webhook.raise_for_status()
        webhook = webhook.json()

        logging.info(f"Fetching URLs from {endpoint}")
        urls = fetch_urls(endpoint)
        logging.info(f"Found {len(urls)} URLs")
        main()
    except KeyboardInterrupt:
        logging.info("Script terminated by user")
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
