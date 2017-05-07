import sqlite3
import os
import shutil
from tkinter import messagebox

if os.path.isfile("personalNotes.db"):
    shutil.copyfile("personalNotes.db", "tempDB.db")
    connection = sqlite3.connect("tempDB.db")
else:
    connection = sqlite3.connect("personalNotes.db")
    shutil.copyfile("personalNotes.db", "tempDB.db")
    connection = sqlite3.connect("tempDB.db")

cursor = connection.cursor()

initial_db_setup_step_one = """
CREATE TABLE IF NOT EXISTS subjects(
subject_name TEXT PRIMARY KEY,
notes TEXT
)
"""

initial_db_setup_step_two = """
CREATE TABLE IF NOT EXISTS documentation(
guide_id INTEGER PRIMARY KEY AUTOINCREMENT,
subject TEXT,
name TEXT,
type TEXT,
link TEXT
)
"""

initial_db_setup_step_three = """
INSERT INTO subjects (subject_name, notes)
SELECT 'Other', ' '
WHERE NOT EXISTS (SELECT * FROM subjects WHERE subject_name = 'Other')
"""

cursor.execute(initial_db_setup_step_one)
cursor.execute(initial_db_setup_step_two)
cursor.execute(initial_db_setup_step_three)
connection.commit()


def check_if_record_name_exists(record_name):
    cursor.execute("SELECT subject_name FROM subjects WHERE subject_name = ?", (record_name,))
    if cursor.fetchall():
        return True
    else:
        return False


def convert_doc_type(doc_type):
    if doc_type == "Link to Local File" or doc_type == "document":
        return "document"
    else:
        return "url"


def add_record(record_name, list_of_record_links, record_notes):
    if not check_if_record_name_exists(record_name):
        cursor.execute("INSERT INTO subjects (subject_name, notes) VALUES (?,?)", (record_name, record_notes))
        connection.commit()
        for eachLink in list_of_record_links:
            doc_name, doc_type, doc_url = eachLink
            doc_type = convert_doc_type(doc_type)
            cursor.execute("INSERT INTO documentation (subject, name, type, link) VALUES (?,?,?,?)",
                           (record_name, doc_name, doc_type, doc_url))
            connection.commit()
    else:
        messagebox.showerror("Contract Already Exists", "A subject named " + str(record_name) + " already exists!\n" +
                             "Use 'Edit Record' to change existing entries.")


def update_record(record_name, record_notes):
    cursor.execute('''UPDATE subjects
                   SET notes = ?
                   WHERE subject_name = ?''',
                   (record_notes, record_name))
    connection.commit()


def update_documentation(list_of_documentation_edits):
    for eachItem in list_of_documentation_edits:
        guide_id, doc_name, doc_type, doc_url = eachItem
        if guide_id:
            doc_type = convert_doc_type(doc_type)
            cursor.execute('''UPDATE documentation
                           SET name = ?, type = ?, link = ?
                           WHERE guide_id = ?''',
                           (doc_name, doc_type, doc_url, guide_id))
            connection.commit()


def delete_documentation(list_of_docs_to_delete):
    for eachItem in list_of_docs_to_delete:
        guide_id, doc_name, doc_type, doc_url = eachItem
        cursor.execute("DELETE FROM documentation WHERE guide_id = ?", (guide_id,))


def add_new_documentation(list_of_docs_to_add, subject_name):
    for eachItem in list_of_docs_to_add:
        guide_id, doc_name, doc_type, doc_url = eachItem
        doc_type = convert_doc_type(doc_type)
        cursor.execute("INSERT INTO documentation (subject, name, type, link) VALUES (?,?,?,?)",
                       (subject_name, doc_name, doc_type, doc_url))
        connection.commit()


def delete_entire_record(subject_name):
    cursor.execute("DELETE FROM subjects WHERE subject_name = ?", (subject_name,))
    connection.commit()
    cursor.execute("DELETE FROM documentation WHERE subject = ?", (subject_name,))
    connection.commit()
