import os
import calendar
from datetime import datetime
from datetime import date
import sqlite3
from flask import Flask, app, render_template, request, redirect, session, Response
app = Flask(__name__)

app.secret_key = "attendflow_secret_key"

# ---------------- HOME ---------------- #

@app.route('/')
def home():
    return render_template('index.html')

# ---------------- REGISTER ---------------- #

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO admins(username,password)
        VALUES(?,?)
        """,(username,password))

        conn.commit()

        conn.close()

        return redirect('/login')

    return render_template(
        'register.html'
    )


# ---------------- LOGIN ---------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, password)
        )

        admin = cursor.fetchone()

        conn.close()

        if admin:
            session['admin_id'] = admin[0]
            session['admin'] = admin[1]
            return redirect('/dashboard')
        else:
            return "Invalid Credentials"

    return render_template('login.html')


# ---------------- DASHBOARD ---------------- #

@app.route('/dashboard')
def dashboard():

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM employees"
    )
    total_employees = cursor.fetchone()[0]

    today = str(date.today())

    cursor.execute("""
    SELECT COUNT(*)
    FROM attendance
    WHERE date=? AND status='Present'
    """, (today,))
    present_today = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM attendance
    WHERE date=? AND status='Absent'
    """, (today,))
    absent_today = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM attendance"
    )
    total_records = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',

        total_employees=total_employees,
        present_today=present_today,
        absent_today=absent_today,
        total_records=total_records
    )



# ---------------- ADD EMPLOYEE ---------------- #

@app.route('/add-employee', methods=['GET', 'POST'])
def add_employee():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        phone = request.form['phone']

        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()

        admin_id = session['admin_id']

        cursor.execute("""
        INSERT INTO employees(
            name,
            email,
            department,
            phone,
            admin_id
        )
        VALUES(?,?,?,?,?)
        """, (
            name,
            email,
            department,
            phone,
            admin_id
        ))

        conn.commit()
        conn.close()

        return "Employee Added Successfully"

    return render_template('add_employee.html')


# ---------------- VIEW EMPLOYEES ---------------- #

@app.route('/employees')
def employees():

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    admin_id = session['admin_id']

    cursor.execute(
        "SELECT * FROM employees WHERE admin_id=?",
        (admin_id,)
    )
    employees = cursor.fetchall()

    conn.close()

    return render_template(
        'employees.html',
        employees=employees
    )


# ---------------- ATTENDANCE ---------------- #

@app.route('/attendance')
def attendance():

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    admin_id = session['admin_id']

    cursor.execute(
        "SELECT * FROM employees WHERE admin_id=?",
        (admin_id,)
    )

    employees = cursor.fetchall()

    conn.close()

    return render_template(
        'attendance.html',
        employees=employees,
        current_date=str(date.today())
    )


@app.route('/mark-attendance', methods=['POST'])
def mark_attendance():

    employee_id = request.form['employee_id']
    status = request.form['status']

    attendance_date = request.form['attendance_date']
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM attendance
    WHERE employee_id=? AND date=?
    """, (employee_id, attendance_date))

    existing = cursor.fetchone()

    if existing:

        conn.close()

        return "Attendance already marked today"

    cursor.execute("""
    INSERT INTO attendance(employee_id,date,status)
    VALUES(?,?,?)
    """, (employee_id, attendance_date, status))
    conn.commit()
    conn.close()

    return "Attendance Saved Successfully"




@app.route('/check-attendance')
def check_attendance():

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance")

    data = cursor.fetchall()

    conn.close()

    return render_template(
    'all_attendance.html',
    data=data
)

@app.route('/attendance-report')
def attendance_report():

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    admin_id = session['admin_id']

    cursor.execute("""
    SELECT id,name
    FROM employees
    WHERE admin_id=?
    """, (admin_id,))

    employees = cursor.fetchall()

    conn.close()

    return render_template(
        'attendance_report.html',
        employees=employees
    )

@app.route('/delete-employee/<int:id>')
def delete_employee(id):

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    admin_id = session['admin_id']

    cursor.execute(
        """
        DELETE FROM employees
        WHERE id=? AND admin_id=?
        """,
        (id, admin_id)
    )

    conn.commit()
    conn.close()

    return redirect('/employees')

@app.route('/edit-employee/<int:id>', methods=['GET','POST'])
def edit_employee(id):

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    admin_id = session['admin_id']

    cursor.execute(
        """
        SELECT *
        FROM employees
        WHERE id=? AND admin_id=?
        """,
        (id, admin_id)
    )

    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return "Access Denied"

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        phone = request.form['phone']

        cursor.execute("""
        UPDATE employees
        SET name=?, email=?, department=?, phone=?
        WHERE id=?
        """, (name, email, department, phone, id))

        conn.commit()
        conn.close()

        return redirect('/employees')

    conn.close()

    return render_template(
        'edit_employee.html',
        employee=employee
    )
    


@app.route('/employee-attendance/<int:id>/<int:year>/<int:month>')
def employee_attendance(id, year, month):

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    admin_id = session['admin_id']

    cursor.execute(
        """
        SELECT *
        FROM employees
        WHERE id=? AND admin_id=?
        """,
        (id, admin_id)
    )

    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return "Access Denied"

    cursor.execute("""
    SELECT date,status
    FROM attendance
    WHERE employee_id=?
    """, (id,))

    records = cursor.fetchall()

    attendance_data = {}

    for record in records:
        attendance_date = datetime.strptime(record[0], "%Y-%m-%d")

        if (
            attendance_date.year == year and
            attendance_date.month == month
        ):
            attendance_data[attendance_date.day] = record[1]

    cal = calendar.monthcalendar(year, month)

    present_count = 0
    absent_count = 0

    for status in attendance_data.values():
        if status == "Present":
            present_count += 1
        else:
            absent_count += 1

    total_days = present_count + absent_count

    attendance_percentage = 0

    if total_days > 0:

        attendance_percentage = round(
            (present_count / total_days) * 100,
            2
        )

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    conn.close()

    return render_template(
        'employee_attendance.html',

        employee=employee,
        employee_id=id,

        calendar_days=cal,
        attendance_data=attendance_data,

        month=month,
        year=year,
        month_name=calendar.month_name[month],

        present_count=present_count,
        absent_count=absent_count,
        attendance_percentage=attendance_percentage,

        prev_month=prev_month,
        prev_year=prev_year,

        next_month=next_month,
        next_year=next_year
    )

@app.route('/manage-attendance/<int:id>')
def manage_attendance(id):

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    admin_id = session['admin_id']
    cursor.execute(
        """
        SELECT *
        FROM employees
        WHERE id=? AND admin_id=?
        """,
        (id, admin_id)
    )

    employee_check = cursor.fetchone()

    if not employee_check:
        conn.close()
        return "Access Denied"

    cursor.execute(
        "SELECT name FROM employees WHERE id=?",
        (id,)
    )

    employee = cursor.fetchone()

    cursor.execute("""
    SELECT id,date,status
    FROM attendance
    WHERE employee_id=?
    ORDER BY date DESC
    """,(id,))

    records = cursor.fetchall()

    conn.close()

    return render_template(
        'manage_attendance.html',
        employee=employee,
        employee_id=id,
        records=records
    )

@app.route('/delete-attendance/<int:id>/<int:employee_id>')
def delete_attendance(id, employee_id):

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM attendance WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        f'/manage-attendance/{employee_id}'
    )

@app.route('/export-attendance')
def export_attendance():

    admin_id = session['admin_id']

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        employees.name,
        attendance.date,
        attendance.status

    FROM attendance

    JOIN employees
    ON attendance.employee_id = employees.id

    WHERE employees.admin_id = ?

    ORDER BY attendance.date DESC
    """, (admin_id,))

    records = cursor.fetchall()

    conn.close()

    csv_data = "Employee,Date,Status\n"

    for row in records:

        csv_data += (
            f"{row[0]},{row[1]},{row[2]}\n"
        )

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=attendance_report.csv"
        }
    )

@app.route('/reports')
def reports():

    return render_template(
        'reports.html'
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# ---------------- RUN APP ---------------- #


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
