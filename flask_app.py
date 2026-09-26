from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from bs4 import BeautifulSoup

from secret import usr, psw 
import time

driver = webdriver.Chrome()

'''
students = [
    ('Bazenikas, Alexandros', '5692079'),
    ('Beach, Matthew', '5692100'),
    ('Brahmachary, Aneek', '5692090'),
    ('Briggs-Garcia, Arnario', '5692070'),
    ('Chahal, Tanvir', '5692068'),
    ('Del Grosso, Sean', '5710864'),
    ('Di Meo, Mario', '5692076'),
    ('Evans, Rasheed', '5692074'),
    ('Hemraj, Avinash', '4174707'),
    ('Herrera, Noah', '5692093'),
    ('Jimenez, Victor', '5692084'),
    ('Koumantaris, Ari', '5692082'),
    ('Laatikainen, Kai', '5692088'),
    ('Lee, Nicolaus', '5692077'),
    ('Mochwart, Shane', '5692071'),
    ('Morales, Alesandra', '5692086'),
    ('Morales, Oliver', '5731690'),
    ('Ospina, Nicolas', '5692072'),
    ('Pappert, Kenneth', '5692073'),
    ('Paqueo, Rachel', '5692080'),
    ('Pullo, Sydney', '5692103'),
    ('Reyes, Bella', '5692098'),
    ('Singh, Brahmjot', '5741364'),
    ('Singh, Gurneet', '5692109'),
    ('Singh, Manveer', '5692106'),
    ('Somrah, Alexander', '5692075'),
    ('Yang, Rachel', '5741365'),
    ('Yeung, Yuvonnie', '5692111'),
    ('Zapanta, Joaquin', '5731691'),
    ('Zhang, Thomas', '5692095'),
]
'''

# shorter list for test-purposes:

students = [
    ('Bazenikas, Alexandros', '5692079'),
    ('Beach, Matthew', '5692100'),
    ('Brahmachary, Aneek', '5692090'),
]

results = []

section = "600389"
assignment = "75952406"

# Go to the PROJECTSTEM website
print("Opening CODEHS...")
driver.get("https://codehs.com/login")
title = driver.title
driver.implicitly_wait(0.5)

# Fill in the username and password fields and click 'Log In'
print("Logging in...")
text_box = driver.find_element(by=By.ID, value="login-email")       # username
text_box.click()
driver.implicitly_wait(0.5)
text_box.send_keys(usr)
text_box = driver.find_element(by=By.ID, value="login-password")    # password
text_box.send_keys(psw)
submit_button = driver.find_element(by=By.XPATH, value="//button[@type='submit']")
submit_button.click()
driver.implicitly_wait(3)
time.sleep(3)

# Now for each student, go to the specific assignment page and take a screenshot

for student in students:
    s_name = student[0]
    s_nr = student[1]

    print("Opening Grades page... for student")
    url = "https://codehs.com/student/" + s_nr + "/section/600389/assignment/" + assignment
    driver.get(url)
    #title = driver.title
    driver.implicitly_wait(2)

    # Clicking tab 'Output'
    # Locate the div element with the specified XPath
    button_div = driver.find_element(by=By.XPATH, value="//div[@class=' r c']")
    # Click the element
    button_div.click()

    # clicking "Check Code"
    # Locate the button using the updated method
    submit_button = driver.find_element(by=By.XPATH, value="//button[normalize-space()='Check Code']")
    # Click the button
    submit_button.click()
    # Wait...
    driver.implicitly_wait(4)
    time.sleep(4)
    # //button[normalize-space()='Check Code']
    # Locate the <p> element with the XPath
    score_element = driver.find_element(by=By.XPATH, value="//p[@id='score-text']")
    # Extract the text content of the element
    score_text = score_element.text

    print("saving screenshot")
    print(s_name, " - ", score_text)

    results.append((s_name,score_text))

    datetime_string = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    filename = "screenshots/scrn_" + assignment + "_" + s_name.replace(" ","_") + "_" + datetime_string +".png"
    driver.save_screenshot(filename)
    driver.implicitly_wait(3)
    time.sleep(3)

driver.close

for result in results:
    print(f"| {result[0]} |  {result[1]} |")
