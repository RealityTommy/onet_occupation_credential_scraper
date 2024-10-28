import os
import csv
import time
import pandas as pd
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="scraper.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Set up paths based on environment variables or use default paths
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")
INPUT_CSV = os.getenv("INPUT_CSV_PATH", "/input/occupation_input.csv")
OUTPUT_CSV = os.getenv("OUTPUT_CSV_PATH", "/output/occupation_credentials_output.csv")


def check_env_vars():
    """Check if essential environment variables are set correctly."""
    if not os.path.exists(CHROME_DRIVER_PATH):
        raise EnvironmentError("CHROME_DRIVER_PATH is invalid or missing.")
    if not os.path.isfile(INPUT_CSV):
        raise EnvironmentError("INPUT_CSV_PATH is invalid or missing.")
    if not os.path.isdir(os.path.dirname(OUTPUT_CSV)):
        raise EnvironmentError("OUTPUT_CSV_PATH directory is invalid or missing.")


def setup_driver():
    """
    Set up the Selenium WebDriver with options.
    This function configures the browser (Chrome) to run in headless mode (no GUI) and sets a page load timeout.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def parse_modal_content(driver):
    """Extracts certification description and organization website from the modal."""
    modal_content = BeautifulSoup(driver.page_source, "html.parser")
    description_div = modal_content.select_one(
        "div#ajaxModal .accordion .accordion-item:nth-of-type(2) div div"
    )
    description = description_div.text.strip() if description_div else "N/A"

    # Check if description is a placeholder; replace it if necessary
    if description == "More information about this certification":
        description = "TODO: Write description."

    org_link = modal_content.select_one(
        "div#ajaxModal .accordion .accordion-item:nth-of-type(1) a"
    )
    org_website = org_link["href"].strip() if org_link else "N/A"

    return description, org_website
    """Extracts certification description and organization website from the modal."""
    modal_content = BeautifulSoup(driver.page_source, "html.parser")
    description_div = modal_content.select_one(
        "div#ajaxModal .accordion .accordion-item:nth-of-type(2) div div"
    )
    description = description_div.text.strip() if description_div else "N/A"

    org_link = modal_content.select_one(
        "div#ajaxModal .accordion .accordion-item:nth-of-type(1) a"
    )
    org_website = org_link["href"].strip() if org_link else "N/A"

    return description, org_website


def scrape_certifications(driver, occupation_name, occupation_code, max_retries=3):
    url = f"https://www.onetonline.org/link/localcert/{occupation_code}"
    retries = 0
    certifications = []

    while retries < max_retries:
        try:
            driver.get(url)
            break
        except Exception as e:
            logging.warning(f"Attempt {retries + 1} failed for {occupation_name}: {e}")
            retries += 1
            time.sleep(5)

    if retries == max_retries:
        logging.error(
            f"Failed to load page for {occupation_name} after {max_retries} attempts."
        )
        return certifications, 0, 1

    success_count = 0
    failure_count = 0

    try:
        # Check if no certifications are available
        try:
            no_cert_msg = driver.find_element(
                By.XPATH, "/html/body/div/div[1]/div/div[2]/p[1]/b"
            ).text
            if "No certifications were found." in no_cert_msg:
                logging.info(f"No certifications found for {occupation_name}")
                return certifications, 0, 0
        except Exception:
            pass

        # Wait for certification table
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]

        for row in rows:
            try:
                title_link = row.find_element(By.TAG_NAME, "a")
                cert_name = title_link.text.strip()

                # Skip if cert_name is empty
                if not cert_name:
                    logging.info(
                        f"Skipped empty credential name for occupation '{occupation_name}'"
                    )
                    continue

                cert_org = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Open modal and parse content
                driver.execute_script("arguments[0].click();", title_link)
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "ajaxModal"))
                )
                time.sleep(0.5)
                description, org_website = parse_modal_content(driver)

                # Add certification details to list
                certifications.append(
                    {
                        "Occupation Name": occupation_name,
                        "Credential Name": cert_name,
                        "Credential Description": description,
                        "Certifying Organization Name": cert_org,
                        "Certifying Organization Website": org_website,
                    }
                )

                # Close modal
                try:
                    close_button = driver.find_element(
                        By.CSS_SELECTOR,
                        "button.close, .modal-header button, .btn-close",
                    )
                    driver.execute_script("arguments[0].click();", close_button)
                except Exception:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)

                success_count += 1

            except Exception as cert_error:
                logging.error(
                    f"Failed to process certification for {occupation_name}: {cert_error}"
                )
                failure_count += 1

    except Exception as e:
        logging.error(
            f"Error processing occupation {occupation_name} ({occupation_code}): {e}"
        )

    return certifications, success_count, failure_count
    url = f"https://www.onetonline.org/link/localcert/{occupation_code}"
    retries = 0
    certifications = []

    while retries < max_retries:
        try:
            driver.get(url)
            break
        except Exception as e:
            logging.warning(f"Attempt {retries + 1} failed for {occupation_name}: {e}")
            retries += 1
            time.sleep(5)

    if retries == max_retries:
        logging.error(
            f"Failed to load page for {occupation_name} after {max_retries} attempts."
        )
        return certifications, 0, 1

    success_count = 0
    failure_count = 0

    try:
        # Check if no certifications are available
        try:
            no_cert_msg = driver.find_element(
                By.XPATH, "/html/body/div/div[1]/div/div[2]/p[1]/b"
            ).text
            if "No certifications were found." in no_cert_msg:
                logging.info(f"No certifications found for {occupation_name}")
                return certifications, 0, 0
        except Exception:
            pass

        # Wait for certification table
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]

        for row in rows:
            try:
                title_link = row.find_element(By.TAG_NAME, "a")
                cert_name = title_link.text.strip()
                cert_org = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Open modal and parse content
                driver.execute_script("arguments[0].click();", title_link)
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "ajaxModal"))
                )
                time.sleep(0.5)
                description, org_website = parse_modal_content(driver)

                # Add certification details to list
                certifications.append(
                    {
                        "Occupation Name": occupation_name,
                        "Credential Name": cert_name,
                        "Credential Description": description,
                        "Certifying Organization Name": cert_org,
                        "Certifying Organization Website": org_website,
                    }
                )

                # Close modal
                try:
                    close_button = driver.find_element(
                        By.CSS_SELECTOR,
                        "button.close, .modal-header button, .btn-close",
                    )
                    driver.execute_script("arguments[0].click();", close_button)
                except Exception:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)

                success_count += 1

            except Exception as cert_error:
                logging.error(
                    f"Failed to process certification for {occupation_name}: {cert_error}"
                )
                failure_count += 1

    except Exception as e:
        logging.error(
            f"Error processing occupation {occupation_name} ({occupation_code}): {e}"
        )

    return certifications, success_count, failure_count


def save_to_csv(data):
    """Save collected certification data to a CSV file."""
    with open(OUTPUT_CSV, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Occupation Name",
                "Credential Name",
                "Credential Description",
                "Certifying Organization Name",
                "Certifying Organization Website",
            ]
        )
        for row in data:
            writer.writerow(
                [
                    row["Occupation Name"],
                    row["Credential Name"],
                    row["Credential Description"],
                    row["Certifying Organization Name"],
                    row["Certifying Organization Website"],
                ]
            )


def main():
    check_env_vars()  # Validate environment variables

    driver = setup_driver()
    df = pd.read_csv(INPUT_CSV)

    all_certifications = []
    total_occupations = len(df)
    overall_success_count = 0
    overall_failure_count = 0

    for index, row in tqdm(
        df.iterrows(),
        total=total_occupations,
        desc="Processing Occupations",
        ncols=100,
        ascii=True,
    ):
        occupation_name = row["occupation name"]
        occupation_code = row["onet code"]

        certifications, success_count, failure_count = scrape_certifications(
            driver, occupation_name, occupation_code
        )
        all_certifications.extend(certifications)

        overall_success_count += success_count
        overall_failure_count += failure_count

    save_to_csv(all_certifications)
    driver.quit()


if __name__ == "__main__":
    main()
