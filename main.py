import os
import csv
import sqlite3
from tkinter import Tk, Label, Button, Entry, filedialog, Text, StringVar, messagebox, simpledialog
from bs4 import BeautifulSoup


class HTMLtoDBApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HTML to CSV & Database Tool")
        self.root.geometry("700x600")

        # Variables
        self.file_paths = []
        self.csv_file_path = StringVar()  # Holds the path for the saved CSV file
        self.table_name = StringVar()

        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # Label and button to add HTML files
        Label(self.root, text="HTML Files:").pack(pady=10)
        self.files_display = Text(self.root, height=5, width=70)
        self.files_display.pack()
        Button(self.root, text="Add HTML Files", command=self.add_files).pack(pady=5)

        # Button to clear all HTML files from the list
        Button(self.root, text="Clear All Files", command=self.clear_all_files).pack(pady=5)

        # Label and input for table name
        Label(self.root, text="Table Name:").pack(pady=10)
        Entry(self.root, textvariable=self.table_name).pack()

        # Buttons for processing
        Button(self.root, text="Extract to CSV", command=self.extract_to_csv).pack(pady=10)
        Button(self.root, text="Push Data", command=self.push_data).pack(pady=10)

        # Button to exit
        Button(self.root, text="Exit", command=self.root.quit).pack(pady=10)

    def add_files(self):
        """Open file dialog to select files."""
        files = filedialog.askopenfilenames(
            title="Select HTML Files",
            filetypes=(("HTML files", "*.html;*.htm"), ("All files", "*.*"))
        )
        if files:
            self.file_paths.extend(files)
            self.update_files_display()

    def update_files_display(self):
        """Display selected file paths."""
        self.files_display.delete("1.0", "end")
        self.files_display.insert("1.0", "\n".join(self.file_paths))

    def clear_all_files(self):
        """Clear all selected files."""
        self.file_paths.clear()  # Clear the list of file paths
        self.update_files_display()  # Update the display to show an empty list

    def extract_to_csv(self):
        """Extract HTML table data into a CSV file."""
        if not self.file_paths:
            messagebox.showerror("Error", "No HTML files selected.")
            return

        # Ask user for CSV file location and name
        save_path = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )

        if not save_path:
            messagebox.showwarning("Warning", "No file location selected. Operation canceled.")
            return

        self.csv_file_path.set(save_path)

        try:
            self.process_html_to_csv()
            messagebox.showinfo("Success", f"Data extracted to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def process_html_to_csv(self):
        """Process HTML files and write table data to the specified CSV file."""
        with open(self.csv_file_path.get(), "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            headers_written = False  # Ensure headers are written only once

            for file_path in self.file_paths:
                with open(file_path, "r", encoding="utf-8") as html_file:
                    soup = BeautifulSoup(html_file, "html.parser")
                    table = soup.find("table")
                    if not table:
                        continue

                    # Extract headers
                    headers = [header.text.strip() for header in table.find_all("th")]
                    if not headers_written and headers:
                        writer.writerow(headers)
                        headers_written = True

                    # Extract rows
                    rows = table.find_all("tr")
                    for row in rows:
                        data = [cell.text.strip() for cell in row.find_all("td")]
                        if data:
                            writer.writerow(data)

    def push_data(self):
        """Prompt user to select an option to push data."""
        if not os.path.exists(self.csv_file_path.get()):
            messagebox.showerror("Error", f"CSV file {self.csv_file_path.get()} not found.")
            return

        table_name = self.table_name.get().strip()
        if not table_name:
            messagebox.showerror("Error", "Please enter a table name.")
            return

        # Ask the user if they want to append to an existing table or create a new one
        choice = messagebox.askyesno(
            "Choose Option",
            f"Do you want to append data to the existing table '{table_name}'?\n"
            f"Click 'Yes' to append or 'No' to create a new table."
        )

        try:
            self.push_csv_to_db(table_name, create_new=not choice)
            if choice:
                messagebox.showinfo("Success", f"Data appended to table '{table_name}'")
            else:
                messagebox.showinfo("Success", f"Data pushed to new table '{table_name}'")
            # Clear the files display after processing
            self.file_paths.clear()
            self.update_files_display()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def push_csv_to_db(self, table_name, create_new=True, db_name="database.db"):
        """Push CSV data to the database."""
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        with open(self.csv_file_path.get(), "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            headers = next(reader)

            # Create table if needed
            if create_new:
                columns = ", ".join([f"{header} TEXT" for header in headers])
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")

            # Insert rows
            cursor.executemany(
                f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({', '.join(['?'] * len(headers))})",
                reader
            )

        conn.commit()
        conn.close()


if __name__ == "__main__":
    root = Tk()
    app = HTMLtoDBApp(root)
    root.mainloop()