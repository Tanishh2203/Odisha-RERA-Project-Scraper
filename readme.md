# Enhanced Odisha RERA Project Scraper

#### Overview

The Enhanced Odisha RERA Project Scraper is a Python-based web scraping tool designed to extract detailed information about the top 6 real estate projects registered with the Odisha Real Estate Regulatory Authority (RERA) from the official website (https://rera.odisha.gov.in). The scraper collects key project details such as project name, RERA registration number, promoter name, promoter address, GST number, and project URL, and saves the data in CSV, JSON, and HTML formats.
The tool uses Selenium WebDriver for robust web scraping, handling dynamic content, and navigating through the RERA website's project listings and details pages. It includes error handling, retries, and optimized selectors to ensure reliable data extraction even with varying website structures.

#### Features

- Scrapes the top 6 projects from the Odisha RERA website's project list.
- Extracts detailed information including:
- Project Name
- RERA Registration Number
- Promoter Name
- Promoter Address
- GST Number
- Project URL
- Saves data in multiple formats: CSV, JSON, and a styled HTML table.
- Supports headless browsing for faster execution.
- Includes robust error handling and retry mechanisms for stable scraping.
- Uses regular expressions for reliable extraction of RERA numbers and GST numbers.
- Displays results in a formatted console output for quick review.

#### Prerequisites

To run the scraper, ensure you have the following installed:

- Google Chrome (required for Selenium WebDriver)
- Required Python packages (install via pip):pip install pandas selenium webdriver-manager

#### Installation

**Clone the Repository (or download the script):**
`git clone <repository-url>
cd <repository-directory>`

**Install Dependencies:Run the following command to install the required Python packages:**
`pip install -r requirements.txt`

Alternatively, install the packages individually:
`pip install pandas selenium webdriver-manager`

**Ensure Google Chrome is Installed:**The scraper uses ChromeDriver, which requires Google Chrome. The webdriver-manager library will automatically download the compatible ChromeDriver version.

#### Usage

**Run the Scraper:**Execute the main script to start scraping:
`python enhanced_odisha_rera_scraper.py`

- By default, the scraper runs in non-headless mode (browser visible).
- To run in headless mode (no browser UI), modify the EnhancedOdishaRERAProjectScraper initialization in the main() function:
  `scraper = EnhancedOdishaRERAProjectScraper(headless=True)`

**
Output:**

- The scraper will process the top 6 projects and display their details in the console.
- Output files will be generated in the project directory:
- *enhanced_odisha_rera_top6_projects.csv: *Project data in CSV format.
- _enhanced_odisha_rera_top6_projects.json:_ Project data in JSON format.
- _enhanced_odisha_rera_top6_projects.html:_ Styled HTML table with project data.
- The HTML file can be opened in a web browser to view a formatted table of the scraped data.

**Example Output:**The console will display a summary of each project's details, such as:
🏗️ PROJECT 1:

---

Project URL : https://rera.odisha.gov.in/projects/details/...
RERA Regd. No : RP/19/2023/12345
Project Name : Sample Project
Promoter Name : Sample Developer
Promoter Address : 123, Sample Street, Bhubaneswar, Odisha
GST No : 21ABCDE1234F1Z5

### Project Structure

```
enhanced_odisha_rera_scraper/
├── enhanced_odisha_rera_scraper.py
├── README.md
├── requirements.txt
├── enhanced_odisha_rera_top6_projects.csv
├── enhanced_odisha_rera_top6_projects.json
├── enhanced_odisha_rera_top6_projects.html
```

#### How It Works

**Initialization:**

- Sets up a Selenium WebDriver with Chrome, configured for optimal performance and anti-bot detection avoidance.
- Supports headless mode for faster execution.

**Scraping Process:**

- Navigates to the Odisha RERA projects page (https://rera.odisha.gov.in/projects/project-list).
- Identifies project cards using CSS selectors and extracts basic information (project name, RERA number, promoter name).
- Clicks the "View Details" button for each project to access detailed information.
- Extracts additional details (promoter address, GST number) from the project details page, with retries for dynamic content.

**
Data Handling:**

- Uses regular expressions to reliably extract RERA numbers (e.g., RP/19/2023/12345) and GST numbers (e.g., 21ABCDE1234F1Z5).
- Stores data in a structured format and saves it as CSV, JSON, and HTML files.
- Displays results in the console with a formatted table.

**Error Handling:**

- Handles common Selenium exceptions (e.g., TimeoutException, StaleElementReferenceException).
- Implements retries for dynamic content loading and element interactions.
- Provides fallback selectors to accommodate varying website structures.
