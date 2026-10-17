# Student Attendance Management System

## 📌 Project Overview

The **Student Attendance Management System** is a Python-based desktop application developed to simplify student attendance management. It allows users to maintain student records, mark daily attendance, manage the total number of classes conducted, and generate attendance reports.

The application uses **Python Tkinter** for the graphical user interface and **MySQL** for storing student and attendance information.

## 🎯 Objectives

- Maintain student details in a database.
- Record daily attendance as Present or Absent.
- Manage the total number of classes conducted.
- Calculate student attendance percentages.
- Generate attendance reports.
- Identify students whose attendance is below 75%.

## ✨ Features

- **Student Management:** Add and manage student records.
- **Attendance Management:** Record daily attendance.
- **Class Management:** Maintain the total number of classes conducted.
- **Attendance Reports:** View student attendance information.
- **Percentage Calculation:** Calculate attendance percentages.
- **Low Attendance Warning:** Identify students with attendance below 75%.
- **MySQL Database:** Store and retrieve application data.

## 🛠️ Technologies Used

- **Programming Language:** Python
- **GUI Framework:** Tkinter
- **Database:** MySQL
- **Database Connector:** MySQL Connector/Python
- **Environment Configuration:** python-dotenv
- **IDE:** Visual Studio Code
- **Database Tool:** MySQL Workbench

## 📁 Project Structure

```text
StudentAttendanceSystem/
│
├── main.py
├── db_config.py
├── test_db.py
├── requirements.txt
├── README.md
├── .gitignore
└── ex.env
```

**Note:** `ex.env` is a local configuration file and should not be uploaded to GitHub. It is shown above only to explain the local project setup.

## 💻 Requirements

- Python 3
- MySQL Server
- MySQL Workbench (recommended)
- Visual Studio Code (optional)

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/adarshggit/StudentAttendanceManagementSystem.git
```

### 2. Open the Project Folder

```bash
cd StudentAttendanceManagementSystem
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure MySQL

- Start your MySQL server.
- Create the database named `student_attendance_db`.
- Create the required tables: `students`, `attendance`, and `class_sessions`.
- Configure your local database connection details in `ex.env`.

Use the following format in your local `ex.env` file:

```text
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=student_attendance_db
```

Replace `your_mysql_password` with your own MySQL password.

**Security:** Never upload `ex.env` or real database passwords to GitHub.

### 6. Run the Application

```bash
python main.py
```

To test the database connection, run:

```bash
python test_db.py
```

## 📊 Attendance Calculation

The system uses attendance records and the total number of classes conducted to calculate attendance percentages.

Students with attendance below **75%** can be identified for follow-up.

## 🚀 Future Enhancements

- Export attendance reports to PDF or Excel.
- Add teacher and administrator login.
- Improve report filtering and searching.
- Add graphical attendance statistics.
- Provide additional attendance analysis.

## 👨‍💻 Author

**Adarsha Babu Gouda**

## 🎓 Internship

**Domain:** Python Programming  
**Organization:** CodSoft

## 🔗 GitHub Repository

[Student Attendance Management System](https://github.com/adarshggit/StudentAttendanceManagementSystem)

## 📄 Purpose

This project is developed for educational and Python programming internship purposes.
