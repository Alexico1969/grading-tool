import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
from secret import usr, psw  # Import credentials from 'secret' module
from chromedriver_py import binary_path
from datetime import datetime

# Initialize the database
def initialize_database():
    conn = sqlite3.connect("settings.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            assignment TEXT NOT NULL
        )
    """)
    # Insert default values if table is empty
    cursor.execute("SELECT * FROM settings")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (section, assignment) VALUES (?, ?)", ("779844", "193450567"))
    conn.commit()
    conn.close()


# Fetch default settings from the database
def get_default_settings():
    conn = sqlite3.connect("settings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT section, assignment FROM settings LIMIT 1")
    settings = cursor.fetchone()
    conn.close()
    return settings


# Save updated settings into the database
def save_settings(section, assignment):
    conn = sqlite3.connect("settings.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET section = ?, assignment = ? WHERE id = 1", (section, assignment))
    conn.commit()
    conn.close()


# Start Selenium scraper
def start_scraper():
    try:
        # Retrieve section and assignment numbers from GUI
        section = section_entry.get()
        assignment = assignment_entry.get()

        # Save updated defaults to the database
        save_settings(section, assignment)

        # Create the WebDriver
        driver = webdriver.Chrome()

        results = []

   
        students = [
            ("Budin, Daniel", '6818579'),
            ("Cabeza, Bella", '6818580'),
            ("Chan, Emma", '6818543'),
            ("Cheung, Anson", '6818592'),
            ("Chung, Abrianna", '6818833'),
            ("Dai, Suri", '6818487'),
            ("David, Victor", '6818583'),
            ("Day, Pierson", '6818540'),
            ("Hinners, Christopher", '6813954'),
            ("Iniguez, Alexander", '6818552'),
            ("Kacziba, Lilly", '6818548'),
            ("Khan, Mahdi", '6818551'),
            ("Kovacs, Maximillian", '6818550'),
            ("Lacourt, Lucas", '4174700'),
            ("Lombardo, Ryder", '6818593'),
            ("Martinez, Lukas Xavier", '6818873'),
            ("Morelli, Joseph", '6818874'),
            ("ODonohue, Daniel", '6818688'),
            ("Otolorin, Jordan", '6809053'),
            ("Pena, Eric", '6818591'),
            ("Perez, Kirstine", '6818549'),
            ("Pinlac, Ethan", '6818553'),
            ("Puracchio, Marek", '6818545'),
            ("Ramkirath, Ethan", '6818589'),
            ("Samaroo, Brandon", '6818546'),
            ("Sefaj, Emma", '6818564'),
            ("Sosa, Mauricio", '6818588'),
            ("Xiao, Matthew", '6818590'),
            ("Yao, Nicole", '6831630'),
            ("Zaheid, Sameera", '6810766'),
            ("Zamir, Jayden", '6806849'),
        ]


        # shorter list for test-purposes:
        """
        students = [
            ('Bazenikas, Alexandros', '5692079'),
            ('Beach, Matthew', '5692100'),
            ('Brahmachary, Aneek', '5692090'),
        ]
        """

        # Open CodeHS
        driver.get("https://codehs.com/login")
        driver.implicitly_wait(3)

        # Log in using credentials from 'secret' module
        driver.find_element(By.ID, "login-email").send_keys(usr)
        driver.find_element(By.ID, "login-password").send_keys(psw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)

        for student in students:
            s_name, s_nr = student
            driver.get(f"https://codehs.com/student/{s_nr}/section/{section}/assignment/{assignment}")
            driver.implicitly_wait(3)

            # Click "Test cases"
            driver.find_element(By.XPATH, "//a[normalize-space()='Test Cases']").click()
            time.sleep(6)
            driver.implicitly_wait(2)

            # Click "Check Code"
            driver.find_element(By.XPATH, "//button[normalize-space()='Check Code']").click()
            time.sleep(6)
            driver.implicitly_wait(2)
                   
            # Get score
            score = driver.find_element(By.XPATH, "//p[@id='score-text']").text

            # Save screenshot
            datetime_string = datetime.now().strftime("%Y_%m_%d--%H_%M_%S")

            filename = "screenshots/scrn_" + assignment + "_" + s_name.replace(" ","_") + "_" + datetime_string +".png"
            #filename = f"screenshots/scrn_{assignment}_{s_name.replace(' ', '_')}.jpg"
            driver.save_screenshot(filename)

            # Append results
            results.append((s_name, score))

        driver.quit()

        # Display results in the GUI
        for result in results:
            results_tree.insert("", tk.END, values=result)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# Tkinter GUI
root = tk.Tk()
root.title("CodeHS Scraper")

# Initialize database and fetch default settings
initialize_database()
default_section, default_assignment = get_default_settings()

# Frame for user input
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill=tk.X)

# Section field
tk.Label(frame, text="Section Number:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
section_entry = tk.Entry(frame, width=30)
section_entry.insert(0, default_section)  # Populate default value
section_entry.grid(row=0, column=1, padx=5, pady=5)

# Assignment field
tk.Label(frame, text="Assignment Number:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
assignment_entry = tk.Entry(frame, width=30)
assignment_entry.insert(0, default_assignment)  # Populate default value
assignment_entry.grid(row=1, column=1, padx=5, pady=5)

# Start button
start_button = tk.Button(frame, text="Start Scraper", command=start_scraper)
start_button.grid(row=2, column=0, columnspan=2, pady=10)

# Results table
results_frame = tk.Frame(root, padx=10, pady=10)
results_frame.pack(fill=tk.BOTH, expand=True)

columns = ("Name", "Score")
results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
results_tree.heading("Name", text="Student Name")
results_tree.heading("Score", text="Score")
results_tree.pack(fill=tk.BOTH, expand=True)

# Run the Tkinter main loop
root.mainloop()
