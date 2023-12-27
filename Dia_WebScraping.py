from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas
import re
from unidecode import unidecode


def cerrarVentanaSesion(driver):
    """
    This function will close the windows that ask you to log in.
    """
    boton_presente = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'vtex-modal-layout-0-x-closeButtonContainer'))
    )
    boton_presente.click()
    driver.implicitly_wait(10)

def scrollPage(driver):
    """
    This function will scroll until the end of the page.
    """

    # Obtain the actual page's height
    height_before = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")

    # Scroll until the end of the page and wait the page complete load
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Obtain the new page's height
    height_after = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")

    # Repeat the process until the hight dont change anymore
    while height_before < height_after:
        height_before = height_after
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.implicitly_wait(10)
        time.sleep(2)
        height_after = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
    

def openPage(url, content = True):
    """
    This function will open thr url in chrome. Then if content is True will return the page content, 
    will return the page driver.
    """
    # Config chrome options. The window will open in full screen.
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized') 

    #Chromedriver's path, if you dont have it, you can download it in chromedriver page.
    chrome_driver_path = 'C:/Users/mega_/OneDrive/Desktop/chromedriver.exe'
    chrome_service = ChromeService(executable_path=chrome_driver_path)

    # Initialize chrome
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    # Load the page and wait until is load,
    driver.get(url)
    driver.implicitly_wait(10)
    time.sleep(2)

    # if content return the page content, else, return page's driver
    if content:
        page_content = driver.page_source
        driver.quit()
        return page_content
    else:
        return driver
    

# Open Dia's main page and close the log in window
driver = openPage("https://diaonline.supermercadosdia.com.ar/", False)
driver.implicitly_wait(10)
cerrarVentanaSesion(driver)

#Open the categories tab.
button_menu = driver.find_element(By.CSS_SELECTOR, '[data-id="mega-menu-trigger-button"]')
button_menu.click()
driver.implicitly_wait(10)
time.sleep(2)

# Seach for all the categories name.
categories = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, 'diaio-store-5-x-menuItem'))
)

dict_category = {}

# Iter over all categories
for category in categories:

    if category.text.strip() == "Kiosco":
        continue
    
    # move the mouse over the category 
    ActionChains(driver).move_to_element(category).perform()
    driver.implicitly_wait(10)
    time.sleep(1)
    category = unidecode(category.text.replace(" ", "-").replace(",","").strip())
    dict_category[category] = []

    #Get page content
    page_content = driver.page_source
    soup = BeautifulSoup(page_content, 'html.parser')

    #find all sub_categories from the category
    sub_categories = soup.find('ul', class_='diaio-store-5-x-menuContainer diaio-store-5-x-submenuContainer list ma0 pa0 pb3 br b--muted-4')
    sub_categories = sub_categories.find_all('li', class_='diaio-store-5-x-menuItem')

    #Iter over the sub categories and save then in a {category:[sub_categories]} dict                          
    for sub_category in sub_categories:
        dict_category[category].append( unidecode(sub_category.text.replace(" ", "-").replace(",","").strip()) )
        driver.implicitly_wait(10)
        time.sleep(1)
driver.quit()



items_data = []
# Iter over the dict keys.
for key in dict_category.keys():

    #iter over the values
    for value in dict_category[key]:
        # Page format https://diaonline.supermercadosdia.com.ar/category/sub_category
        url = "https://diaonline.supermercadosdia.com.ar/" + key + "/" + value
        driver = openPage(url, False)
        #Scroll until all the page is load.
        scrollPage(driver)
        
        # obtain page content and its products.
        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')
        page_content_products = soup.find("div", id = "gallery-layout-container")
        if not page_content_products:
            driver.quit()
            continue
        products = page_content_products.find_all("div", class_ = "vtex-search-result-3-x-galleryItem vtex-search-result-3-x-galleryItem--normal vtex-search-result-3-x-galleryItem--default pa4")
        # iter over the products, save its name and price in items_data.
        for product in products:
             
            name = product.find("span", class_="vtex-product-summary-2-x-productBrand vtex-product-summary-2-x-brandName t-body")
            price = product.find("span", class_="vtex-product-price-1-x-currencyContainer")
            if price:
                name = name.text.strip()
                price = price.text.strip()[1:]
                items_data.append([name, value, price])
        driver.quit()


# Save the data in a .csv file.

import pandas as pd
from datetime import datetime

column_names = ["Product", "Category", "Price"]
df = pd.DataFrame(items_data)
df.columns = column_names

date_today = datetime.now()
date_today = date_today.strftime("%d-%m-%Y")
save_file_name = f"Dia_Prices-{date_today}.csv"

df.to_csv(save_file_name, index = False, sep = ";")
