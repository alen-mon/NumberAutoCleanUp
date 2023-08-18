import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import re

def browse_file():
    global df
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls"),
                                                      ("CSV files", "*.csv"),
                                                      ("Tab-delimited files", "*.txt")])
    if file_path:
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.txt'):
                df = pd.read_csv(file_path, delimiter='\t')
            else:
                df = pd.read_excel(file_path)

            update_display_message(f"File loaded successfully.\nNumber of rows: {df.shape[0]}\nNumber of columns: {df.shape[1]}")
            populate_column_listbox()

        except Exception as e:
            update_display_message(f"Error loading the file:\n{str(e)}")

def update_display_message(message):
    display_text.config(text=message)

def populate_column_listbox():
    column_headers = list(df.columns)
    column_listbox.delete(0, tk.END)
    for col in column_headers:
        column_listbox.insert(tk.END, col)


def auto_detect_phone_columns():
    selected_columns = []
    for i in range(column_listbox.size()):
        column_name = column_listbox.get(i)
        column_data = df[column_name]

        if re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{10})', column_name) or \
                column_data.apply(lambda x: bool(
                    re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{10})',
                              str(x)))).any():
            selected_columns.append(i)

    column_listbox.selection_clear(0, tk.END)  # Clear any existing selections
    for col_index in selected_columns:
        column_listbox.selection_set(col_index)

    update_description()


def update_description(*args):
    selected_columns = column_listbox.curselection()
    selected_rows = 0
    for col_index in selected_columns:
        col_name = column_listbox.get(col_index)
        col_data = df[col_name]
        selected_rows = max(selected_rows, col_data.count())

    description_label.config(text="Number of rows selected: {}".format(selected_rows))
    update_preview()

def update_scroll():
    preview_canvas.config(scrollregion=preview_canvas.bbox("all"))

row_to_item = {}
def update_preview():
    for widget in preview_frame.winfo_children():
        widget.destroy()

    selected_columns = column_listbox.curselection()
    if not selected_columns:
        return

    col_names = [column_listbox.get(index) for index in selected_columns]

    global table
    frame_canvas = tk.Frame(preview_frame)
    frame_canvas.pack(fill="both", expand=True)

    canvas = tk.Canvas(frame_canvas)
    canvas.pack(side="left", fill="both", expand=True)

    table = ttk.Treeview(canvas, columns=col_names, show="headings")

    for col_name in col_names:
        table.heading(col_name, text=col_name)

    initial_row_data = {}  # Dictionary to store initial row index and data

    for i, row in df.iterrows():
        initial_row_data[i] = {}
        for col_name in col_names:
            initial_row_data[i][col_name] = row[col_name]
        values = [row[col_name] for col_name in col_names]
        item_id = table.insert("", "end", values=values)
        row_to_item[i] = item_id

    table.pack(side="left", fill="both", expand=True)

    scrollbar_y = ttk.Scrollbar(frame_canvas, orient="vertical", command=table.yview)
    scrollbar_y.pack(side="right", fill="y")
    table.configure(yscrollcommand=scrollbar_y.set)

    canvas.create_window((0, 0), window=table, anchor="nw")

    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.pack(side="left", fill="both", expand=True)

def cleanup_numbers():
    selected_columns = column_listbox.curselection()
    print("Selected columns:", selected_columns)

    initial_row_data = {}  # Dictionary to store initial row index and data

    for col_index in selected_columns:
        col_name = column_listbox.get(col_index)
        col_data = df[col_name]
        print("Cleaning up column:", col_name)

        if col_name == "Mobile Number":  # Debug print for the "Mobile Number" column
            print("Before cleanup - Mobile Number column:")
            print(col_data)  # Debug print

        for i, value in col_data.items():
            print("Cleaning up value:", value)  # Debug print

            # Store the initial row data for reference
            if i not in initial_row_data:
                initial_row_data[i] = {}

            initial_row_data[i][col_name] = value  # Store the original value

            if isinstance(value, str):
                cleaned_value = re.sub(r'[^0-9]', '', value)
                if re.match(r'^[6789]\d{9}$', cleaned_value):
                    cleaned_value = '91' + cleaned_value
                if cleaned_value.startswith('0'):
                    cleaned_value = '91' + cleaned_value[1:]
                if re.match(r'^\d+\.\d+$', cleaned_value):
                    cleaned_value = cleaned_value.replace('.', '')
                if re.match(r'^\d+\.\d+e[+-]\d+$', cleaned_value, re.I):
                    cleaned_value = '{:.0f}'.format(float(cleaned_value))
                if len(cleaned_value) >= 12:  # Remove rows with less than 12 digits
                    df.at[i, col_name] = cleaned_value
                else:
                    df.at[i, col_name] = ''  # Remove rows with less than 12 digits

        if col_name == "Mobile Number":  # Debug print for the "Mobile Number" column
            print("After cleanup - Mobile Number column:")
            print(col_data)  # Debug print

    print("Initial row data:", initial_row_data)  # Debug print
    update_preview()


def show_cleaned_data():
    cleaned_data = {}
    for i, row in df.iterrows():
        cleaned_data[i] = {}
        for col_name in df.columns:
            cleaned_data[i][col_name] = row[col_name]
    show_dictionary_preview(cleaned_data)

def show_dictionary_preview(data):
    top = tk.Toplevel()
    top.title("Cleaned Data Preview")

    frame = tk.Frame(top)
    frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(frame)
    canvas.pack(side="left", fill="both", expand=True)

    modified_columns = [col_name.replace(" ", "_").replace("-", "_") for col_name in data[0].keys()]

    table = ttk.Treeview(canvas, columns=modified_columns, show="headings")

    for col_name, modified_col_name in zip(data[0].keys(), modified_columns):
        table.heading(modified_col_name, text=col_name)

    for i, row_data in data.items():
        values = list(row_data.values())
        table.insert("", "end", values=values)

    table.pack(fill="both", expand=True)


    scrollbar_y = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    scrollbar_y.pack(side="right", fill="y")
    table.configure(yscrollcommand=scrollbar_y.set)

    canvas.create_window((0, 0), window=table, anchor="nw")

    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Bind a function to adjust canvas size when the window is resized
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas_hscrollbar.set(0, 1)  # Adjust the view to force scrollbar resizing

    frame.bind("<Configure>", on_frame_configure)

    frame.bind("<Configure>", on_frame_configure)

    # Add a horizontal scrollbar to the canvas
    canvas_hscrollbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
    canvas_hscrollbar.pack(side="bottom",fill="x")
    canvas.configure(xscrollcommand=canvas_hscrollbar.set)
    # Pack the frame containing checkboxes after the canvas and scrollbar
    checkboxes_frame = tk.Frame(top)
    checkboxes_frame.pack()

    # Add a label to display the row count
    row_count_label = tk.Label(top, text="Number of rows: {}".format(len(data)))
    row_count_label.pack(pady=10)

    # Create a new frame for checkboxes
    checkboxes_frame = tk.Frame(top)
    checkboxes_frame.pack()

    # Add checkboxes for column selection
    col_selection_vars = {}
    col_checkboxes = []
    max_checkboxes_per_row = 3  # You can adjust this number as needed

    for col_name in data[0].keys():
        col_selection_vars[col_name] = tk.BooleanVar()
        col_checkbox = ttk.Checkbutton(checkboxes_frame, text=col_name, variable=col_selection_vars[col_name])
        col_checkbox.grid(row=len(col_checkboxes) // max_checkboxes_per_row, column=len(col_checkboxes) % max_checkboxes_per_row, sticky="w")
        col_checkboxes.append(col_checkbox)

    # Export button function
    def export_selected_columns():
        selected_columns = [col_name for col_name, var in col_selection_vars.items() if var.get()]
        if selected_columns:
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
            if file_path:
                if file_path.endswith('.xlsx'):
                    export_df = pd.DataFrame([{col: row_data[col] for col in selected_columns} for row_data in data.values()])
                    export_df.to_excel(file_path, index=False)
                    update_display_message("Selected columns exported to Excel file successfully.")
                elif file_path.endswith('.csv'):
                    export_df = pd.DataFrame([{col: row_data[col] for col in selected_columns} for row_data in data.values()])
                    export_df.to_csv(file_path, index=False)
                    update_display_message("Selected columns exported to CSV file successfully.")

    # Export button
    export_button = tk.Button(top, text="Export Selected Columns", command=export_selected_columns)
    export_button.pack(pady=10)

    top.mainloop()






root = tk.Tk()
root.title("Upload Data File")
root.geometry("800x600")

# Browse button
browse_button = tk.Button(root, text="Browse Data File", command=browse_file)
browse_button.pack(pady=10)

# Display area for messages
display_text = tk.Label(root, text="", wraplength=700, justify="center")
display_text.pack()

# Heading for column selection
heading_label = tk.Label(root, text="Select Columns:")
heading_label.pack()

# Listbox to display column headers
column_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, exportselection=False)
column_listbox.pack(pady=5)
column_listbox.bind("<<ListboxSelect>>", update_description)

# Button to auto-detect phone number columns
auto_detect_button = tk.Button(root, text="Auto Detect Phone Columns", command=auto_detect_phone_columns)
auto_detect_button.pack(pady=10)

# Description of selected columns
description_label = tk.Label(root, text="Number of rows selected: 0")
description_label.pack()

# Button to clean up numbers
cleanup_button = tk.Button(root, text="Cleanup Numbers", command=cleanup_numbers)
cleanup_button.pack(pady=10)

# Button to show cleaned data preview
show_cleaned_data_button = tk.Button(root, text="Show Cleaned Data Preview", command=show_cleaned_data)
show_cleaned_data_button.pack(pady=10)

# Frame for preview
preview_frame = tk.Frame(root)
preview_frame.pack()

# Canvas for scrolling
preview_canvas = tk.Canvas(preview_frame)
preview_canvas.pack(side="left", fill="both", expand=True)

# Call update_preview after creating the canvas
update_preview()

root.mainloop()
