"""
Download each student's code for one CodeHS assignment and save it as
<First>_<Last>.txt in student_code/<assignment>/.

The roster is read straight from the `ROSTERS` dict in app_UI.py,
so there is only one list to update each school year.
"""
import ast
import re
import sqlite3
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from secret import usr, psw  # your credentials

ASSIGNMENT = "237486312"
CLASS_NAME = "APCSP"  # key in app_UI.ROSTERS

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "settings.db"
OUT_DIR = HERE / "student_code" / ASSIGNMENT


# ----------------------------
# Roster / settings
# ----------------------------
def load_students():
    """Return ROSTERS[CLASS_NAME] from app_UI.py as [(\"Last, First\", id), ...]."""
    tree = ast.parse((HERE / "app_UI.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "ROSTERS" for t in node.targets)):
            return ast.literal_eval(node.value)[CLASS_NAME]
    raise RuntimeError("Could not find the `ROSTERS` dict in app_UI.py")


def load_section():
    """Last section used in app_UI.py (stored in settings.db)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute("SELECT section FROM settings WHERE id = 1").fetchone()[0]
    finally:
        conn.close()


def file_name_for(display_name: str) -> str:
    """'Bhatti, Aydenviraj (Ayden)' -> 'Aydenviraj_Bhatti.txt'"""
    last, _, first = display_name.partition(",")
    first = re.sub(r"\(.*?\)", "", first)  # drop nicknames in parentheses
    name = f"{first.strip()} {last.strip()}"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") + ".txt"


# ----------------------------
# Selenium helpers (same login as app_UI.py)
# ----------------------------
def make_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    return webdriver.Chrome(options=opts)


def login_codehs(driver, wait: WebDriverWait):
    driver.get("https://codehs.com/login")
    wait.until(EC.presence_of_element_located((By.ID, "login-email"))).send_keys(usr)
    driver.find_element(By.ID, "login-password").send_keys(psw)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    wait.until(EC.presence_of_element_located((By.ID, "logged-in-navbar")))


# Reads the full text of every code editor on the page. Editor widgets only
# render the visible lines in the DOM, so ask the editor's own API instead.
# Covers Ace, Monaco, CodeMirror 6 and CodeMirror 5. Returns [] if none loaded yet.
GET_CODE_JS = r"""
const out = [];
if (window.ace) {
    document.querySelectorAll('.ace_editor').forEach(el => {
        try { out.push(ace.edit(el).getValue()); } catch (e) {}
    });
}
if (!out.length && window.monaco && monaco.editor) {
    monaco.editor.getModels().forEach(m => out.push(m.getValue()));
}
if (!out.length) {
    document.querySelectorAll('.cm-content').forEach(el => {
        const view = el.cmView && el.cmView.view;
        if (view) out.push(view.state.doc.toString());
    });
}
if (!out.length) {
    document.querySelectorAll('.CodeMirror').forEach(el => {
        if (el.CodeMirror) out.push(el.CodeMirror.getValue());
    });
}
return out;
"""


def extract_code(driver, timeout=25) -> str:
    try:
        parts = WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(GET_CODE_JS) or False
        )
    except TimeoutException:
        raise TimeoutException("No code editor found on the page.")
    return "\n\n".join(parts)


# ----------------------------
# Main
# ----------------------------
def main():
    students = load_students()
    section = load_section()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Section {section}, assignment {ASSIGNMENT}, {len(students)} students -> {OUT_DIR}")

    driver = make_driver()
    try:
        wait = WebDriverWait(driver, 25)
        login_codehs(driver, wait)

        failed = []
        for display_name, sid in students:
            url = f"https://codehs.com/student/{sid}/section/{section}/assignment/{ASSIGNMENT}"
            try:
                driver.get(url)
                code = extract_code(driver)
                path = OUT_DIR / file_name_for(display_name)
                path.write_text(code, encoding="utf-8")
                print(f"OK     {display_name} -> {path.name} ({len(code)} chars)")
            except Exception as e:
                failed.append(display_name)
                print(f"ERROR  {display_name}: {e}")

        print(f"\nDone: {len(students) - len(failed)} saved, {len(failed)} failed.")
        for name in failed:
            print(f"  failed: {name}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
