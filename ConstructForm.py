import tkinter
from tkinter import ttk
from tkinter import *
from tkinter import messagebox
import shutil
import os
import webbrowser
import subprocess
import EditRecords

connection = EditRecords.connection
cursor = EditRecords.cursor

root = tkinter.Tk()

root.resizable(height=False, width=False)
root.wm_title("Personal Notepad")

notePage = ttk.Notebook(root)

combobox_selection = StringVar()
subject_label_text = StringVar()
previous_window_count = 0

subject_label_text.set("")
notes_content = ""

list_of_doc_links = []
list_of_use_links = []
list_of_link_types = ["Link to Local File", "Link to Web Address"]
list_of_subjects_pending_deletion = []

list_of_sub_forms = []


subject_name_frame = LabelFrame(root, text="Subject:")
notes_text_box_frame = LabelFrame(root, text="Notes:", width=500)
documentation_frame = LabelFrame(root, text="Documentation:")
useful_links_frame = LabelFrame(root, text="Useful Links:")

scrollbar = Scrollbar(notes_text_box_frame)

subject_name_label = Label(subject_name_frame, textvariable=subject_label_text)
notes_text_box = Text(notes_text_box_frame, height=20, width=50, yscrollcommand=scrollbar.set)
subject_selection_combo_box = ttk.Combobox(root, textvariable=combobox_selection, state="readonly")


def populate_subject_list(db_cursor):
    db_cursor.execute("SELECT subject_name FROM subjects")
    temp_list = db_cursor.fetchall()
    for i in range(len(temp_list)):
        temp_list[i] = str(temp_list[i])[2:-3]
        if temp_list[i] in list_of_subjects_pending_deletion:
            temp_list.pop(i)
    temp_list = sorted(temp_list)
    temp_list.append(temp_list.pop(temp_list.index("Other")))  # Moves "Other" to end of sorted list
    return temp_list


def populate_notes_text_box(db_cursor, subject_name):
    db_cursor.execute("SELECT notes FROM subjects WHERE subject_name = ?", (subject_name,))
    new_string = str(db_cursor.fetchone())[2:-3].replace(r"\n", "\n")  # SQL returns line breaks as '\n', this fixes it
    return new_string


def obtain_list_of_documentation(dbcursor, subject_name):
    dbcursor.execute("SELECT name, link FROM documentation WHERE type IS 'document' AND subject = ?", (subject_name,))
    list_of_documentation = dbcursor.fetchall()
    return list_of_documentation


def obtain_list_of_useful_links(dbcursor, subject_name):
    dbcursor.execute("SELECT name, link FROM documentation WHERE type IS 'url' AND subject = ?", (subject_name,))
    list_of_useful_links = dbcursor.fetchall()
    return list_of_useful_links


def open_link(link):
    list_of_web_address_indicators = ["http", ".com", ".net", ".co.", ".gov", ".org", ".biz", ".info"]
    for eachIndicator in list_of_web_address_indicators:
        if eachIndicator in link:
            webbrowser.open_new(link)
            return
    subprocess.Popen("explorer " + link)


def populate_documentation_frame(list_of_documentation):
    global list_of_doc_links
    if list_of_documentation:
        for eachTuple in list_of_documentation:
            name, url = eachTuple
            link = Label(documentation_frame, text=name, foreground="#0000FF")
            link.bind("<Enter>", lambda event, current_link=link: current_link.config(foreground="#FF0000"))
            link.bind("<Leave>", lambda event, current_link=link: current_link.config(foreground="#0000FF"))
            link.bind("<1>", lambda event, current_url=url: open_link(current_url))
            link.pack()
            list_of_doc_links.append(link)
    else:
        blank_link = Label(documentation_frame, text="None")
        blank_link.pack()
        list_of_doc_links.append(blank_link)


def populate_useful_links_frame(list_of_useful_links):
    global list_of_use_links
    if list_of_useful_links:
        for eachTuple in list_of_useful_links:
            name, url = eachTuple
            link = Label(useful_links_frame, text=name, foreground="#0000FF")
            link.bind("<Enter>", lambda event, current_link=link: current_link.config(foreground="#FF0000"))
            link.bind("<Leave>", lambda event, current_link=link: current_link.config(foreground="#0000FF"))
            link.bind("<1>", lambda event, current_url=url: open_link(current_url))
            link.pack()
            list_of_doc_links.append(link)
    else:
        blank_link = Label(useful_links_frame, text="None")
        blank_link.pack()
        list_of_use_links.append(blank_link)


def depopulate_documentation_frame():
    global list_of_doc_links
    for eachLink in list_of_doc_links:
        eachLink.destroy()
    list_of_doc_links = []


def depopulate_useful_links_frame():
    global list_of_use_links
    for eachLink in list_of_use_links:
        eachLink.destroy()
    list_of_use_links = []


def update_notes_content(db_cursor, subject_name):
    global notes_content
    notes_content = populate_notes_text_box(db_cursor, subject_name)


def get_notes_from_text_box(text_box):
    return text_box.get("1.0", "end-1c")


def set_prev_label(current_label_text):
    global prev_label_text
    prev_label_text = current_label_text


def set_label_text(new_text):
    global subject_label_text
    subject_label_text.set(new_text)


def save_notes(db_cursor, db_connection, notes_to_save, subject_to_update):
    db_cursor.execute("UPDATE subjects SET notes = ? WHERE subject_name = ?", (notes_to_save, subject_to_update))
    db_connection.commit()


def confirm_save():
    if messagebox.askyesno("Save Changes?", "Would you like to save your changes?"):
        save_notes(cursor, connection, get_notes_from_text_box(notes_text_box), subject_label_text.get())
        connection.close()
        shutil.copyfile("tempDB.db", "personalNotes.db")
        os.remove("tempDB.db")
        for eachForm in list_of_sub_forms:
            eachForm.destroy()
        root.destroy()
    else:
        connection.close()
        os.remove("tempDB.db")
        for eachForm in list_of_sub_forms:
            eachForm.destroy()
        root.destroy()


def add_doc_link_to_list(doc_name, doc_type, doc_url, list_of_links_to_add, is_edit_bool):
    if is_edit_bool:
        list_of_links_to_add.append((None, doc_name, doc_type, doc_url))
    else:
        list_of_links_to_add.append((doc_name, doc_type, doc_url))


def populate_list_of_links_to_add_box(listbox, list_of_links_to_add, is_edit_bool):
    listbox.delete(0, END)
    for eachLink in list_of_links_to_add:
        if is_edit_bool:
            guide_id, doc_name, doc_type, doc_url = eachLink
        else:
            doc_name, doc_type, doc_url = eachLink
        if doc_type == "Link to Local File" or doc_type == "document":
            listbox.insert(END, (doc_name + " (File)"))
        else:
            listbox.insert(END, (doc_name + " (Web)"))


def obtain_list_of_links_to_edit(subject_name):
    cursor.execute("SELECT guide_id, name, type, link FROM documentation WHERE subject = ?", (subject_name,))
    list_to_return = cursor.fetchall()
    return list_to_return


def get_name_of_document_selection(list_of_links, index_to_print):
    guide_id, doc_name, doc_type, doc_url = list_of_links[index_to_print]
    return doc_name


def get_type_of_document_selection(list_of_links, index_to_print):
    guide_id, doc_name, doc_type, doc_url = list_of_links[index_to_print]
    if doc_type == "Link to Local File" or doc_type == "document":
        return "Link to Local File"
    else:
        return "Link to Web Address"


def get_url_of_document_selection(list_of_links, index_to_print):
    guide_id, doc_name, doc_type, doc_url = list_of_links[index_to_print]
    return doc_url


def edit_link_save(temp_list, list_index, doc_name, doc_type, doc_url):
    current_guide_id, current_name, current_type, current_url = temp_list[list_index]
    temp_list[list_index] = (current_guide_id, doc_name, doc_type, doc_url)


def clear_add_link_entry_boxes(doc_name_entry, doc_url_entry, doc_type_entry):
    doc_name_entry.delete(0, END)
    doc_url_entry.delete(0, END)
    doc_type_entry.set("")


def check_for_empty_fields(doc_name, doc_url, doc_type):
    if doc_name.replace(" ", "") == "" or doc_url.replace(" ", "") == "" or doc_type == "":
        messagebox.showerror("Blank Field Detected", "You must fill out all fields before saving a link.")
        return False
    else:
        return True


def check_for_empty_subject_name(subject_name):
    if subject_name.replace(" ", "") == "":
        messagebox.showerror("No Subject Name", "You must add a subject name before saving.")
        return False
    else:
        return True


def confirm_delete_link(link_name):
    if messagebox.askyesno("Confirm Deletion", "Delete link to " + link_name + "?"):
        return True
    else:
        return False


def delete_subject(subject_name):
    if subject_name == "Other":
        messagebox.showinfo('Cannot Delete "Other"', '"Other" is used to store information not associated with\n' +
                            'any current subject. It cannot be deleted.')
        return False
    else:
        if messagebox.askyesno("Confirm Deletion", "Once changes are saved this action cannot be reversed.\n" +
                               "All data for this subject will be lost. Continue?"):
            EditRecords.delete_entire_record(subject_name)
            list_of_subjects_pending_deletion.append(subject_name)
            return True
        else:
            return False


def close_delete_window(bool_value, delete_window_form):
    if bool_value:
        list_of_sub_forms.remove(delete_window_form)
        delete_window_form.destroy()
    else:
        delete_window_form.lift()


def update_ui():

        subject_selection_combo_box['values'] = populate_subject_list(cursor)

        depopulate_documentation_frame()
        depopulate_useful_links_frame()
        '''
        save_notes(cursor, connection,
                   get_notes_from_text_box(notes_text_box),
                   subject_label_text.get())
                   '''
        notes_text_box.delete("1.0", END)
        set_label_text(combobox_selection.get())
        populate_documentation_frame(obtain_list_of_documentation(cursor,
                                     subject_label_text.get()))
        populate_useful_links_frame(obtain_list_of_useful_links(cursor,
                                    subject_label_text.get()))
        update_notes_content(cursor, combobox_selection.get())
        notes_text_box.insert(END, notes_content)


def construct_form(db_cursor, db_connection):
    subject_list = populate_subject_list(db_cursor)

    subject_name_frame.grid(row=0, column=0, sticky=W+E, padx=4)
    documentation_frame.grid(row=1, column=0, sticky=N+S+W+E, padx=4)
    useful_links_frame.grid(row=1, column=1, sticky=N+S+W+E, padx=4)
    notes_text_box_frame.grid(row=2, column=0, columnspan=2, padx=4, pady=2)

    subject_name_label.pack()
    subject_label_text.set("Other")

    scrollbar.pack(side=RIGHT, fill=Y)
    notes_text_box.pack()
    scrollbar.config(command=notes_text_box.yview)

    subject_selection_combo_box['values'] = subject_list
    subject_selection_combo_box.set("Other")
    subject_selection_combo_box.bind('<<ComboboxSelected>>',
                                      lambda x: (depopulate_documentation_frame(),
                                                 depopulate_useful_links_frame(),
                                                 save_notes(db_cursor, db_connection,
                                                            get_notes_from_text_box(notes_text_box),
                                                            subject_label_text.get()),
                                                 notes_text_box.delete("1.0", END),
                                                 set_label_text(combobox_selection.get()),
                                                 populate_documentation_frame(obtain_list_of_documentation(db_cursor,
                                                                              subject_label_text.get())),
                                                 populate_useful_links_frame(obtain_list_of_useful_links(db_cursor,
                                                                             subject_label_text.get())),
                                                 update_notes_content(db_cursor, combobox_selection.get()),
                                                 notes_text_box.insert(END, notes_content)))
    subject_selection_combo_box.grid(row=0, column=1)
    update_notes_content(db_cursor, subject_label_text.get())
    notes_text_box.insert(END, notes_content)


def construct_menu():

    menu_bar = Menu(root)

    file_menu = Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="New Subject", command=construct_add_record_form)
    file_menu.add_command(label="Edit Subject", command=lambda: (construct_edit_record_form(subject_label_text)))
    file_menu.add_command(label="Delete Subject", command=construct_delete_record_form)
    file_menu.add_command(label="Save", command=lambda: (save_notes(cursor, connection,
                                                                    get_notes_from_text_box(notes_text_box),
                                                                    combobox_selection.get()),
                                                         shutil.copyfile("tempDB.db", "personalNotes.db")))
    file_menu.add_command(label="Exit", command=lambda: (confirm_save()))

    menu_bar.add_cascade(label="File", menu=file_menu)

    root.config(menu=menu_bar)


def construct_add_record_form():

        sub_root = Toplevel()
        sub_root.geometry("+" + str(root.winfo_x() + 50) + "+" + str(root.winfo_y() + 50))
        sub_root.resizable(height=False, width=False)
        sub_root.transient(root)
        sub_root.grab_set()

        list_of_sub_forms.append(sub_root)
        sub_root.wm_title("Add Subject")

        add_link_type_selection = StringVar()

        list_of_links_to_add = []

        add_subject_name_frame = LabelFrame(sub_root, text="Subject Name:")
        add_subject_name_entry = Entry(add_subject_name_frame)

        add_link_frame = LabelFrame(sub_root, text="Add Link:")
        add_link_name_entry = Entry(add_link_frame)
        add_link_url_entry = Entry(add_link_frame)
        add_link_type_combo = ttk.Combobox(add_link_frame, textvariable=add_link_type_selection, state="readonly")
        add_link_type_combo['values'] = list_of_link_types

        docs_and_links_list_frame = LabelFrame(sub_root, text="Docs and Links:")
        doc_and_links_listbox = Listbox(docs_and_links_list_frame)
        docs_scrollbar = Scrollbar(docs_and_links_list_frame)

        add_subject_notes_frame = LabelFrame(sub_root, text="Notes:")
        add_subject_notes_entry = Text(add_subject_notes_frame, width=50, height=15)
        notes_scrollbar = Scrollbar(add_subject_notes_frame)

        add_link_button = Button(add_link_frame, text="Add", command=lambda: (add_doc_link_to_list(
                                                                                        add_link_name_entry.get(),
                                                                                        add_link_type_combo.get(),
                                                                                        add_link_url_entry.get(),
                                                                                        list_of_links_to_add,
                                                                                        False),
                                 populate_list_of_links_to_add_box(doc_and_links_listbox, list_of_links_to_add, False),
                                clear_add_link_entry_boxes(add_link_name_entry, add_link_url_entry, add_link_type_combo)
                                 ) if check_for_empty_fields(add_link_name_entry.get(),
                                                             add_link_url_entry.get(),
                                                             add_link_type_combo.get()) else None)
        add_link_clear_button = Button(add_link_frame, text="Clear", command=lambda: clear_add_link_entry_boxes(
                                                          add_link_name_entry, add_link_url_entry, add_link_type_combo))
        add_record_button = Button(sub_root, text="Add Subject", command=lambda: (EditRecords.add_record(
                    add_subject_name_entry.get(), list_of_links_to_add, add_subject_notes_entry.get("1.0", "end-1c")),
                    list_of_sub_forms.remove(sub_root),
                    update_ui(),
                    sub_root.destroy(),
                    ) if check_for_empty_subject_name(add_subject_name_entry.get()) else None)
        cancel_button = Button(sub_root, text="Cancel", command=lambda: (list_of_sub_forms.remove(sub_root),
                                                                         update_ui(),
                                                                         sub_root.destroy()))

        add_subject_name_frame.grid(row=0, column=0, sticky=N+S+W+E, padx=4, pady=2)
        add_subject_name_entry.pack(anchor=W, fill=X, padx=4, pady=2)

        add_link_frame.grid(row=1, column=0, sticky=N+S+W+E, padx=4, pady=2)
        add_link_name_entry.pack(anchor=W, fill=X, padx=4, pady=2)
        add_link_url_entry.pack(anchor=W, fill=X, padx=4, pady=2)
        add_link_type_combo.pack(anchor=W, fill=X, padx=4, pady=2)
        add_link_button.pack(side=LEFT, padx=25, expand=True)
        add_link_clear_button.pack(side=RIGHT, padx=25, expand=True)

        docs_and_links_list_frame.grid(row=0, column=1, rowspan=2, sticky=N+S+E+W, padx=4, pady=2)
        docs_scrollbar.pack(side=RIGHT, pady=4, fill=Y)
        doc_and_links_listbox.pack(pady=4, fill=BOTH)
        docs_scrollbar.config(command=doc_and_links_listbox.yview)

        add_subject_notes_frame.grid(row=2, column=0, columnspan=2, padx=4, pady=2, sticky=N+S+W+E)
        notes_scrollbar.pack(side=RIGHT, fill=Y)
        add_subject_notes_entry.pack(fill=BOTH)
        notes_scrollbar.config(command=add_subject_notes_entry.yview)

        add_record_button.grid(row=3, column=0, padx=25, pady=4)
        cancel_button.grid(row=3, column=1, padx=25, pady=4)

        add_link_name_entry.insert(0, 'Name')
        add_link_url_entry.insert(0, 'URL')


def construct_edit_record_form(subject_name):

        sub_root = Toplevel()
        sub_root.geometry("+" + str(root.winfo_x() + 50) + "+" + str(root.winfo_y() + 50))
        sub_root.resizable(height=False, width=False)
        sub_root.transient(root)
        sub_root.grab_set()

        list_of_sub_forms.append(sub_root)
        sub_root.wm_title("Edit Subject")

        edit_link_type_selection = StringVar()
        current_listbox_index = IntVar()

        master_list_of_links_to_edit = obtain_list_of_links_to_edit(subject_name.get())
        temp_list_of_links_to_edit = master_list_of_links_to_edit[:]

        list_of_docs_to_add = []
        list_of_docs_to_delete = []

        list_box_selected = BooleanVar()  # Prevents first entry being edited before being selected
        list_box_selected.set(False)

        edit_subject_name_frame = LabelFrame(sub_root, text="Subject Name:")
        edit_subject_name_label = Label(edit_subject_name_frame, text=subject_name.get())

        edit_link_frame = LabelFrame(sub_root, text="Edit Link:")
        edit_link_name_entry = Entry(edit_link_frame)
        edit_link_url_entry = Entry(edit_link_frame)
        edit_link_type_combo = ttk.Combobox(edit_link_frame, textvariable=edit_link_type_selection, state="readonly")
        edit_link_type_combo['values'] = list_of_link_types

        clear_fields_button = Button(edit_link_frame, text="Clear", command=lambda: (clear_add_link_entry_boxes(
                                                      edit_link_name_entry, edit_link_url_entry, edit_link_type_combo)))

        add_new_link_button = Button(edit_link_frame, text="Add New", command=lambda: (add_doc_link_to_list(
                edit_link_name_entry.get(), edit_link_type_combo.get(), edit_link_url_entry.get(), list_of_docs_to_add,
                True),
                clear_fields_button.invoke(), temp_list_of_links_to_edit.append(list_of_docs_to_add[-1]),
                populate_list_of_links_to_add_box(edit_docs_and_links_listbox, temp_list_of_links_to_edit, True))
                                     if check_for_empty_fields(edit_link_name_entry.get(),
                                                               edit_link_url_entry.get(),
                                                               edit_link_type_combo.get())
                                     else None)

        edit_link_button = Button(edit_link_frame, text="Save Edit", command=lambda: (edit_link_save(
                temp_list_of_links_to_edit, current_listbox_index.get(), edit_link_name_entry.get(),
                edit_link_type_combo.get(), edit_link_url_entry.get()),
                populate_list_of_links_to_add_box(edit_docs_and_links_listbox, temp_list_of_links_to_edit, True))
                                  if list_box_selected.get() and check_for_empty_fields(edit_link_name_entry.get(),
                                                                                        edit_link_url_entry.get(),
                                                                                        edit_link_type_combo.get())
                                  else None)

        delete_link_button = Button(edit_link_frame, text="Delete", command=lambda: (list_of_docs_to_delete.append(
                temp_list_of_links_to_edit.pop(current_listbox_index.get())),
                clear_fields_button.invoke(),
                populate_list_of_links_to_add_box(edit_docs_and_links_listbox, temp_list_of_links_to_edit, True))
                                    if confirm_delete_link(edit_link_name_entry.get())
                                    else None)

        edit_docs_and_links_list_frame = LabelFrame(sub_root, text="Docs and Links:")
        edit_docs_and_links_listbox = Listbox(edit_docs_and_links_list_frame, width=30)
        edit_docs_and_links_listbox.bind("<<ListboxSelect>>",
                                         lambda x: (list_box_selected.set(True),
                                                    clear_fields_button.invoke(),
                                                    current_listbox_index.set(int(edit_docs_and_links_listbox.index(
                                                            edit_docs_and_links_listbox.curselection()))),
                                                    edit_link_name_entry.insert(0, get_name_of_document_selection(
                                                        temp_list_of_links_to_edit, int(
                                                                    edit_docs_and_links_listbox.index(
                                                                        edit_docs_and_links_listbox.curselection())))),
                                                    edit_link_url_entry.insert(0, get_url_of_document_selection(
                                                        temp_list_of_links_to_edit, int(
                                                                    edit_docs_and_links_listbox.index(
                                                                        edit_docs_and_links_listbox.curselection())))),
                                                    edit_link_type_combo.set(
                                                        get_type_of_document_selection(temp_list_of_links_to_edit, int(
                                                            edit_docs_and_links_listbox.index(
                                                                edit_docs_and_links_listbox.curselection()))))))
        edit_docs_scrollbar = Scrollbar(edit_docs_and_links_list_frame)

        edit_subject_notes_frame = LabelFrame(sub_root, text="Notes:")
        edit_subject_notes_entry = Text(edit_subject_notes_frame, width=50, height=15)
        edit_notes_scrollbar = Scrollbar(edit_subject_notes_frame)

        edit_record_button = Button(sub_root, text="Save Changes", command=lambda: (edit_link_button.invoke(),
                                                                                    EditRecords.update_documentation(
                                                                                            temp_list_of_links_to_edit),
                                                                                    EditRecords.delete_documentation(
                                                                                            list_of_docs_to_delete),
                                                                                    EditRecords.add_new_documentation(
                                                                                            list_of_docs_to_add,
                                                                                            subject_name.get()),
                                                                                    EditRecords.update_record(
                                                                                          subject_name.get(),
                                                                                          edit_subject_notes_entry.get(
                                                                                                "1.0", "end-1c")),
                                                                                    list_of_sub_forms.remove(sub_root),
                                                                                    update_ui(),
                                                                                    sub_root.destroy()))

        cancel_button = Button(sub_root, text="Cancel", command=lambda: (list_of_sub_forms.remove(sub_root),
                                                                         update_ui(),
                                                                         sub_root.destroy()))

        edit_subject_name_frame.grid(row=0, column=0, sticky=N+S+W+E, padx=4, pady=2)
        edit_subject_name_label.pack(anchor=W, fill=X, padx=4)

        edit_link_frame.grid(row=1, column=0, sticky=N+S+W+E, padx=4, pady=2)
        edit_link_name_entry.pack(anchor=W, fill=X, padx=4, pady=2)
        edit_link_url_entry.pack(anchor=W, fill=X, padx=4, pady=2)
        edit_link_type_combo.pack(anchor=W, fill=X, padx=4, pady=2)
        add_new_link_button.pack(side=LEFT, padx=5, pady=2)
        edit_link_button.pack(side=LEFT, padx=15, pady=2)
        clear_fields_button.pack(side=LEFT)
        delete_link_button.pack(side=RIGHT, padx=15, pady=2)

        edit_docs_and_links_list_frame.grid(row=0, column=1, rowspan=2, sticky=N+S+E+W, padx=4, pady=2)
        edit_docs_scrollbar.pack(side=RIGHT, fill=Y)
        edit_docs_and_links_listbox.pack(fill=BOTH)
        edit_docs_scrollbar.config(command=edit_docs_and_links_listbox.yview)

        edit_subject_notes_frame.grid(row=2, column=0, columnspan=2, padx=4, pady=2, sticky=N+S+W+E)
        edit_notes_scrollbar.pack(side=RIGHT, fill=Y)
        edit_subject_notes_entry.pack(fill=BOTH)
        edit_notes_scrollbar.config(command=edit_subject_notes_entry.yview)

        edit_record_button.grid(row=3, column=0, padx=25, pady=4)
        cancel_button.grid(row=3, column=1, padx=25, pady=4)

        edit_link_name_entry.insert(0, 'Name')
        edit_link_url_entry.insert(0, 'URL')

        populate_list_of_links_to_add_box(edit_docs_and_links_listbox, temp_list_of_links_to_edit, True)
        edit_subject_notes_entry.insert(END, populate_notes_text_box(cursor, subject_name.get()))


def construct_delete_record_form():

    sub_root = Toplevel()
    sub_root.geometry("+" + str(root.winfo_x() + 50) + "+" + str(root.winfo_y() + 50))
    sub_root.resizable(height=False, width=False)
    sub_root.transient(root)
    sub_root.grab_set()

    list_of_sub_forms.append(sub_root)
    sub_root.wm_title("Delete Subject")

    subject_list = populate_subject_list(cursor)

    subject_to_delete_combo_box = ttk.Combobox(sub_root, state="readonly")
    subject_to_delete_combo_box['values'] = subject_list
    delete_subject_button = Button(sub_root, text="Delete Subject", command=lambda: (
                                                                                close_delete_window(
                                                                                 delete_subject(
                                                                                  subject_to_delete_combo_box.get()),
                                                                                 sub_root),
                                                                                update_ui()))
    cancel_button = Button(sub_root, text="Cancel", command=lambda: (list_of_sub_forms.remove(sub_root),
                                                                     update_ui(),
                                                                     sub_root.destroy()))

    subject_to_delete_combo_box.pack(padx=25, pady=10)
    delete_subject_button.pack(side=LEFT, padx=20, pady=10)
    cancel_button.pack(side=RIGHT, padx=15)

populate_documentation_frame(obtain_list_of_documentation(cursor, subject_label_text.get()))
populate_useful_links_frame(obtain_list_of_useful_links(cursor, subject_label_text.get()))
construct_form(cursor, connection)
construct_menu()
