import os
import csv
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from tqdm import tqdm

# Set up paths based on environment variables or use default paths
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")
INPUT_CSV = os.getenv("INPUT_CSV_PATH", "/app/input/occupation_input.csv")
OUTPUT_CSV = os.getenv(
    "OUTPUT_CSV_PATH", "/app/output/occupation_credentials_output.csv"
)


def setup_driver():
    """
    Set up the Selenium WebDriver with options.
    This function configures the browser (Chrome) to run in headless mode (no GUI) and sets a page load timeout.
    """
    chrome_options = Options()
    chrome_options.add_argument(
        "--headless"
    )  # Run Chrome without opening a browser window
    chrome_options.add_argument("--disable-gpu")  # Disable GPU for compatibility
    chrome_options.add_argument(
        "--no-sandbox"
    )  # For running Chrome as root in containers
    chrome_options.add_argument(
        "--disable-dev-shm-usage"
    )  # Overcome limited resource problems
    service = Service(CHROME_DRIVER_PATH)  # Point to the ChromeDriver executable
    driver = webdriver.Chrome(
        service=service, options=chrome_options
    )  # Create the driver

    driver.set_page_load_timeout(60)  # Set the page load timeout to 60 seconds
    return driver


def scrape_certifications(driver, occupation_name, occupation_code, max_retries=3):
    """
    Scrape certifications for a specific occupation from ONET.

    Parameters:
        driver: Selenium WebDriver instance.
        occupation_name: The name of the occupation (e.g., "Software Developers").
        occupation_code: The ONET code for the occupation (e.g., "15-1121.00").
        max_retries: Number of times to retry loading the page in case of a timeout.

    Returns:
        A list of dictionaries containing certification details for the occupation,
        and counts of successes and failures.
    """
    url = f"https://www.onetonline.org/link/localcert/{occupation_code}"
    retries = 0
    certifications = []

    while retries < max_retries:
        try:
            driver.get(url)  # Navigate to the URL
            break  # Exit loop if successful
        except Exception as e:
            print(f"Attempt {retries + 1} failed: {e}")
            retries += 1
            time.sleep(5)  # Wait for a few seconds before retrying

    if retries == max_retries:
        print(
            f"Failed to load the page for {occupation_name} after {max_retries} attempts."
        )
        return certifications, 0, 1  # Return empty data indicating failure

    success_count = 0
    failure_count = 0

    try:
        # Check if there are no certifications for the occupation
        try:
            no_cert_msg = driver.find_element(
                By.XPATH, "/html/body/div/div[1]/div/div[2]/p[1]/b"
            ).text
            if "No certifications were found." in no_cert_msg:
                print(f"No certifications were found for '{occupation_name}'")
                return (
                    certifications,
                    0,
                    1,
                )  # Return indicating no certifications were found
        except Exception:
            pass  # No "No certifications were found" message, continue to find the table

        # Wait for the table containing certifications to load on the page
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        # Find all the rows in the table, excluding the header row
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]
        total_certifications = len(rows)

        for i, row in enumerate(rows, start=1):
            start_time = time.time()  # Start timer for each certification
            try:
                # Get the link (title) and certifying organization from each row
                title_link = row.find_element(By.TAG_NAME, "a")
                cert_name = (
                    title_link.text.strip()
                )  # Get the text for the certification name
                cert_org = row.find_elements(By.TAG_NAME, "td")[
                    1
                ].text.strip()  # Get the organization name

                # Click the title link to open the modal window containing details
                driver.execute_script(
                    "arguments[0].click();", title_link
                )  # Use JS to click the link
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "ajaxModal"))
                )
                time.sleep(0.5)  # Pause to allow the modal to fully load

                # Use BeautifulSoup to parse the modal content
                modal_content = BeautifulSoup(driver.page_source, "html.parser")
                # Find the description inside the modal
                description_div = modal_content.select_one(
                    "div#ajaxModal .accordion .accordion-item:nth-of-type(2) div div"
                )
                description = description_div.text.strip() if description_div else "N/A"

                # Find the certifying organization's website link in the modal
                org_link = modal_content.select_one(
                    "div#ajaxModal .accordion .accordion-item:nth-of-type(1) a"
                )
                org_website = org_link["href"].strip() if org_link else "N/A"

                # Add the certification details to the list
                certifications.append(
                    {
                        "Occupation Name": occupation_name,
                        "Credential Name": cert_name,
                        "Credential Description": description,
                        "Certifying Organization Name": cert_org,
                        "Certifying Organization Website": org_website,
                    }
                )

                # Close the modal using alternative methods
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
                elapsed_time = time.time() - start_time
                certification_progress = (i / total_certifications) * 100
                print(
                    f"Certification Progress: {certification_progress:.2f}% - Successfully processed '{cert_name}' in {elapsed_time:.2f} seconds"
                )

            except Exception as cert_error:
                elapsed_time = time.time() - start_time
                failure_count += 1
                certification_progress = (i / total_certifications) * 100
                print(
                    f"Certification Progress: {certification_progress:.2f}% - Failed to process certification in {elapsed_time:.2f} seconds: {cert_error}"
                )

    except Exception as e:
        print(f"Error processing occupation {occupation_name} ({occupation_code}): {e}")

    return certifications, success_count, failure_count


def save_to_csv(data):
    """
    Save the collected certification data to a CSV file.

    Parameters:
        data: A list of dictionaries containing the certification details.
    """
    with open(OUTPUT_CSV, mode="w", newline="") as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(
            [
                "Occupation Name",
                "Credential Name",
                "Credential Description",
                "Certifying Organization Name",
                "Certifying Organization Website",
            ]
        )
        # Write each row of data to the CSV
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
    # Initialize the web driver
    driver = setup_driver()
    df = pd.read_csv(INPUT_CSV)  # Read in the CSV containing occupation names and codes

    all_certifications = []  # List to collect all certifications from all occupations
    total_occupations = len(df)  # Get the total number of occupations
    overall_success_count = 0
    overall_failure_count = 0

    # Loop through each occupation in the CSV using tqdm for progress display
    for index, row in tqdm(
        df.iterrows(),
        total=total_occupations,
        desc="Processing Occupations",
        ncols=100,
        ascii=True,
    ):
        occupation_name = row["occupation name"]
        occupation_code = row["onet code"]

        # Start timer for each occupation
        occupation_start_time = time.time()

        # Scrape certifications for the current occupation
        certifications, success_count, failure_count = scrape_certifications(
            driver, occupation_name, occupation_code
        )
        all_certifications.extend(certifications)

        # Update overall success and failure counts
        overall_success_count += success_count
        overall_failure_count += failure_count

        occupation_end_time = time.time()
        occupation_time = occupation_end_time - occupation_start_time
        occupation_progress = ((index + 1) / total_occupations) * 100

        # Display ongoing stats for each occupation
        print(f"Occupation Progress: {occupation_progress:.2f}%")
        print(f"Time taken for '{occupation_name}': {occupation_time:.2f} seconds")
        print(
            f"Total Successes: {overall_success_count}, Total Failures: {overall_failure_count}"
        )

        time.sleep(1)  # Pause to avoid overloading the server

    # Save all collected data to a CSV file
    save_to_csv(all_certifications)
    driver.quit()  # Close the web driver


if __name__ == "__main__":
    main()
