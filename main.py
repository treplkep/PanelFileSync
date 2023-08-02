from selenium import webdriver
import logging
import configparser
import os
import schedule
import time
from pystray import MenuItem as item
import pystray
from app import login_to_webserver, check_files, start_webdriver
from PIL import Image
import platform
import threading
import subprocess
import sys



# Create an Icon for the system tray
def create_image(width, height, color1, color2):
    # Load the custom .ico file
    custom_icon = Image.open("icon.png")
    # Resize the custom icon to the desired dimensions
    custom_icon = custom_icon.resize((width, height))

    return custom_icon

# Load the configuration from the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Set up logging
log_file = config.get('General', 'log_file')
log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename=log_file, level=logging.INFO, format=log_format)

# Get the configuration values
ip_address = config.get('WebServer', 'ip_address')
username = config.get('WebServer', 'username')
password = config.get('WebServer', 'password')
save_directory = config.get('Paths', 'save_directory')    
save_directory = save_directory.replace("\\", "\\\\")   # Replace '\' with '\\' 
sync_folder = config.get('Paths', 'sync_folder')
sync_folder += "?UP=TRUE&FORCEBROWSE" 
interval = int(config.get('General', 'interval'))

# INFO
logging.info("### Panel file sync started! ###")
# userconfig = ('ip: '+ str(ip_address) + ' user: ' + username + 
#              ' targetDIR: ' + save_directory + 
#              ' srcDIR: ' + sync_folder + 
#              ' cycle: ' + str(interval))
# logging.info(userconfig)

# Start webdriver
driver = start_webdriver(save_directory)

# Login to the web server
try:
    login_to_webserver(driver, ip_address, username, password)
except:
    logging.error("Error during login attempt")
if not driver:
    exit()

# Wait for 2 seconds after login and before first sync
time.sleep(2)

# Perform initial synchronization
check_files(driver, ip_address, save_directory, sync_folder, username, password)

# Define the menu actions
def on_exit_selected(icon, item):

    logging.info("Exited by user")
    driver.quit()
    try:
        icon.stop()
        sys.exit()
    except SystemExit:
        pass
    
def on_show_log_selected(icon, item):
    subprocess.run(['notepad', log_file], creationflags=subprocess.CREATE_NO_WINDOW)

# Create a menu for the system tray
menu = [
    item('Show Log', on_show_log_selected),
    item('Exit', on_exit_selected)
    ]

# Create an icon for the system tray
icon = pystray.Icon("pfs", icon=create_image(64, 64, 'black', 'white'), menu=menu)


# Define the main function to run the scheduler
def main():
    schedule.every(interval).seconds.do(check_files, driver, ip_address, save_directory, sync_folder, username, password)

    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the main function in a separate thread
thread = threading.Thread(target=main)
thread.daemon = True
thread.start()
        

# Run the system tray applications
icon.run()

    



