from flask import Flask, render_template, send_from_directory, redirect, url_for, request, flash,session,jsonify
import mysql.connector
import os
import re  # Add this import for regular expressions
from urllib.parse import quote



app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = 'your_secret_key_here'
port = 4000


try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="qwerty@123",
        database="team"
    )
    cursor = db.cursor()
except mysql.connector.Error as err:
    print(f"Failed to connect to the database: {err}")

def is_strong_password(password):
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password))

@app.route('/<filename>')
def static_files(filename):
    return send_from_directory(os.path.dirname(__file__), filename)

@app.route('/')
def front_page():
    return render_template('index.html')

@app.route('/group')
def group_page():
    try:
        # Check if the 'members' table exists
        cursor.execute("SHOW TABLES LIKE 'members'")
        table_exists = cursor.fetchone()

        if table_exists:
            cursor.execute("SELECT DISTINCT group_id FROM users")
            group_id = [row[0] for row in cursor.fetchall()]
        else:
            flash("The 'members' table does not exist.", 'error')
            group_id = []

    except mysql.connector.Error as err:
        flash(f"Failed to fetch data: {err}", 'error')
        group_titles = []

    return render_template('group.html', group_id=group_id)

@app.route('/sign')
def sign_up():        
    return render_template('sign.html')

@app.route('/group')
def group():        
    return render_template('group.html')

@app.route('/sign', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        group_id = request.form['group_id']
        email = request.form['email']
        password = request.form['password']

        # Check if the group_id already exists in the database
        cursor.execute("SELECT * FROM users WHERE group_id = %s", (group_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("User already exists in this group", 'error')
            return render_template('sign.html')  

        # Check if the password is strong
        if not is_strong_password(password):
            flash("Password is not strong enough", 'error')
            return redirect(url_for('front_page'))

        # Insert user information into the database
        try:
            cursor.execute("INSERT INTO users (group_id, email, password) VALUES (%s, %s, %s)", (group_id, email, password))
            db.commit()
            flash("Registration successful!", 'success')
            return redirect(url_for('group'))  # Redirect to member page upon successful registration
        except mysql.connector.Error as err:
            db.rollback()
            flash(f"Failed to register: {err}", 'error')

    return render_template('sign.html')


@app.route('/member', methods=['GET', 'POST'])
def member():
    try:
        cursor.execute("SELECT * FROM members")
        members_data = {}

        for row in cursor.fetchall():
            group_title = row[1]
            member = {"name": row[2], "email": row[3], "contact_number": row[4], "role": row[5]}

            if group_title not in members_data:
                members_data[group_title] = []

            members_data[group_title].append(member)

        selected_group = request.args.get('group')  # Get the selected group from the URL parameters

    except mysql.connector.Error as err:
        flash(f"Failed to fetch data: {err}", 'error')
        members_data = {}
        selected_group = None

    return render_template('member.html', members_data=members_data, selected_group=selected_group)


@app.route('/form', methods=['GET', 'POST'])
def me_form():
    if request.method == 'POST':
        group_title = request.form['group_title']
        name = request.form['name']
        email = request.form['email']
        contact_number = request.form['contact_number']
        role = request.form['role']

        try:
            # Check if the name already exists in the database
            cursor.execute("SELECT * FROM members WHERE name = %s", (name,))
            existing_member = cursor.fetchone()

            if existing_member:
                ("Username already exists. Choose a different username.", 'error')
                return redirect(url_for('me_form'))

            # If the name doesn't exist, insert the new record
            cursor.execute("INSERT INTO members (group_title, name, email, contact_number, role) VALUES (%s, %s, %s, %s, %s)",
                           (group_title, name, email, contact_number, role))
            db.commit()
            flash("Data submitted successfully!", 'success')
            return redirect(url_for('group'))
        except mysql.connector.Error as err:
            db.rollback()
            flash(f"Failed to submit data: {err}", 'error')
            return redirect(url_for('group'))  # Change 'member.html' to 'member'

    return render_template('me_form.html')

@app.route('/api/member', methods=['GET'])
def api_member():
    selected_group = request.args.get('members')

    # Fetch member information for the selected group from the database
    cursor.execute("SELECT * FROM members WHERE name = %s", (selected_group,))
    members_data = []

    for row in cursor.fetchall():
        member = {
            "group_title": row[1],
            "name": row[2],
            "email": row[3],
            "contact_number": row[4],
            "role": row[5]
        }
        members_data.append(member)

    return jsonify(members_data)

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True, port=port)
