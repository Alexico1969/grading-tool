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
NUM_ASSIGNMENTS = 4
# Columns for assignments 2..4 (assignment 1 uses the original "assignment" column)
EXTRA_ASSIGNMENT_COLS = [f"assignment{i}" for i in range(2, NUM_ASSIGNMENTS + 1)]

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
    # Migrate older DBs: add columns for the extra assignment fields if missing
    existing = {row[1] for row in c.execute("PRAGMA table_info(settings)")}
    for col in EXTRA_ASSIGNMENT_COLS:
        if col not in existing:
            c.execute(f"ALTER TABLE settings ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.close()


def get_default_settings():
    """Returns (section, [assignment1, ..., assignment4])."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cols = ", ".join(["section", "assignment"] + EXTRA_ASSIGNMENT_COLS)
    c.execute(f"SELECT {cols} FROM settings WHERE id = 1")
    row = c.fetchone()
    conn.close()
    return row[0], list(row[1:])


def save_settings(section, assignments):
    """assignments: list of NUM_ASSIGNMENTS strings (empty string = unused field)."""
    cols = ["section", "assignment"] + EXTRA_ASSIGNMENT_COLS
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""
      INSERT INTO settings (id, {", ".join(cols)})
      VALUES (1, {", ".join("?" for _ in cols)})
      ON CONFLICT(id) DO UPDATE SET {", ".join(f"{col}=excluded.{col}" for col in cols)}
    """, (section, *assignments))
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
# Rosters (one per class; pick with the buttons at the top of the window)
# ----------------------------
# NOTE: the lists use "Last, First" for display in the results table,
# but only student_id is needed for navigation.
# IDs are synced to what you pasted from the live page.
ROSTERS = {
    "APCSP": [
        ("Artemyev, Mason", '8012502'),
        ("Bhatti, Aydenviraj (Ayden)", '8032708'),
        ("Bifulco, Salvatore", '8012547'),
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
    ],
    # TODO: replace the '000' placeholders with the real CodeHS student IDs
    "AP Cyber": [
        ("Bajrami, Joey", '8005977'),
        ("Barros-Devine, Gabriella", '8005996'),
        ("Camacho, Ariel-Chloe", '8006095'),
        ("Dang, Zoey", '8005991'),
        ("Galante, Valentina", '8005981'),
        ("Gomez, Owen", '8005984'),
        ("Gudur, Rachel", '8005986'),
        ("Lombardo, Jack", '8005983'),
        ("Luongo, Rocco", '8005995'),
        ("Manniram, Ash", '8005980'),
        ("McGuire, Aileen", '8005993'),
        ("Musse, Michelle", '8006001'),
        ("O'Donohue, Daniel", '6818688'),
        ("Ramcharran, Riley", '8005979'),
        ("Singh, Abhay", '8005994'),
        ("Suarez, Lizeth", '8005987'),
        ("Walsh, James", '8005985'),
        ("You, Ben", '8006044'),
        ("Younggren, Ori", '8005992'),
    ],
}
DEFAULT_CLASS = "APCSP"

# CodeHS section ID for each class; picking a class fills the Section field with it
SECTIONS = {
    "APCSP": "918751",
    "AP Cyber": "912294",
}


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


def extract_score_any_page(driver, wait: WebDriverWait) -> tuple[str, bool]:
    """
    Support programming (with 'Check Code' + #score-text), quiz (Score: X / Y),
    and written-response pages (status badge only).
    Returns (score, is_written_response), e.g. ('10/10', False) or ('Submitted', True).
    """

    # CodeHS shows a "This page not found." dog page for a bad student/section/assignment combo
    if "page not found" in driver.page_source.lower():
        raise TimeoutException("Page not found - check the assignment ID for this section.")

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
        return driver.find_element(By.ID, "score-text").text.strip(), False
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
            return piece, False  # e.g., "2 / 2"
        # Else return all text as last resort
        return txt, False
    except TimeoutException:
        pass

    # Free-response page (e.g. AP Cyber written tasks): no auto score, only a
    # "Status: Submitted" badge. Report the status without a number, so the CSV
    # export doesn't mistake the "5 points" (points possible) badge for a score.
    badges = driver.find_elements(By.XPATH, "//*[not(*) and starts-with(normalize-space(.), 'Status:')]")
    if badges:
        return badges[0].text.split("Status:", 1)[-1].strip(), True  # e.g. "Submitted"

    raise TimeoutException("Could not detect programming, quiz, or status elements.")


# ----------------------------
# Main scraper (runs on a thread)
# ----------------------------
# Set by the Stop button; the worker checks it between students/assignments
stop_event = threading.Event()
# The worker's browser, so Stop can close it and interrupt a long wait
active_driver = None


def start_scraper(section, assignments, students):
    global active_driver
    driver = None
    try:
        # Ensure screenshots dir
        mk_screenshots_dir()

        # Create driver + waiter
        driver = make_driver(headless=False)
        active_driver = driver
        if stop_event.is_set():
            return
        wait = WebDriverWait(driver, 25)

        # Login
        login_codehs(driver, wait)


        # Iterate students; one row per student with one score per assignment
        for display_name, sid in students:
            if stop_event.is_set():
                break
            scores = []
            for assignment in assignments:
                if stop_event.is_set():
                    break
                try:
                    navigate_to_assignment(driver, sid, section, assignment)
                    score, is_written = extract_score_any_page(driver, wait)
                    scores.append(score)

                    # Screenshot
                    ts = datetime.now().strftime("%Y_%m_%d--%H_%M_%S")
                    if is_written:
                        # Written responses get their own folder named after the assignment,
                        # taken from the tab title ("Identify Risks | CodeHS")
                        title = driver.title.split("|", 1)[0].strip() or assignment
                        folder = Path("screenshots") / safe_name(title)
                        folder.mkdir(parents=True, exist_ok=True)
                        fname = str(folder / f"{safe_name(display_name)}_{ts}.png")
                    else:
                        fname = f"screenshots/scrn_{assignment}_{safe_name(display_name)}_{ts}.png"
                    driver.save_screenshot(fname)
                except Exception as per_assignment_err:
                    if stop_event.is_set():
                        break  # error came from Stop closing the browser
                    # Still record the cell so you know what failed
                    scores.append(f"ERROR: {per_assignment_err}")

            # Don't add a half-finished row for the student we stopped on
            if stop_event.is_set():
                break

            # Stream result to UI (from worker thread). Use tag for alternating rows.
            def insert_row(n=display_name, s=tuple(scores)):
                idx = len(results_tree.get_children())
                tag = "even" if idx % 2 == 0 else "odd"
                results_tree.insert("", tk.END, values=(n, *s), tags=(tag,))
            root.after(0, insert_row)

    except Exception as e:
        if not stop_event.is_set():
            messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        active_driver = None
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        # Re-enable Start, disable Stop
        def reset_buttons():
            start_button.config(state="normal")
            stop_button.config(state="disabled")
        root.after(0, reset_buttons)


def stop_scraper():
    """Stop the running scrape; results gathered so far stay in the table."""
    stop_event.set()
    stop_button.config(state="disabled")
    driver = active_driver
    if driver:
        # quit() can take a few seconds, so keep it off the UI thread
        threading.Thread(target=lambda: driver.quit(), daemon=True).start()


def get_assignment_inputs():
    """Raw text of all assignment fields (empty strings kept, so positions persist)."""
    return [e.get().strip() for e in assignment_entries]


def configure_result_columns(assignments):
    """One 'Name' column plus one score column per assignment (heading = assignment id)."""
    score_cols = [f"A{i}" for i in range(len(assignments))]
    results_tree["columns"] = ("Name", *score_cols)
    results_tree.heading("Name", text="Student Name")
    results_tree.column("Name", width=260, anchor=tk.W)
    for col, assignment in zip(score_cols, assignments):
        results_tree.heading(col, text=assignment)
        results_tree.column(col, width=110, anchor=tk.CENTER)


def start_scraper_threaded():
    section = section_entry.get().strip()
    raw_assignments = get_assignment_inputs()
    save_settings(section, raw_assignments)

    # Empty fields are ignored
    assignments = [a for a in raw_assignments if a]
    if not assignments:
        messagebox.showwarning("Start Scraper", "Enter at least one assignment number.")
        return

    # Clear previous results and set up one score column per assignment
    for item in results_tree.get_children():
        results_tree.delete(item)
    configure_result_columns(assignments)

    stop_event.clear()
    start_button.config(state="disabled")
    stop_button.config(state="normal")
    students = list(ROSTERS[current_class.get()])
    t = threading.Thread(target=start_scraper, args=(section, assignments, students), daemon=True)
    t.start()


def print_results_to_console():
    import re
    headings = [results_tree.heading(col, "text") for col in results_tree["columns"]]
    print("\t".join(headings))
    for item in results_tree.get_children():
        name, *scores = results_tree.item(item, "values")
        out_scores = []
        for score in scores:
            s = str(score).strip()
            if '/' in s:
                out_scores.append(s.split('/', 1)[0].strip())
            else:
                m = re.search(r'(\d+(?:\.\d+)?)', s)
                out_scores.append(m.group(1) if m else s)
        print(f"{name},\t" + ",\t".join(out_scores))


def save_results_csv():
    # Gather rows
    rows = []
    for item in results_tree.get_children():
        name, *scores = results_tree.item(item, "values")
        out_scores = []
        for score in scores:
            s = str(score).strip()
            # strip "/total" if present
            if '/' in s:
                s = s.split('/', 1)[0].strip()
            out_scores.append(s)
        rows.append((name, *out_scores))

    if not rows:
        messagebox.showinfo("Save CSV", "No results to save.")
        return

    headings = [results_tree.heading(col, "text") for col in results_tree["columns"]]
    assign = "_".join(headings[1:]) or "assignment"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"codehs_results_{assign}_{ts}.csv"
    path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name,
                                        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if not path:
        return

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Student Name", *headings[1:]])
            writer.writerows(rows)
        messagebox.showinfo("Save CSV", f"Saved {len(rows)} rows to:\n{path}")
    except Exception as e:
        messagebox.showerror("Save CSV", f"Failed to save CSV: {e}")


# ----------------------------
# Tkinter UI
# ----------------------------
root = tk.Tk()
root.title("CodeHS Scraper")
root.geometry("820x640")
root.minsize(700, 540)

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
saved_section, default_assignments = get_default_settings()
# Reopen on the class used last time (its section is what was saved), so saved
# assignment IDs aren't run against the wrong class
initial_class = next((cls for cls, sec in SECTIONS.items() if sec == saved_section), DEFAULT_CLASS)

# Class selector: picks which roster the scraper uses
style.configure("Class.Toolbutton", padding=(16, 6), font=("Segoe UI", 10, "bold"))
style.map("Class.Toolbutton", background=[("selected", "#4a6fd1")], foreground=[("selected", "#ffffff")])

current_class = tk.StringVar(value=initial_class)
class_bar = ttk.Frame(root, padding=(12, 12, 12, 0))
class_bar.pack(fill=tk.X)


def on_class_change():
    cls = current_class.get()
    class_label.config(text=f"{len(ROSTERS[cls])} students")
    section_entry.delete(0, tk.END)
    section_entry.insert(0, SECTIONS[cls])


for class_name in ROSTERS:
    ttk.Radiobutton(class_bar, text=class_name, value=class_name, variable=current_class,
                    style="Class.Toolbutton", command=on_class_change).pack(side=tk.LEFT, padx=(0, 6))
class_label = ttk.Label(class_bar)
class_label.pack(side=tk.LEFT, padx=6)

frame = ttk.Frame(root, padding=12)
frame.pack(fill=tk.X)

ttk.Label(frame, text="Section Number:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
section_entry = ttk.Entry(frame, width=30)
section_entry.grid(row=0, column=1, padx=5, pady=5)
on_class_change()

assignment_entries = []
for i, default_assignment in enumerate(default_assignments):
    ttk.Label(frame, text=f"Assignment Number {i + 1}:").grid(row=i + 1, column=0, sticky=tk.W, padx=5, pady=5)
    entry = ttk.Entry(frame, width=30)
    entry.insert(0, default_assignment)
    entry.grid(row=i + 1, column=1, padx=5, pady=5)
    assignment_entries.append(entry)

btn_row = ttk.Frame(frame)
btn_row.grid(row=NUM_ASSIGNMENTS + 1, column=0, columnspan=2, pady=10, sticky=tk.EW)

start_button = ttk.Button(btn_row, text="Start Scraper", command=start_scraper_threaded)
start_button.pack(side=tk.LEFT, padx=6)

print_button = ttk.Button(btn_row, text="Print Results to Console", command=print_results_to_console)
print_button.pack(side=tk.LEFT, padx=6)

save_csv_button = ttk.Button(btn_row, text="Save CSV", command=save_results_csv)
save_csv_button.pack(side=tk.LEFT, padx=6)

stop_button = ttk.Button(btn_row, text="Stop", command=stop_scraper, state="disabled")
stop_button.pack(side=tk.LEFT, padx=6)


def on_close():
    # Remember the last-entered section/assignment even if the scraper was never started
    try:
        save_settings(section_entry.get().strip(), get_assignment_inputs())
    finally:
        root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

results_frame = ttk.Frame(root, padding=10)
results_frame.pack(fill=tk.BOTH, expand=True)

results_tree = ttk.Treeview(results_frame, show="headings", selectmode="browse")
configure_result_columns([a for a in default_assignments if a] or ["Score"])

# Alternating row colors
results_tree.tag_configure('odd', background='#ffffff')
results_tree.tag_configure('even', background='#f6f8ff')

# Add vertical scrollbar
vsb = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_tree.yview)
results_tree.configure(yscrollcommand=vsb.set)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
results_tree.pack(fill=tk.BOTH, expand=True)

root.mainloop()
