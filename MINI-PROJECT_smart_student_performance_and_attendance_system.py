import csv
import os
import re
import glob
import warnings
warnings.filterwarnings("ignore")
import easyocr
import cv2

print("Loading OCR engine... Please wait a moment.")
reader_ocr = easyocr.Reader(['en'], gpu=False, verbose=False)


def print_entry_chart(rows):
    print("\n+---------+--------------------+-------+---------+---------+-------------------+")
    print("| Roll No | Student Name       | Math  | Science | English | Attendance        |")
    print("+---------+--------------------+-------+---------+---------+-------------------+")
    for r in rows:
        print(
            f"| {str(r[0]):<7} | {str(r[1]):<18} | {str(r[2]):<5} | {str(r[3]):<7} | {str(r[4]):<7} | {str(r[5]):<17} |")
    print("+---------+--------------------+-------+---------+---------+-------------------+")




def save_student_record(data_file, roll, name, math, science, english, attended_classes, total_classes):
    file_exists = os.path.exists(data_file) and os.path.getsize(data_file) > 0
    attendance_percent = round((attended_classes / total_classes) * 100, 2)

    with open(data_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Roll_No", "Name", "Math", "Science", "English", "Classes_Attended", "Total_Classes",
                             "Attendance_Percent"])
        writer.writerow([roll, name, math, science, english, attended_classes, total_classes, attendance_percent])

    return attendance_percent




def setup_excel_file():
    while True:
        print("\n==========================================================")
        print("               EXCEL / CSV FILE SELECTION                 ")
        print("==========================================================")
        print("1. Continue with an existing Excel/CSV file")
        print("2. Make a NEW Excel/CSV file")
        print("0. Exit Program")

        existing_files = [f for f in glob.glob("*.csv") if not f.endswith("_report.csv") and f != "final_teacher_report.csv"]
        choice = input("Select an option (1/2/0): ").strip()

        if choice == "0":
            return None, None

        elif choice == "1":
            if not existing_files:
                print("No existing Excel/CSV data files found. Please choose Option 2 to create a new one.")
                continue

            print("\nAvailable saved files:")
            for idx, fname in enumerate(existing_files, start=1):
                print(f"  {idx}. {fname}")
            print("  0. Go Back")

            while True:
                try:
                    f_idx = int(input(f"Choose file number (1-{len(existing_files)}) or 0 to Go Back: "))
                    if f_idx == 0:
                        break
                    if 1 <= f_idx <= len(existing_files):
                        selected_data_file = existing_files[f_idx - 1]
                        base_name = selected_data_file.replace("_data.csv", "").replace(".csv", "")
                        selected_report_file = f"{base_name}_report.csv"
                        print(f"Loaded: {selected_data_file}")
                        return selected_data_file, selected_report_file
                except ValueError:
                    pass
                print("Invalid selection. Please enter a valid number.")

        elif choice == "2":
            raw_name = input("Enter a name for the new Excel/CSV file (or type 'b' to Go Back): ").strip()
            if raw_name.lower() == 'b':
                continue
            if not raw_name:
                raw_name = "students"

            clean_name = re.sub(r'[\\/*?:"<>|]', "", raw_name).replace(".csv", "").replace("_data", "")
            new_data_file = f"{clean_name}_data.csv"
            new_report_file = f"{clean_name}_report.csv"

            if os.path.exists(new_data_file):
                overwrite = input(f"'{new_data_file}' already exists. Overwrite it? (y/n or 'b' to Go Back): ").strip().lower()
                if overwrite != 'y':
                    continue
                os.remove(new_data_file)

            print(f"Created new file setup: {new_data_file}")
            return new_data_file, new_report_file

        else:
            print("Invalid choice. Please enter 1, 2, or 0.")



def scan_students_from_image(data_file, total_classes, start_roll=1):
    print("\n==========================================================")
    print("    UNIVERSAL IMAGE SCANNER (HANDWRITTEN & TYPED)         ")
    print("==========================================================")

    image_path = input("Enter the full path to the image file (or type 'b' to Go Back): ").strip().strip('"').strip("'")
    if image_path.lower() == 'b':
        print("Going back...")
        return []

    if not os.path.exists(image_path):
        print(f"Error: Could not find image at '{image_path}'.")
        return []

    print("Enhancing image contrast and scanning... Please wait.")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=-40)

    results = reader_ocr.readtext(enhanced)
    if not results:
        print("No text could be detected. Please try a clearer, brighter photo.")
        return []

    full_text = "\n".join([res[1] for res in results])
    scanned_records = []

    # MODE A: Check if it matches a Typed / Printed Labeled Form
    roll_match = re.search(r"(?:Roll\s*(?:No|Number)?)\s*[:\-]\s*([A-Za-z0-9\-]+)", full_text, re.IGNORECASE)
    math_match = re.search(r"Math(?:ematics)?\s*[:\-]\s*(\d+(?:\.\d+)?)", full_text, re.IGNORECASE)
    sci_match = re.search(r"Science\s*[:\-]\s*(\d+(?:\.\d+)?)", full_text, re.IGNORECASE)
    eng_match = re.search(r"English\s*[:\-]\s*(\d+(?:\.\d+)?)", full_text, re.IGNORECASE)

    if roll_match and math_match and sci_match and eng_match:
        print("\nDetected Format: Typed / Printed Form")
        name_match = re.search(r"(?:Student\s*)?Name\s*[:\-]\s*([A-Za-z\s\.]+)", full_text, re.IGNORECASE)
        att_match = re.search(r"(?:Classes\s*)?Attended\s*[:\-]\s*(\d+)", full_text, re.IGNORECASE)

        roll = roll_match.group(1).strip()
        name = name_match.group(1).strip() if name_match else input("Enter Student Name: ").strip()
        math = float(math_match.group(1))
        science = float(sci_match.group(1))
        english = float(eng_match.group(1))
        attended = int(att_match.group(1)) if att_match else int(input(f"Enter Classes Attended (out of {total_classes}): "))

        print(f"\nParsed: Roll {roll} | {name} | Math: {math} | Sci: {science} | Eng: {english} | Att: {attended}/{total_classes}")
        if input("Save this record? (y/n): ").strip().lower() == 'y':
            att_pct = save_student_record(data_file, roll, name, math, science, english, attended, total_classes)
            scanned_records.append([roll, name[:18], math, science, english, f"{attended}/{total_classes} ({att_pct}%)"])
        return scanned_records

    # MODE B: Parse as a Handwritten or Printed Multi-Row Table
    print("\nDetected Format: Multi-Student Table")
    rows = []
    for (bbox, text, prob) in results:
        y_center = (bbox[0][1] + bbox[2][1]) / 2
        x_left = bbox[0][0]

        placed = False
        for row in rows:
            if abs(row['y'] - y_center) < 45:
                row['items'].append((x_left, text.strip()))
                placed = True
                break
        if not placed:
            rows.append({'y': y_center, 'items': [(x_left, text.strip())]})

    rows.sort(key=lambda r: r['y'])

    def clean_num(val, default="0"):
        fixed = val.replace('S', '5').replace('s', '5').replace('o', '0').replace('O', '0').replace('g', '9').replace(
            '+', '7').replace('l', '1').replace('I', '1')
        digits = re.findall(r"\d+(?:\.\d+)?", fixed)
        return digits[0] if digits else default

    print("\n--- Review & Confirm Scanned Rows ---")
    print("(Press Enter to accept, 'e' to edit, 's' to skip row, or 'b' to stop scanning & go back)\n")

    auto_roll = start_roll
    for r in rows:
        r['items'].sort(key=lambda item: item[0])
        cols = [item[1] for item in r['items']]
        row_str = " ".join(cols).lower()

        if any(h in row_str for h in ["roll", "student", "math", "science", "english", "attend"]):
            continue
        if len(cols) < 2:
            continue

        name_idx = next((idx for idx, val in enumerate(cols) if len(re.findall(r"[A-Za-z]", val)) >= 2), None)
        if name_idx is None:
            continue

        det_name = cols[name_idx]
        det_roll = clean_num(cols[0], str(auto_roll)) if name_idx > 0 else str(auto_roll)

        marks_cols = cols[name_idx + 1:]
        det_math = clean_num(marks_cols[0], "0") if len(marks_cols) > 0 else "0"
        det_sci  = clean_num(marks_cols[1], "0") if len(marks_cols) > 1 else "0"
        det_eng  = clean_num(marks_cols[2], "0") if len(marks_cols) > 2 else "0"
        det_att  = clean_num(marks_cols[3], "0") if len(marks_cols) > 3 else "0"

        print(f"Detected Row -> Roll: {det_roll} | Name: {det_name} | Math: {det_math} | Science: {det_sci} | English: {det_eng} | Attended: {det_att}")
        action = input("Press [Enter] to save, [e] to edit, [s] to skip, or [b] to Go Back: ").strip().lower()

        if action == 'b':
            print("Stopped scanning. Going back...")
            break
        elif action == 's':
            continue
        elif action == 'e':
            det_roll = input(f"  Roll No [{det_roll}]: ").strip() or det_roll
            det_name = input(f"  Name [{det_name}]: ").strip() or det_name
            det_math = input(f"  Math [{det_math}]: ").strip() or det_math
            det_sci  = input(f"  Science [{det_sci}]: ").strip() or det_sci
            det_eng  = input(f"  English [{det_eng}]: ").strip() or det_eng
            det_att  = input(f"  Attended [{det_att}]: ").strip() or det_att

        try:
            att_pct = save_student_record(data_file, det_roll, det_name, float(det_math), float(det_sci), float(det_eng),
                                          int(det_att), total_classes)
            scanned_records.append([det_roll, det_name[:18], float(det_math), float(det_sci), float(det_eng),
                                    f"{det_att}/{total_classes} ({att_pct}%)"])
            auto_roll += 1
        except ValueError:
            print("Invalid number entered; skipping this row.")

    return scanned_records


def enter_single_student_manually(data_file, student_num, total_students, total_classes):
    print(f"\n>>> Enter Data for Student {student_num} of {total_students} (Type 'b' at any prompt to Go Back) <<<")
    roll = input("Student Roll Number: ").strip()
    if roll.lower() == 'b':
        return None

    name = input("Student Full Name: ").strip()
    if name.lower() == 'b':
        return None

    while True:
        val = input("Math Marks (out of 100): ").strip()
        if val.lower() == 'b': return None
        try:
            math = float(val)
            if 0 <= math <= 100: break
            print("Marks must be between 0 and 100.")
        except ValueError:
            print("Invalid number.")

    while True:
        val = input("Science Marks (out of 100): ").strip()
        if val.lower() == 'b': return None
        try:
            science = float(val)
            if 0 <= science <= 100: break
            print("Marks must be between 0 and 100.")
        except ValueError:
            print("Invalid number.")

    while True:
        val = input("English Marks (out of 100): ").strip()
        if val.lower() == 'b': return None
        try:
            english = float(val)
            if 0 <= english <= 100: break
            print("Marks must be between 0 and 100.")
        except ValueError:
            print("Invalid number.")

    while True:
        val = input(f"Classes Attended (out of {total_classes}): ").strip()
        if val.lower() == 'b': return None
        try:
            attended_classes = int(val)
            if 0 <= attended_classes <= total_classes: break
            print(f"Attendance must be between 0 and {total_classes}.")
        except ValueError:
            print("Invalid number.")

    attendance_percent = save_student_record(data_file, roll, name, math, science, english, attended_classes, total_classes)
    return [roll, name[:18], math, science, english, f"{attended_classes}/{total_classes} ({attendance_percent}%)"]


def collect_class_data(data_file):
    print("\n==========================================================")
    print("           CLASS DATA ENTRY & SCANNER SETUP               ")
    print("==========================================================")

    existing_rows = []
    saved_total_classes = None

    if os.path.exists(data_file) and os.path.getsize(data_file) > 0:
        with open(data_file, mode="r") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames and "Roll_No" in reader.fieldnames:
                for row in reader:
                    existing_rows.append([
                        row["Roll_No"],
                        row["Name"][:18],
                        float(row["Math"]),
                        float(row["Science"]),
                        float(row["English"]),
                        f"{row['Classes_Attended']}/{row['Total_Classes']} ({row['Attendance_Percent']}%)"
                    ])
                    saved_total_classes = int(row["Total_Classes"])
            else:
                file.close()
                os.remove(data_file)

    if existing_rows:
        print(f"Found {len(existing_rows)} saved student record(s) in '{data_file}'.")

    # Question 1: How many total students are in the class?
    while True:
        val = input(f"1. How many total students are in the class? (Min {max(1, len(existing_rows))}, or 'b' to Go Back): ").strip()
        if val.lower() == 'b':
            return "BACK"
        try:
            num_students = int(val)
            if num_students >= max(1, len(existing_rows)):
                break
            print(f"Total students cannot be less than the {len(existing_rows)} already saved.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

    # Question 2: How many classes held in semester?
    if saved_total_classes is not None:
        total_classes = saved_total_classes
        print(f"2. Total classes held in this semester: {total_classes} (Loaded from '{data_file}')")
    else:
        while True:
            val = input("2. How many classes were held in this semester? (or 'b' to Go Back): ").strip()
            if val.lower() == 'b':
                return "BACK"
            try:
                total_classes = int(val)
                if total_classes > 0:
                    break
                print("Total classes must be greater than 0.")
            except ValueError:
                print("Invalid input. Please enter a whole number.")

    chart_rows = list(existing_rows)
    for i in range(len(existing_rows) + 1, num_students + 1):
        chart_rows.append([f"#{i}", "[Waiting...]", "-", "-", "-", "-"])

    print("\n--- Current Class Chart ---")
    print_entry_chart(chart_rows)

    filled_count = len(existing_rows)
    if filled_count >= num_students:
        print("\nAll student slots are already filled!")
        return "COMPLETE"

    while filled_count < num_students:
        print(f"\n--- Student Slot {filled_count + 1} of {num_students} ---")
        print("1. Enter Student Data Manually")
        print("2. Scan Student Data from Image (Handwritten / Typed)")
        print("3. Save & Exit for Today (Resume Remaining Tomorrow)")
        print("4. Go Back to Excel / CSV File Selection")
        method = input("Choose an option (1/2/3/4): ").strip()

        if method == "1":
            row_data = enter_single_student_manually(data_file, filled_count + 1, num_students, total_classes)
            if row_data is not None:
                chart_rows[filled_count] = row_data
                filled_count += 1
                print_entry_chart(chart_rows)

        elif method == "2":
            new_rows = scan_students_from_image(data_file, total_classes, start_roll=filled_count + 1)
            for r in new_rows:
                if filled_count < num_students:
                    chart_rows[filled_count] = r
                    filled_count += 1
            if new_rows:
                print_entry_chart(chart_rows)

        elif method == "3":
            remaining = num_students - filled_count
            print(f"\nProgress saved! {filled_count} student(s) saved in '{data_file}'.")
            print(f"Run the program again tomorrow and choose Option 1 to resume from Student Slot {filled_count + 1} ({remaining} remaining).")
            return "PAUSED"

        elif method == "4":
            print("Returning to File Selection menu...")
            return "BACK"
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

    return "COMPLETE"


def generate_report(data_file, report_file):
    seen_rolls = set()
    clean_records = []
    subject_fail_list = []
    low_attendance_list = []

    pass_mark = 40.0
    min_attendance = 75.0

    if not os.path.exists(data_file) or os.path.getsize(data_file) == 0:
        print(f"\nError: Source file '{data_file}' is empty or not found.")
        return

    with open(data_file, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            roll = row["Roll_No"]
            name = row["Name"]

            if roll in seen_rolls:
                continue
            seen_rolls.add(roll)

            math = float(row["Math"])
            science = float(row["Science"])
            english = float(row["English"])
            attendance = float(row["Attendance_Percent"])

            total = math + science + english
            percentage = round((total / 300) * 100, 2)

            failed_subjects = []
            if math < pass_mark:
                failed_subjects.append(f"Math ({math})")
            if science < pass_mark:
                failed_subjects.append(f"Science ({science})")
            if english < pass_mark:
                failed_subjects.append(f"English ({english})")

            if failed_subjects:
                subject_fail_list.append(f"{name} (Roll {roll}) -> Failed in: {', '.join(failed_subjects)}")

            if attendance < min_attendance:
                low_attendance_list.append(
                    f"{name} (Roll {roll}) -> Attendance: {attendance}% ({row['Classes_Attended']}/{row['Total_Classes']} classes)")

            if failed_subjects:
                grade = "F"
            elif percentage >= 90:
                grade = "A+"
            elif percentage >= 75:
                grade = "A"
            elif percentage >= 60:
                grade = "B"
            else:
                grade = "C"

            if failed_subjects and attendance < min_attendance:
                status = "Fail & Low Attnd"
            elif failed_subjects:
                status = "Subject Fail"
            elif attendance < min_attendance:
                status = "Low Attendance"
            else:
                status = "Pass / Good"

            clean_records.append({
                "Roll_No": roll,
                "Name": name,
                "Total_Marks": total,
                "Percentage": f"{percentage}%",
                "Grade": grade,
                "Attendance": f"{attendance}%",
                "Status": status
            })

    with open(report_file, mode="w", newline="") as file:
        fieldnames = ["Roll_No", "Name", "Total_Marks", "Percentage", "Grade", "Attendance", "Status"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_records)

    print("\n======================================================================================")
    print("                            FINAL CLASS PERFORMANCE CHART                             ")
    print("======================================================================================")
    print("+---------+--------------------+-------+------------+-------+------------+------------------+")
    print("| Roll No | Student Name       | Total | Percentage | Grade | Attendance | Status           |")
    print("+---------+--------------------+-------+------------+-------+------------+------------------+")
    for rec in clean_records:
        print(
            f"| {rec['Roll_No']:<7} | {rec['Name'][:18]:<18} | {rec['Total_Marks']:<5} | {rec['Percentage']:<10} | {rec['Grade']:<5} | {rec['Attendance']:<10} | {rec['Status']:<16} |")
    print("+---------+--------------------+-------+------------+-------+------------+------------------+")

    print("\n--------------------------------------------------------------------------------------")
    print(" STUDENTS WHO FAILED IN ONE OR MORE SUBJECTS (Passing Marks: 40)")
    print("--------------------------------------------------------------------------------------")
    if subject_fail_list:
        for item in subject_fail_list:
            print(f"* {item}")
    else:
        print("None! All students passed in every subject.")

    print("\n--------------------------------------------------------------------------------------")
    print(" STUDENTS WITH LOW ATTENDANCE (Minimum Required: 75%)")
    print("--------------------------------------------------------------------------------------")
    if low_attendance_list:
        for item in low_attendance_list:
            print(f"* {item}")
    else:
        print("None! All students have 75% or higher attendance.")

    print(f"\nExcel-ready report saved to: {report_file}")


if __name__ == "__main__":
    while True:
        active_data_file, active_report_file = setup_excel_file()
        if active_data_file is None:
            print("Exiting program. Goodbye!")
            break

        status = collect_class_data(active_data_file)
        if status == "BACK":
            continue
        elif status == "COMPLETE":
            generate_report(active_data_file, active_report_file)
            break
        elif status == "PAUSED":
            gen_now = input("Would you also like to generate a partial report for the students entered so far? (y/n): ").strip().lower()
