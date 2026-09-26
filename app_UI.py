import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import re
import csv
from tkinter import filedialog

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from secret import usr, psw  # your credentials


# ----------------------------
# SQLite: single, robust row (id=1)
# ----------------------------
# Keep the DB next to this script so settings persist regardless of the working directory
DB_PATH = Path(__file__).resolve().parent / "settings.db"

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        section TEXT NOT NULL,
        assignment TEXT NOT NULL
      )
    """)
    # Default to a CODING assignment id so "Check Code" exists out of the box
    # (Change these to whatever you need.)
    c.execute("""
      INSERT OR IGNORE INTO settings (id, section, assignment)
      VALUES (1, '779844', '193450569')
    """)
    conn.commit()
    conn.close()


def get_default_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT section, assignment FROM settings WHERE id = 1")
    row = c.fetchone()
    conn.close()
    return row


def save_settings(section, assignment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
      INSERT INTO settings (id, section, assignment)
      VALUES (1, ?, ?)
      ON CONFLICT(id) DO UPDATE SET section=excluded.section, assignment=excluded.assignment
    """, (section, assignment))
    conn.commit()
    conn.close()


# ----------------------------
# Utilities
# ----------------------------
def safe_name(s: str) -> str:
    # Keep letters/numbers/space/_/- ; replace others with "_", then swap spaces for underscores
    return re.sub(r"[^A-Za-z0-9 _-]", "_", s).replace(" ", "_")


def mk_screenshots_dir():
    Path("screenshots").mkdir(exist_ok=True)


# ----------------------------
# Selenium helpers
# ----------------------------
def make_driver(headless: bool = False):
    opts = Options()
    # Uncomment to run headless:
    # if headless:
    #     opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    return webdriver.Chrome(options=opts)


def login_codehs(driver, wait: WebDriverWait):
    driver.get("https://codehs.com/login")
    wait.until(EC.presence_of_element_located((By.ID, "login-email"))).send_keys(usr)
    driver.find_element(By.ID, "login-password").send_keys(psw)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    # Wait for any logged-in element (navbar)
    wait.until(EC.presence_of_element_located((By.ID, "logged-in-navbar")))


def navigate_to_assignment(driver, student_id: str, section: str, assignment: str):
    url = f"https://codehs.com/student/{student_id}/section/{section}/assignment/{assignment}"
    driver.get(url)


def extract_score_any_page(driver, wait: WebDriverWait) -> str:
    """
    Support both programming (with 'Check Code' + #score-text)
    and quiz pages (Score: X / Y).
    Returns a short string like '10/10', '2 / 2', or raw #score-text.
    """

    # Try the programming path first
    try:
        # "Check Code" might already be visible/clickable; if not, Timeout
        check_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(normalize-space(.), 'Check Code')]")
        ))
        check_btn.click()
        # #score-text shows a placeholder ("x/x") until the autograder finishes,
        # so wait until it contains an actual numeric score like "3/5"
        wait.until(EC.visibility_of_element_located((By.ID, "score-text")))
        try:
            WebDriverWait(driver, 60, ignored_exceptions=(StaleElementReferenceException,)).until(
                lambda d: re.search(r"\d+\s*/\s*\d+", d.find_element(By.ID, "score-text").text)
            )
        except TimeoutException:
            pass  # autograder never finished; report whatever is shown
        return driver.find_element(By.ID, "score-text").text.strip()
    except TimeoutException:
        # Fall back to quiz page parse (no "Check Code")
        pass

    # Quiz layout: "Score: <span class='num-correct'>2</span> / 2"
    try:
        container = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".stats-options-container .score-container")
        ))
        txt = container.text.strip()  # e.g., "Score: 2 / 2"
        # Extract the piece after "Score:" if present
        if "Score:" in txt:
            piece = txt.split("Score:", 1)[-1].strip()
            return piece  # e.g., "2 / 2"
        # Else return all text as last resort
        return txt
    except TimeoutException:
        # If neither worked, throw for caller
        raise TimeoutException("Could not detect programming or quiz score elements.")


# ----------------------------
# Main scraper (runs on a thread)
# ----------------------------
def start_scraper():
    driver = None
    try:
        # Read user inputs
        section = section_entry.get().strip()
        assignment = assignment_entry.get().strip()

        # Persist settings
        save_settings(section, assignment)

        # Ensure screenshots dir
        mk_screenshots_dir()

        # Create driver + waiter
        driver = make_driver(headless=False)
        wait = WebDriverWait(driver, 25)

        # Login
        login_codehs(driver, wait)

        # NOTE: the list uses "Last, First" for display in the results table,
        # but only student_id is needed for navigation.
        # IDs are synced to what you pasted from the live page.
        students = [
            ("Artemyev, Mason", '8012502'),
            ("Bhatti, Aydenviraj (Ayden)", '8032708'),
            ("Bifulco, Salvatore", '8012547'),
            ("Chaglla, Romina", '8012546'),
            ("Chen, Collin", '8012572'),
            ("Colin-Keita, Sophia", '8012544'),
            ("Gellineau, Joshua", '8012506'),
            ("Liu, Gongchen", '8012525'),
            ("Lo, James", '8012579'),
            ("Maingrette, Evan", '8012505'),
            ("Marina, Emma", '8012503'),
            ("McGuire, Aileen", '8005993'),
            ("Miazga, Christian", '8012578'),
            ("Nembhard, Michael (Mike)", '8012580'),
            ("Qirko, Alexander (Alex)", '8012508'),
            ("Ruiz, Conner", '8012575'),
            ("Sultan, Muhammad (Adam)", '8012509'),
            ("Valjato, Gregory", '8012573'),
            ("wagner, Robert", '8012519'),
            ("Weber, Valerie", '8012507'),
            ("Younggren, Ori", '8005992'),
                        
        ]

        # Clear previous results in UI
        for item in results_tree.get_children():
            results_tree.delete(item)

        # Iterate students
        for display_name, sid in students:
            try:
                navigate_to_assignment(driver, sid, section, assignment)
                score = extract_score_any_page(driver, wait)

                # Screenshot
                ts = datetime.now().strftime("%Y_%m_%d--%H_%M_%S")
                fname = f"screenshots/scrn_{assignment}_{safe_name(display_name)}_{ts}.png"
                driver.save_screenshot(fname)

                # Stream result to UI (from worker thread). Use tag for alternating rows.
                def insert_row(n=display_name, s=score):
                    idx = len(results_tree.get_children())
                    tag = "even" if idx % 2 == 0 else "odd"
                    results_tree.insert("", tk.END, values=(n, s), tags=(tag,))
                root.after(0, insert_row)

            except Exception as per_student_err:
                # Still insert a row so you know who failed
                msg = f"ERROR: {per_student_err}"
                def insert_err_row(n=display_name, s=msg):
                    idx = len(results_tree.get_children())
                    tag = "even" if idx % 2 == 0 else "odd"
                    results_tree.insert("", tk.END, values=(n, s), tags=(tag,))
                root.after(0, insert_err_row)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        # Re-enable the button
        start_button.config(state="normal")


def start_scraper_threaded():
    start_button.config(state="disabled")
    t = threading.Thread(target=start_scraper, daemon=True)
    t.start()


def print_results_to_console():
    import re
    print("Student Name\tScore")
    for item in results_tree.get_children():
        name, score = results_tree.item(item, "values")
        if score is None:
            out_score = ""
        else:
            s = str(score).strip()
            if '/' in s:
                out_score = s.split('/', 1)[0].strip()
            else:
                m = re.search(r'(\d+(?:\.\d+)?)', s)
                out_score = m.group(1) if m else s
        print(f"{name},\t{out_score}")


def save_results_csv():
    # Gather rows
    rows = []
    for item in results_tree.get_children():
        name, score = results_tree.item(item, "values")
        s = "" if score is None else str(score).strip()
        # strip "/total" if present
        if '/' in s:
            s = s.split('/', 1)[0].strip()
        rows.append((name, s))

    if not rows:
        messagebox.showinfo("Save CSV", "No results to save.")
        return

    assign = assignment_entry.get().strip() or "assignment"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"codehs_results_{assign}_{ts}.csv"
    path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name,
                                        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if not path:
        return

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Student Name", "Score"])
            writer.writerows(rows)
        messagebox.showinfo("Save CSV", f"Saved {len(rows)} rows to:\n{path}")
    except Exception as e:
        messagebox.showerror("Save CSV", f"Failed to save CSV: {e}")


# ----------------------------
# Tkinter UI
# ----------------------------
root = tk.Tk()
root.title("CodeHS Scraper")
root.geometry("720x520")
root.minsize(640, 420)

# Improve look & feel
style = ttk.Style(root)
try:
    style.theme_use("clam")
except Exception:
    pass
style.configure("TButton", padding=6)
style.configure("TLabel", padding=4)
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
style.configure("Treeview", rowheight=22, font=("Segoe UI", 10))

initialize_database()
default_section, default_assignment = get_default_settings()

frame = ttk.Frame(root, padding=12)
frame.pack(fill=tk.X)

ttk.Label(frame, text="Section Number:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
section_entry = ttk.Entry(frame, width=30)
section_entry.insert(0, default_section)
section_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(frame, text="Assignment Number:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
assignment_entry = ttk.Entry(frame, width=30)
assignment_entry.insert(0, default_assignment)
assignment_entry.grid(row=1, column=1, padx=5, pady=5)

btn_row = ttk.Frame(frame)
btn_row.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.EW)

start_button = ttk.Button(btn_row, text="Start Scraper", command=start_scraper_threaded)
start_button.pack(side=tk.LEFT, padx=6)

print_button = ttk.Button(btn_row, text="Print Results to Console", command=print_results_to_console)
print_button.pack(side=tk.LEFT, padx=6)

save_csv_button = ttk.Button(btn_row, text="Save CSV", command=save_results_csv)
save_csv_button.pack(side=tk.LEFT, padx=6)


def on_close():
    # Remember the last-entered section/assignment even if the scraper was never started
    try:
        save_settings(section_entry.get().strip(), assignment_entry.get().strip())
    finally:
        root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

results_frame = ttk.Frame(root, padding=10)
results_frame.pack(fill=tk.BOTH, expand=True)

columns = ("Name", "Score")
results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="browse")
results_tree.heading("Name", text="Student Name")
results_tree.heading("Score", text="Score")
results_tree.column("Name", width=420, anchor=tk.W)
results_tree.column("Score", width=120, anchor=tk.CENTER)

# Alternating row colors
results_tree.tag_configure('odd', background='#ffffff')
results_tree.tag_configure('even', background='#f6f8ff')

# Add vertical scrollbar
vsb = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_tree.yview)
results_tree.configure(yscrollcommand=vsb.set)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
results_tree.pack(fill=tk.BOTH, expand=True)

root.mainloop()
