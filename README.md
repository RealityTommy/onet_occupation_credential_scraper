# ONET Occupation Credential Scraper

This project is a Python-based web scraping application designed to extract certifications and related details for various occupations from the ONET Online platform. The application navigates to ONET pages for each occupation, scrapes the list of certifications, and retrieves detailed information, including descriptions and certifying organizations. The collected data is saved in a CSV file for further use.

## Table of Contents
- [Project Overview](#project-overview)
- [Setup](#setup)
- [Usage](#usage)
- [Directory Structure](#directory-structure)
- [Configuration](#configuration)
- [Output Details](#output-details)
- [Dependencies](#dependencies)
- [Notes](#notes)
- [License](#license)

## Project Overview

The program takes a CSV file containing occupation names and their corresponding ONET codes as input. It then:
1. Navigates to the ONET certification page for each occupation.
2. Extracts details about certifications, including:
   - Certification name
   - Certification description
   - Certifying organization name
   - Certifying organization website
3. Saves the collected information in a CSV file.
4. Provides detailed console feedback, including progress for each occupation and certification.

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/onet-certification-scraper.git
   cd onet-certification-scraper
   ```

2. **Set up a virtual environment (recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install ChromeDriver**:
   - Download ChromeDriver that matches your version of Chrome [here](https://sites.google.com/a/chromium.org/chromedriver/).
   - Set the `CHROME_DRIVER_PATH` environment variable to the path of your ChromeDriver executable.

## Usage

1. **Prepare the input CSV**:
   - Place the input CSV (`occupation_input.csv`) containing occupation names and ONET codes in the `input` directory.
   - The CSV should have the following structure:
     ```
     occupation name,onet code
     Software Developers,15-1132.00
     Registered Nurses,29-1141.00
     ```

2. **Set the output directory path**:
   - Set the environment variable `OUTPUT_DIR_PATH` to the path where you want to store the output CSV and logs.

3. **Run the program**:
   ```bash
   python main.py
   ```

   The program will start scraping, and the console will display:
   - Occupation progress
   - Certification progress for each occupation
   - Total successes and failures

## Directory Structure

The project follows this structure:

```
onet-certification-scraper/
│
├── input/
│   └── occupation_input.csv     # Input CSV file with occupations and ONET codes
├── output/
│   └── occupation_credentials_output.csv   # Output CSV file with scraped certifications
├── app/
│   └── main.py                  # Main Python script
├── requirements.txt             # List of required Python libraries
└── README.md                    # Documentation
```

## Configuration

The application uses environment variables for configuration:
- **`CHROME_DRIVER_PATH`**: Path to the ChromeDriver executable.
- **`OUTPUT_DIR_PATH`**: Path to the base directory containing `input` and `output` folders.

Ensure these environment variables are correctly set before running the program.

## Output Details

The program outputs a CSV file (`occupation_credentials_output.csv`) in the `output` directory. The CSV file contains the following columns:
- **Occupation Name**: The name of the occupation (e.g., "Software Developers").
- **Credential Name**: The name of the certification.
- **Credential Description**: A detailed description of the certification.
- **Certifying Organization Name**: The name of the certifying organization.
- **Certifying Organization Website**: The website of the certifying organization (if available).

## Dependencies

The application requires the following Python libraries:
- `pandas`
- `selenium`
- `beautifulsoup4`
- `tqdm`

All dependencies are listed in `requirements.txt`. Install them using:
```bash
pip install -r requirements.txt
```

## Notes

- **ChromeDriver**: Ensure that your ChromeDriver version matches your local Chrome browser version.
- **Rate Limiting**: The program includes delays (`time.sleep`) to prevent overwhelming the ONET servers. Adjust the delay time as needed.
- **Error Handling**: The program logs errors for any failed certification scraping attempts and continues with the next certification to ensure it completes all occupations.

## License

This project is open-source and licensed under the MIT License. Feel free to use and modify the code as needed.