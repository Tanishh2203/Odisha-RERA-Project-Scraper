import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, StaleElementReferenceException
)
import json
import warnings
warnings.filterwarnings('ignore')

class EnhancedOdishaRERAProjectScraper:
    def __init__(self, headless=False):
        self.base_url = "https://rera.odisha.gov.in"
        self.projects_url = "https://rera.odisha.gov.in/projects/project-list"
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with optimized settings"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 30)  # Increased timeout
        self.driver.set_page_load_timeout(60)  # Increased page load timeout
    
    def wait_and_load(self, url, wait_time=10):  # Increased wait time
        """Navigate to URL and wait for page to load"""
        try:
            print(f"Loading: {url}")
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(wait_time)
            return True
        except Exception as e:
            print(f"Error loading {url}: {str(e)}")
            return False
    
    def safe_get_text(self, element):
        """Safely extract text from element"""
        try:
            return element.text.strip() if element else ""
        except (StaleElementReferenceException, WebDriverException):
            return ""
    
    def find_project_cards(self):
        """Find project cards on the main listing page"""
        if not self.wait_and_load(self.projects_url):
            return []
        
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.project-card")))
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.project-card")
            print(f"Found {len(cards)} cards using selector: div.project-card")
            return cards[:6]
        except TimeoutException:
            print("No project cards found with div.project-card")
            return []
    
    def extract_card_info(self, card):
        """Extract basic info from project card with enhanced selectors"""
        info = {
            'project_name': '',
            'rera_no': '',
            'promoter_name': '',
            'view_details_btn': None
        }
        
        try:
            # Extract project name with broader selectors
            try:
                name_element = card.find_element(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, div.card-title, div[class*='title'], div[class*='name']")
                info['project_name'] = self.safe_get_text(name_element)
            except Exception as e:
                print(f"   Error extracting project name from card: {str(e)}")
            
            # Extract RERA number with fallback
            try:
                card_text = card.text
                print(f"   Debug: Card text for RERA: {card_text[:200]}...")  # Debug output
                match = re.search(r'(RP|PS)/\d{1,2}/\d{4}/\d{5}', card_text)
                if match:
                    info['rera_no'] = match.group(0)
                else:
                    rera_element = card.find_element(By.XPATH, ".//*[contains(text(), 'Reg') or contains(text(), 'No') or contains(text(), 'RP/') or contains(text(), 'PS/')] | .//*[contains(@class, 'reg')]")
                    rera_text = self.safe_get_text(rera_element)
                    match = re.search(r'(RP|PS)/\d{1,2}/\d{4}/\d{5}', rera_text)
                    if match:
                        info['rera_no'] = match.group(0)
            except Exception as e:
                print(f"   Error extracting RERA number from card: {str(e)}")
            
            # Extract promoter name with broader selectors
            try:
                promoter_element = card.find_element(By.XPATH, ".//*[contains(text(), 'by ') or contains(text(), 'Promoter') or contains(text(), 'Developer')] | .//*[contains(@class, 'promoter')]")
                promoter_text = self.safe_get_text(promoter_element)
                info['promoter_name'] = promoter_text.replace('by ', '').strip()
            except Exception as e:
                print(f"   Error extracting promoter name from card: {str(e)}")
            
            # Find View Details button with broader selectors
            try:
                btn = card.find_element(By.XPATH, ".//a[contains(text(), 'View Details') or contains(text(), 'Details') or contains(@class, 'view-details') or contains(@href, 'details')]")
                info['view_details_btn'] = btn
            except Exception as e:
                print(f"   Error finding View Details button: {str(e)}")
        
        except Exception as e:
            print(f"   Unexpected error in extract_card_info: {str(e)}")
        
        return info
    
    def click_view_details_and_extract(self, card_info):
        """Click View Details button and extract detailed information"""
        project_data = {
            'Project URL': self.driver.current_url,
            'RERA Regd. No': card_info.get('rera_no', ''),
            'Project Name': card_info.get('project_name', ''),
            'Promoter Name': card_info.get('promoter_name', ''),
            'Promoter Address': '',
            'GST No': ''
        }
        
        if not card_info.get('view_details_btn'):
            print("   ⚠️ No View Details button found")
            return project_data
        
        try:
            button = card_info['view_details_btn']
            print(f"   🖱️ Clicking View Details button...")
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(2)  # Increased wait
            self.driver.execute_script("arguments[0].click();", button)
            
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//h3 | //h2 | //h1")))
            time.sleep(5)
            project_data['Project URL'] = self.driver.current_url  # Capture URL after navigation
            
            detailed_info = self.extract_detailed_information()
            for key, value in detailed_info.items():
                if value and value != "Not Available":
                    project_data[key] = value
            
            # Navigate back
            self.driver.back()
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.project-card")))
            time.sleep(5)
            
        except Exception as e:
            print(f"   ❌ Error clicking View Details: {str(e)}")
        
        return project_data
    
    def extract_detailed_information(self):
        """Extract detailed information from the details page with retries"""
        details = {
            'RERA Regd. No': 'Not Available',
            'Project Name': 'Not Available',
            'Promoter Name': 'Not Available',
            'Promoter Address': 'Not Available',
            'GST No': 'Not Available'
        }
        
        try:
            # Extract Project Name
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, "h1, h2, h3, div.project-title, div[class*='title'], div[class*='name']")
                details['Project Name'] = self.safe_get_text(name_element)
            except Exception as e:
                print(f"   Error extracting project name from detail page: {str(e)}")
            
            # Extract RERA Number with retry
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    page_source = self.driver.page_source
                    print(f"   Debug: Searching page source for RERA: {details['Project Name']}")  # Debug output
                    match = re.search(r'(RP|PS)/\d{1,2}/\d{4}/\d{5}', page_source)
                    if match:
                        details['RERA Regd. No'] = match.group(0)
                        break
                    else:
                        details_section = self.driver.find_element(By.CSS_SELECTOR, "div.project-details, div.container, table, div.card-body, div[class*='details']")
                        details_text = details_section.text
                        match = re.search(r'(RP|PS)/\d{1,2}/\d{4}/\d{5}', details_text)
                        if match:
                            details['RERA Regd. No'] = match.group(0)
                            break
                    retry_count += 1
                    time.sleep(3)
                except Exception as e:
                    print(f"   Error extracting RERA number from detail page (attempt {retry_count + 1}): {str(e)}")
                    retry_count += 1
                    time.sleep(3)
            
            # Click Promoter Details tab with retries
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    tab = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Promoter Details') or contains(text(), 'Promoter') or contains(@href, 'promoter')]")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", tab)
                    time.sleep(2)
                    self.driver.execute_script("arguments[0].click();", tab)
                    time.sleep(10)  # Increased wait for dynamic content
                    print("   ✅ Clicked Promoter Details tab")
                    
                    # Wait for promoter details to load
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.promoter-details, table, div.container, div[class*='promoter']")))
                    break
                except Exception as e:
                    print(f"   ⚠️ Promoter Details tab not found or not clickable (attempt {retry_count + 1}): {str(e)}")
                    retry_count += 1
                    time.sleep(3)
            
            # Extract Promoter Name
            try:
                promoter_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Name') or contains(text(), 'Proprietor') or contains(text(), 'Individual') or contains(text(), 'M/S')]/following-sibling::* | //*[contains(text(), 'M/S')] | //*[contains(@class, 'promoter-name')]")
                promoter_text = self.safe_get_text(promoter_element)
                if promoter_text and len(promoter_text) > 3 and 'Name' not in promoter_text:
                    details['Promoter Name'] = promoter_text
            except Exception as e:
                print(f"   Error extracting promoter name: {str(e)}")
            
            # Extract Promoter Address
            try:
                address_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Address')]/following-sibling::* | //*[contains(text(), 'Address')]/..//* | //div[contains(@class, 'address')] | //*[contains(@class, 'address')]")
                address_text = ""
                for elem in address_elements:
                    text = self.safe_get_text(elem)
                    if len(text) > 10 and 'Address' not in text:
                        address_text = text
                        break
                
                if not address_text:
                    try:
                        table = self.driver.find_element(By.CSS_SELECTOR, "table")
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        for row in rows:
                            if 'Address' in row.text:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) > 1:
                                    address_text = self.safe_get_text(cells[1])
                                    if len(address_text) > 10:
                                        break
                    except:
                        pass
                
                if address_text and len(address_text) > 10:
                    details['Promoter Address'] = address_text
            except Exception as e:
                print(f"   Error extracting promoter address: {str(e)}")
            
            # Extract GST Number with retry
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    promoter_section = self.driver.find_element(By.CSS_SELECTOR, "div.promoter-details, table, div.container, div[class*='promoter']")
                    promoter_text = promoter_section.text
                    print(f"   Debug: Promoter section text for GST: {promoter_text[:200]}...")  # Debug output
                    match = re.search(r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9]{1}[Z]{1}[0-9A-Z]{1}', promoter_text)
                    if match:
                        details['GST No'] = match.group(0)
                        break
                    else:
                        # Enhanced table parsing
                        try:
                            table = promoter_section.find_element(By.CSS_SELECTOR, "table")
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            for row in rows:
                                row_text = row.text
                                print(f"   Debug: Table row for GST: {row_text}")  # Debug output
                                if 'GST' in row_text or 'Tax' in row_text:
                                    cells = row.find_elements(By.TAG_NAME, "td")
                                    if len(cells) > 1:
                                        gst_text = self.safe_get_text(cells[1])
                                        match = re.search(r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9]{1}[Z]{1}[0-9A-Z]{1}', gst_text)
                                        if match:
                                            details['GST No'] = match.group(0)
                                            break
                        except:
                            pass
                    
                    # Fallback: Search entire page source
                    if details['GST No'] == 'Not Available':
                        page_source = self.driver.page_source
                        match = re.search(r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9]{1}[Z]{1}[0-9A-Z]{1}', page_source)
                        if match:
                            details['GST No'] = match.group(0)
                            break
                    
                    retry_count += 1
                    time.sleep(3)
                except Exception as e:
                    print(f"   Error extracting GST number (attempt {retry_count + 1}): {str(e)}")
                    retry_count += 1
                    time.sleep(3)
        
        except Exception as e:
            print(f"   ❌ Error extracting detailed information: {str(e)}")
        
        return details
    
    def generate_html_table(self, projects_data, filename='enhanced_odisha_rera_top6_projects.html'):
        """Generate an HTML file with a styled table of project data"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Odisha RERA Registered Projects</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto py-8 px-4">
        <h1 class="text-3xl font-bold text-center mb-8">Odisha RERA Registered Projects</h1>
        <div class="overflow-x-auto">
            <table class="min-w-full bg-white shadow-md rounded-lg">
                <thead class="bg-gray-800 text-white">
                    <tr>
                        <th class="py-3 px-4 text-left">Project Name</th>
                        <th class="py-3 px-4 text-left">RERA Regd. No</th>
                        <th class="py-3 px-4 text-left">Promoter Name</th>
                        <th class="py-3 px-4 text-left">Promoter Address</th>
                        <th class="py-3 px-4 text-left">GST No</th>
                        <th class="py-3 px-4 text-left">Project URL</th>
                    </tr>
                </thead>
                <tbody>
"""
        for project in projects_data:
            html_content += """
                    <tr class="border-b hover:bg-gray-50">
                        <td class="py-3 px-4">{}</td>
                        <td class="py-3 px-4">{}</td>
                        <td class="py-3 px-4">{}</td>
                        <td class="py-3 px-4">{}</td>
                        <td class="py-3 px-4">{}</td>
                        <td class="py-3 px-4"><a href="{}" class="text-blue-600 hover:underline" target="_blank">{}</a></td>
                    </tr>
""".format(
                project.get('Project Name', 'Not Available'),
                project.get('RERA Regd. No', 'Not Available'),
                project.get('Promoter Name', 'Not Available'),
                project.get('Promoter Address', 'Not Available'),
                project.get('GST No', 'Not Available'),
                project.get('Project URL', '#'),
                project.get('Project URL', 'Not Available')[:50] + "..." if project.get('Project URL') else 'Not Available'
            )
        
        html_content += """
                </tbody>
            </table>
        </div>
        <p class="text-center mt-4 text-gray-600">Generated on {}</p>
    </div>
</body>
</html>
""".format(time.strftime("%Y-%m-%d %H:%M:%S"))

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   📄 {filename}")
        return html_content
    
    def scrape_top_6_projects(self):
        """Main method to scrape top 6 projects"""
        print("🚀 Starting Enhanced Odisha RERA Top 6 Projects Scraping...")
        print("=" * 70)
        
        all_projects = []
        
        for i in range(1, 7):
            print(f"\n🔍 Processing Project {i}/6...")
            project_cards = self.find_project_cards()
            if not project_cards or i > len(project_cards):
                print("   ❌ Insufficient project cards found!")
                all_projects.append({
                    'Project URL': self.driver.current_url,
                    'RERA Regd. No': '',
                    'Project Name': '',
                    'Promoter Name': '',
                    'Promoter Address': '',
                    'GST No': ''
                })
                continue
            
            card = project_cards[i-1]
            retry_count = 0
            max_retries = 3
            project_data = None
            
            while retry_count < max_retries:
                try:
                    card_info = self.extract_card_info(card)
                    print(f"   📌 Project: {card_info['project_name']}")
                    print(f"   🏷️ RERA: {card_info['rera_no']}")
                    print(f"   🏢 Promoter: {card_info['promoter_name']}")
                    
                    project_data = self.click_view_details_and_extract(card_info)
                    if any(project_data[key] for key in ['RERA Regd. No', 'Project Name', 'Promoter Name']):
                        print(f"   ✅ Success: {project_data['Project Name']} - {project_data['RERA Regd. No']}")
                        if project_data['GST No'] and project_data['GST No'] != 'Not Available':
                            print(f"      💼 GST No: {project_data['GST No']}")
                    else:
                        print(f"   ⚠️ Limited data extracted")
                    
                    all_projects.append(project_data)
                    break
                
                except StaleElementReferenceException:
                    retry_count += 1
                    print(f"   Retry {retry_count}/{max_retries} due to stale element")
                    time.sleep(2)
                    if retry_count < max_retries:
                        project_cards = self.find_project_cards()
                        if i <= len(project_cards):
                            card = project_cards[i-1]
                        else:
                            break
                except Exception as e:
                    print(f"   ❌ Error processing project {i}: {str(e)}")
                    all_projects.append({
                        'Project URL': self.driver.current_url,
                        'RERA Regd. No': '',
                        'Project Name': '',
                        'Promoter Name': '',
                        'Promoter Address': '',
                        'GST No': ''
                    })
                    break
            
            if not project_data:
                all_projects.append({
                    'Project URL': self.driver.current_url,
                    'RERA Regd. No': '',
                    'Project Name': '',
                    'Promoter Name': '',
                    'Promoter Address': '',
                    'GST No': ''
                })
        
        return all_projects
    
    def save_results(self, projects_data, filename='enhanced_odisha_rera_top6_projects'):
        """Save results to CSV, JSON, and HTML files"""
        if not projects_data:
            print("❌ No data to save!")
            return
        
        csv_file = f"{filename}.csv"
        df = pd.DataFrame(projects_data)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        json_file = f"{filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(projects_data, f, indent=2, ensure_ascii=False)
        
        html_file = f"{filename}.html"
        self.generate_html_table(projects_data, html_file)
        
        print(f"\n💾 Files saved:")
        print(f"   📄 {csv_file}")
        print(f"   📄 {json_file}")
        print(f"   📄 {html_file}")
        
        return df
    
    def display_results(self, projects_data):
        """Display results in a formatted table"""
        if not projects_data:
            print("❌ No data to display!")
            return
        
        print("\n" + "="*100)
        print("🏢 ENHANCED ODISHA RERA - TOP 6 PROJECTS DETAILS")
        print("="*100)
        
        for i, project in enumerate(projects_data, 1):
            print(f"\n🏗️ PROJECT {i}:")
            print("-" * 80)
            for key, value in project.items():
                display_value = value if value else "Not Available"
                if key == 'Project URL' and len(display_value) > 60:
                    display_value = display_value[:57] + "..."
                print(f"   {key:20}: {display_value}")
    
    def cleanup(self):
        """Close browser and cleanup"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass

def main():
    """Main execution function"""
    scraper = None
    try:
        print("🔧 Initializing Enhanced Odisha RERA Scraper...")
        scraper = EnhancedOdishaRERAProjectScraper(headless=False)
        projects_data = scraper.scrape_top_6_projects()
        scraper.display_results(projects_data)
        scraper.save_results(projects_data)
        
        valid_projects = sum(1 for p in projects_data if any(p[k] for k in ['RERA Regd. No', 'Project Name', 'Promoter Name']))
        projects_with_gst = sum(1 for p in projects_data if p.get('GST No') and p.get('GST No') != 'Not Available')
        
        print(f"\n🎉 ENHANCED SCRAPING COMPLETED!")
        print(f"   ✅ Successfully extracted {valid_projects} out of {len(projects_data)} projects")
        print(f"   💼 Projects with GST Numbers: {projects_with_gst}")
        print(f"   📁 Output files: enhanced_odisha_rera_top6_projects.csv, .json, and .html")
        
        return projects_data
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        return []
    
    finally:
        if scraper:
            scraper.cleanup()

if __name__ == "__main__":
    results = main()
    if results:
        print(f"\n📋 Final validation: {len(results)} projects processed")
        complete_projects = [p for p in results if p.get('RERA Regd. No') and p.get('Project Name')]
        gst_projects = [p for p in results if p.get('GST No') and p.get('GST No') != 'Not Available']
        print(f"   🔍 {len(complete_projects)} projects have RERA No. and Project Name")
        print(f"   💼 {len(gst_projects)} projects have GST Numbers")
    else:
        print("\n⚠️ No results obtained. Check your internet connection and try again.")