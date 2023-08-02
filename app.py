from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup
import requests
import time
import os
import logging
import shutil
from subprocess import CREATE_NO_WINDOW


def is_webserver_reachable(ip_address):
    # Add "https://" to the beginning of the IP address
    url = "https://" + ip_address

    # Check if the web server is reachable
    try:
        response = requests.get(url, verify=False)
        if response.status_code != 200:
            logging.debug("Web server is not reachable.")
            return False
        else:
            return True
    except requests.exceptions.RequestException:
        logging.debug("Web server is not reachable.")
        return False
    

def start_webdriver(save_directory):
    # Add "https://" to the beginning of the IP address
    

    if is_webserver_reachable: 
        # Set the Firefox profile preferences for automatic download and headless mode
        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", save_directory)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream;\
                            text/plain;\
                            text/html;\
                            application/pdf;\
                            text/csv;\
                            application/json;\
                            application/zip;\
                            application/x-gzip;\
                            application/vnd.ms-excel;\
                            application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;\
                            application/msword;\
                            application/vnd.openxmlformats-officedocument.wordprocessingml.document;\
                            image/jpeg;\
                            image/png")

        options.set_preference("pdfjs.disabled", True)
        options.headless = True

        # Create a new Firefox driver with the modified profile and options
        driver_service = Service('./geckodriver.exe', log_path=os.devnull)
        driver_service.creation_flags = CREATE_NO_WINDOW
        driver = webdriver.Firefox(service=driver_service, options=options)
        logging.info("## Webdriver started ##")
        return driver   


def login_to_webserver(driver, ip_address, username, password):          
    
    url = "https://" + ip_address
    # Open Browser
    driver.get(url + "/Browse.html")
    assert "MiniWeb" in driver.title

    time.sleep(3)

    # Login
    elem = driver.find_element(By.NAME, "Login")
    elem.clear()
    elem.send_keys(username)
    elem = driver.find_element(By.NAME, "Password")
    elem.clear()
    elem.send_keys(password)
    elem.send_keys(Keys.RETURN)    

    time.sleep(1)


def is_user_logged_in(driver):
    print(driver.current_url)
    if "Loginpage.html" in driver.current_url:
        logging.debug("User logged out")
        return False
    else:
        logging.debug("User logged in")
        return True 


def get_file_list(driver, ip_address, sync_folder, username, password):
    
    if is_webserver_reachable(ip_address):
        if not is_user_logged_in(driver):
            login_to_webserver(driver, ip_address, username, password)
    else:
        logging.error("Webserver cannot be reached")
        return
    
    logging.info("Checking files ...")

    # Check if there are files in the specified directory
    sync_folder = 'https://' + ip_address + sync_folder #+ "?UP=TRUE&FORCEBROWSE"
    try:
        driver.get(sync_folder)
    except:
        is_webserver_reachable()
    # Get HTML Code of page
    html = driver.page_source

    # Beautifulsoup object for code analysis
    soup = BeautifulSoup(html, 'html.parser')

    # Find the table using CSS selector
    css_selector = "body > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(3) > div:nth-child(5) > font:nth-child(1) > table:nth-child(1)"
    target_table_css = soup.select_one(css_selector)

    # Find the table using XPath
    xpath = "/html/body/table[2]/tbody/tr/td[3]/div/font/table"
    target_table_xpath = soup.find(xpath)

    # Find the table using CSS path
    css_path = "html body table tbody tr td div font table"
    target_table_css_path = soup.select_one(css_path)

    # Check if the table is found
    if target_table_css:
        target_table = target_table_css
        #logging.info("CSS selector table used")
    elif target_table_xpath:
        target_table = target_table_xpath
        logging.info("XPath table used")
    elif target_table_css_path:
        target_table = target_table_css_path
        logging.info("CSS path table used")
    else:
        target_table = None

    file_list = []

    if target_table:
        rows = target_table.find_all('tr')  # Get all rows in the table

        for row in rows[2:]:  # Skip the first two rows as they contain headers and parent directory information
            cells = row.find_all('td')  # Get all cells in the row

            # Extract the relevant information from the cells
            file_name = cells[1].find('a').text.strip()  # Get the file name from the second cell anchor tag
            file_size = cells[2].text.strip()  # Get the file size from the third cell

            # Create a dictionary or a tuple with the extracted information
            file_info = {'file_name': file_name, 'file_size': file_size}

            # Add the file info to the file_list
            if(file_info["file_size"] != ''):
                file_list.append(file_info)

    return file_list


def move_file_to_syncFolder(save_directory, file_name):
    download_folder = os.path.expanduser("~\Downloads")
    file_path = os.path.join(download_folder, file_name)
    destination_path = os.path.join(save_directory, file_name)

    # Move file to sync_folder if it is contained in Download folder
    if os.path.isfile(file_path): 
        shutil.move(file_path, destination_path)
    elif not is_file_contained_in_save_directory(save_directory, file_name):
        logging.info(f"Could not move {file_name} to {save_directory}")
    
         
def is_file_contained_in_save_directory(save_directory, file_name):
    
    destination_path = os.path.join(save_directory, file_name)

    download_folder = os.path.expanduser("~\Downloads")
    file_path = os.path.join(download_folder, file_name)

    if os.path.isfile(destination_path):
        return True
    # elif os.path.isfile(file_path):
    #     move_file_to_syncFolder(save_directory, file_name)
    else:
        return False


def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_all_files(driver, file_list, save_directory, sync_folder, ip_address):
   ensure_directory_exists(save_directory)
   base_url = 'https://' + ip_address + sync_folder#.rstrip('?UP=TRUE&FORCEBROWSE') + '/'
   for file_info in file_list:
        file_name = file_info['file_name']
        
        if not is_file_contained_in_save_directory(save_directory, file_name):
            # Download the file using Selenium
            #driver.get(sync_folder)
            driver.get(base_url)
            link = driver.find_element(By.LINK_TEXT, file_name)
            link.click()    

            # Check if the file extension is .txt
            if file_name.lower().endswith('.txt'):
                 # Extract the content from the HTML response
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                content = soup.find('pre').text.strip()

                # Save the content to the file
                file_path = os.path.join(save_directory, file_name)
                with open(file_path, 'w') as file:
                    file.write(content)  
            else:
                # Wait for the file to be downloaded
                time.sleep(2)

                move_file_to_syncFolder(save_directory, file_name)
                       
            logging.info(f"File '{file_name}' downloaded successfully.")
        else:
            logging.debug(f"{file_name} already synchronized")


def check_files(driver, ip_address, save_directory, sync_folder, username, password):
    file_list = get_file_list(driver, ip_address, sync_folder, username, password)
    
    if file_list is not None:
        download_all_files(driver, file_list, save_directory,  sync_folder, ip_address)

    