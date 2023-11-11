from flask import Flask, render_template, request, redirect, url_for, session
from db import create_connection
import secrets

def generate_secret_key():
    return secrets.token_hex(16)

app = Flask(__name__, template_folder="templates")
app.secret_key = generate_secret_key()

def create_user_table():
    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        donor_type VARCHAR(20),
                        name VARCHAR(100),
                        phone VARCHAR(15),
                        email VARCHAR(100),
                        state_choice VARCHAR(50),
                        aadhar VARCHAR(20),
                        blood_group VARCHAR(5)
                    )
                    ''')
        conn.commit()
        conn.close()

create_user_table()

def create_userdetails_table():
    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS userdetails (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100),
                        email_id VARCHAR(100),
                        hospital_name VARCHAR(100),
                        blood_donated INT,
                        blood_group VARCHAR(5),
                        state_choice VARCHAR(50)
                        )
                    ''')
        conn.commit()
        conn.close()

create_userdetails_table()

def create_blood_details_table():
    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS blood_details (
                        blood_grp VARCHAR(5),
                        hospital_name VARCHAR(100),
                        quantity INT,
                        state VARCHAR(50),
                        PRIMARY KEY (hospital_name, state)
                    )
                    ''')
        conn.commit()
        conn.close()

create_blood_details_table()

def get_database_version():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('SELECT version()')
    data = cur.fetchone()
    cur.close()
    conn.close()
    return data[0] if data else None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        donor_type = request.form['donorType']
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        state_choice = request.form['StateChoice']
        aadhar = request.form['aadhar']
        blood_group = request.form['bloodGroup']

        conn = create_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('''
                        INSERT INTO users (donor_type, name, phone, email, state_choice, aadhar, blood_group) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''', (donor_type, name, phone, email, state_choice, aadhar, blood_group))
            conn.commit()
            conn.close()

        return redirect(url_for('login'))

    return render_template('registration.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    user = session.get('user')
    if user:
        if request.method == 'POST':
            if request.form.get('desiredQuantity'):
                return handle_desired_blood_quantity(request.form, user)
            else:
                return handle_blood_donation(request.form, user)

        return render_template('dashboard.html', user=user)
    else:
        return redirect(url_for('login'))

def handle_blood_donation(form, user):
    hospital = form['hospital']
    liters = form['liters']
    question1 = form.get('question1')
    question2 = form.get('question2')

    if not (question1 or question2):
        conn = create_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('''
                        INSERT INTO userdetails (username, email_id, hospital_name, blood_donated, blood_group, state_choice) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (user['name'], user['email'], hospital, liters, user['bgroup'], user['state']))
            conn.commit()

            cur.execute('''
                        INSERT INTO blood_details (blood_grp, hospital_name, quantity, state)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (hospital_name, state)
                        DO UPDATE SET quantity = blood_details.quantity + EXCLUDED.quantity
                        ''', (user['bgroup'], hospital, liters, user['state']))
            conn.commit()

            conn.close()
            return redirect(url_for('dashboard'))

        return "Database connection error"

    return "User is not eligible"

def handle_desired_blood_quantity(form, user):
    desired_hospital = form['desiredHospital']
    desired_liters = int(form['desiredQuantity'])
    desired_blood_group = form['desiredBloodGroup']
    desired_state = form['desiredState']

    conn = create_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT quantity FROM blood_details WHERE hospital_name = %s AND blood_grp = %s AND state = %s',
                    (desired_hospital, desired_blood_group, desired_state))
        blood_data = cur.fetchone()

        if blood_data and blood_data[0] >= desired_liters:
            cur.execute('''
                        UPDATE blood_details 
                        SET quantity = quantity - %s 
                        WHERE hospital_name = %s AND blood_grp = %s AND state = %s
                        ''', (desired_liters, desired_hospital, desired_blood_group, desired_state))
            conn.commit()

            conn.close()
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            return "Requested Quantity of Blood is not available"

    return "Database connection error"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        aadhar = request.form['aadhar']

        conn = create_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE email = %s AND aadhar = %s', (email, aadhar))
            user_data = cur.fetchone()
            conn.close()

            if user_data:
                # Starting user session
                session['user'] = {
                    'email': user_data[4],  # index 4 is the email in the 'users' table
                    'name': user_data[2],
                    'state':user_data[5],
                    'aadhar': user_data[6],
                    'phoneNum':user_data[3],
                    'bgroup': user_data[7]   # index 2 is the name in the 'users' table
                    # Add other user data as needed
                }
                # User found in the database, redirect to the dashboard
                return redirect(url_for('dashboard'))
            else:
                # Invalid credentials, render the login page with an error message
                return render_template('login.html', invalid=True)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # Clear the user session
    return redirect(url_for('home'))

@app.route('/enquiry', methods=['GET', 'POST'])
def enquiry():
    if request.method == 'POST':
        state = request.form['state']
        hospital = request.form['hospital']
        blood_group = request.form['bloodGroup']

        conn = create_connection()
        if conn:
            cur = conn.cursor()
            results = []

            if hospital and not state and not blood_group:  # Case 1: Only hospital name is entered
                cur.execute('''
                            SELECT blood_grp, quantity AS total_quantity
                            FROM blood_details
                            WHERE hospital_name = %s
                            ''', (hospital,))
                results = cur.fetchall()

            elif state and not hospital and not blood_group:  # Case 2: Only State is entered
                cur.execute('''
                            SELECT blood_grp, quantity AS total_quantity
                            FROM blood_details
                            WHERE state = %s
                            ''', (state,))
                results = cur.fetchall()

            elif hospital and blood_group and not state:  # Case 3: Hospital name and blood group are chosen
                cur.execute('''
                            SELECT quantity AS total_quantity
                            FROM blood_details
                            WHERE hospital_name = %s AND blood_grp = %s
                            ''', (hospital, blood_group))
                results = cur.fetchall()

            elif state and hospital and not blood_group:  # Case 4: State and hospital name are chosen
                cur.execute('''
                            SELECT blood_grp, quantity AS total_quantity
                            FROM blood_details
                            WHERE state = %s AND hospital_name = %s
                            ''', (state, hospital))
                results = cur.fetchall()

            conn.close()
            return render_template('enquiry.html', results=results)

    return render_template('enquiry.html')

if __name__ == '__main__':
    app.run(debug=True)
