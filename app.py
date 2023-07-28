import os
import sqlite3
import random
import datetime
from flask import Flask, request, g
from twilio.twiml.messaging_response import MessagingResponse
import poe
import logging

app = Flask(__name__)

app.config['TIMEOUT'] = 300  # set the timeout to 60 seconds
# poe settings
#send a message and immediately delete it
token = "mXqoIb80IJEihKjz_KVSbA%3D%3D"
poe.logger.setLevel(logging.INFO)
client = poe.Client(token)
global response
response = ''

# end poe

# Connect to the SQLite database
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("chatbot.db")
    return db


# Create tables for notifications, users, and assignments (if they don't exist)
def create_tables():
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                phone_number TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                subject TEXT NOT NULL,
                file_storage TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                phone_number TEXT NOT NULL,
                content TEXT NOT NULL
            )
            """)

        get_db().commit()


# Initialize the database
create_tables()

# Create table for assignment results
def create_assignment_results_table():
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignment_results (
                id INTEGER PRIMARY KEY,
                subject TEXT NOT NULL,
                mark INTEGER NOT NULL
            )
        """)

        get_db().commit()

create_assignment_results_table()


# Create table for examination dates
def create_exam_dates_table():
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exam_dates (
                id INTEGER PRIMARY KEY,
                subject_name TEXT NOT NULL,
                exam_date DATE NOT NULL
            )
        """)

        get_db().commit()


create_exam_dates_table()


# Create table for account information
def create_account_information_table():
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_information (
                id INTEGER PRIMARY KEY,
                phone_number TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL
            )
        """)

        get_db().commit()

# Initialize the database and create the account information table
create_account_information_table()

def generate_user_id():
    # Generate a user ID prefixed with the current year and a random 3-digit number
    current_year = str(datetime.datetime.now().year)
    random_number = str(random.randint(100, 999))
    random_letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    user_id = current_year + random_number + random_letter
    return user_id


def get_notifications():
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("SELECT id, content FROM notifications")
        notifications = cursor.fetchall()
        return notifications

def reset_last_input():
    global lastInput
    lastInput = ""

# Close the database connection when the app is finished
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


lastInput = ''
@app.route("/sms", methods=["POST"])
def reply_to_sms():
    """Respond to incoming SMS with the same message."""
    incoming_message = request.form.get("Body", "").strip()
    sender_phone_number = request.form.get("From", "")

    twilio_response = MessagingResponse()

    global lastInput

    if incoming_message.lower() == 'hi' and (lastInput == '' or lastInput == 'hi'):
        lastInput = incoming_message.lower()
        twilio_response.message(
            "Welcome! Ruwa Vocational Training Centre:\n0. Register\n1. Ask a question\n2. View Notifications\n3. Update "
            "Profile\n4. Submit Assignment\n5. Assignment Results\n6. Financial Account\n7. Examination Dates\n(research). Use command research to ask any question\n8. Exit")
    elif incoming_message.lower() == "reset":
        # Handle "reset" command to reset lastInput to an empty string
        reset_last_input()
        twilio_response.message("Command reset successful. lastInput is now empty.")
    #     Registration
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '0':
        lastInput = incoming_message.lower()
        # Handle "Register" option
        twilio_response.message("You chose option 0 - Register")
        # Ask the user for their username
        twilio_response.message("Please enter your username:")
    elif lastInput == '0':
        # Save the username and phone number to the database
        username = incoming_message
        user_id = generate_user_id()
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, phone_number, user_id) VALUES (?, ?, ?)",
                           (username, sender_phone_number, user_id))
            conn.commit()
            twilio_response.message("Registration successful! Your user ID is: {}".format(user_id))
        except sqlite3.IntegrityError:
            twilio_response.message("Phone number already registered.")
        finally:
            lastInput = ''
            twilio_response.message(
                "Welcome! Ruwa Vocational Training Centre:\n0. Register\n1. Ask a question\n2. View Notifications\n3. Update "
                "Profile\n4. Submit Assignment\n5. Assignment Results\n6. Financial Account\n7. Examination Dates\n8. Exit")
    elif incoming_message == '9':
        # Handle "View Users" option
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        user_list = "\n".join([f"ID: {user[0]}, Username: {user[1]}, Phone Number: {user[2]}" for user in users])
        twilio_response.message(f"Users:\n{user_list}")
        reset_last_input()
    # End Registration register user


    # Asking Questioms
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '1':
        lastInput = incoming_message.lower()
        # Handle "Ask a question" option
        twilio_response.message("You chose option 1 - Ask a question")
        # Implement the logic to handle asking a question here
    elif lastInput == '1':
        # Save the question to the database
        question_content = incoming_message
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO questions (phone_number, content) VALUES (?, ?)",
                           (sender_phone_number, question_content))
            conn.commit()
            twilio_response.message("Question submitted successfully!")
        except sqlite3.Error:
            twilio_response.message("Failed to submit the question. Please try again.")
        finally:
            lastInput = ''
    elif incoming_message == '10':
        # Handle "View All Questions" option
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()
        question_list = "\n".join(
            [f"ID: {question[0]}, Phone Number: {question[1]}, Content: {question[2]}" for question in questions])
        twilio_response.message(f"All Questions:\n{question_list}")
        reset_last_input()
    # End Questions


    # Deal With Notifications
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '2':
        lastInput = incoming_message.lower()
        # Handle "View Notifications" option
        twilio_response.message("You chose option 2 - View Notifications")
        # Implement the logic to handle viewing notifications here
        # Query the notifications from the database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, content FROM notifications")
        notifications = cursor.fetchall()

        # Check if there are any notifications
        if notifications:
            message = "Notifications:\n"
            for notification in notifications:
                message += f"{notification[0]}. {notification[1]}\n"
        else:
            message = "No notifications found."
        reset_last_input()
        # Send the notifications to the user
        twilio_response.message(message)

    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '11':
        lastInput = incoming_message.lower()
        # Handle "Notifications" option
        twilio_response.message("You chose option 11 - Create Notification")
        # Ask the user for the notification content
        twilio_response.message("Please enter the notification content:")
    elif lastInput == '11':
        # Save the notification to the database
        with app.app_context():
            cursor = get_db().cursor()
            cursor.execute("INSERT INTO notifications (content) VALUES (?)", (incoming_message,))
            get_db().commit()
            twilio_response.message("Notification saved successfully.")
        lastInput = ''
    # End Dealing with Notifictions


    # Update Profile
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '3':
        lastInput = incoming_message.lower()
        # Handle "Update Profile" option
        twilio_response.message("You chose option 3 - Update Profile")
        # Ask the user for their new username
        twilio_response.message("Please enter your new username:")
    elif lastInput == '3':
        # Update the user's profile in the database
        with app.app_context():
            cursor = get_db().cursor()
            # Get the user's current phone number to identify the user
            cursor.execute("SELECT * FROM users WHERE phone_number=?", (sender_phone_number,))
            user = cursor.fetchone()

            if user:
                new_username = incoming_message
                # Update the user's username in the database
                cursor.execute("UPDATE users SET username=? WHERE phone_number=?", (new_username, sender_phone_number))
                get_db().commit()
                twilio_response.message("Your profile has been updated successfully.")
            else:
                twilio_response.message("User not found. Please register first.")
        lastInput = ''
    # Update Profile



    # Code to submit assignment
    elif (lastInput == "" or lastInput == "hi") and incoming_message == "4":
        lastInput = incoming_message.lower()
        # Handle "Submit Assignment" option
        twilio_response.message("You chose option 4 - Submit Assignment")
        # Implement the logic to handle submitting an assignment here

        # Ask the user to submit the assignment file
        twilio_response.message("Please submit your assignment file:")

    elif lastInput == "4":
        # Save the submitted assignment file
        if request.files:
            file = request.files["MediaUrl0"]
            if file:
                # Generate a unique filename for the assignment
                filename = f"assignment_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

                twilio_response.message("File found")
                # Save the assignment details to the database
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO assignments (subject, file_storage) VALUES (?, ?)",
                               ("Mathematics", filename))  # You can change the subject accordingly
                conn.commit()

                # Send confirmation message to the user
                twilio_response.message("Your assignment has been submitted successfully.")
            else:
                # If no file was submitted, inform the user
                twilio_response.message("Your assignment has been submitted successfully. - +")
        else:
            # If no file was submitted, inform the user
            twilio_response.message("Your assignment has been submitted successfully.")

        # Reset the lastInput to empty to allow for other operations
        lastInput = ""

    elif incoming_message == "12":
        # View all assignment files
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, file_storage FROM assignments")
        assignments = cursor.fetchall()

        if assignments:
            message = "Available assignments:\n"
            for assignment in assignments:
                message += f"{assignment[0]}. {assignment[1]}\n"
        else:
            message = "No assignments found."
        reset_last_input()
        twilio_response.message(message)
    # End Submit assignment


    # Assignment Results
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '5':
        lastInput = incoming_message.lower()
        # Handle "Assignment Results" option
        twilio_response.message("You chose option 5 - Assignment Results")
        # Implement the logic to retrieve assignment results here
        # Query the database and retrieve all assignment results
        with app.app_context():
            cursor = get_db().cursor()
            cursor.execute("SELECT * FROM assignment_results")
            assignment_results = cursor.fetchall()

        # Format and send the assignment results to the user
        result_message = "Assignment Results:\n"
        for result in assignment_results:
            result_message += f"ID: {result[0]}, Subject: {result[1]}, Mark: {result[2]}\n"
        reset_last_input()
        twilio_response.message(result_message)

    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '13':
        lastInput = incoming_message.lower()
        # Handle "Submit Assignment Results" option
        twilio_response.message("You chose option 13 - Submit Assignment Results (Subject, Mark)")
        # Implement the logic to submit assignment results here

    elif lastInput == '13':
        # Parse the incoming message to get subject and mark
        parts = incoming_message.split(",")
        if len(parts) == 2 and parts[1].strip().isdigit():
            subject = parts[0].strip()
            mark = int(parts[1].strip())

            # Insert the assignment result into the database
            with app.app_context():
                cursor = get_db().cursor()
                cursor.execute("INSERT INTO assignment_results (subject, mark) VALUES (?, ?)", (subject, mark))
                get_db().commit()
            twilio_response.message("Assignment result submitted successfully.")
            lastInput = ''
        else:
            twilio_response.message("Invalid format for submitting assignment result. Please use: SUBJECT, MARK")
    # End Assignment results


    # Financial Account
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '6':
        lastInput = incoming_message.lower()
        # Handle "Financial Account" option
        twilio_response.message("You chose option 6 - Financial Account")

    # End Financial


    # Exam Date

    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '7':
        lastInput = incoming_message.lower()
        # Handle "View Examination Dates" option
        twilio_response.message("You chose option 7 - View Examination Dates")
        # Implement the logic to retrieve examination dates here
        # Query the database and retrieve all examination dates
        with app.app_context():
            cursor = get_db().cursor()
            cursor.execute("SELECT * FROM exam_dates")
            exam_dates = cursor.fetchall()

        # Format and send the examination dates to the user
        result_message = "Examination Dates:\n"
        for date in exam_dates:
            result_message += f"ID: {date[0]}, Subject: {date[1]}, Date: {date[2]}\n"

        twilio_response.message(result_message)

    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '14':
        lastInput = incoming_message.lower()
        # Handle "Create Examination Date" option
        twilio_response.message("You chose option 14 - Create Examination Date")
        # Implement the logic to create an examination date here

    elif lastInput == '14':
        # Parse the incoming message to get subject name and date
        parts = incoming_message.split(",")
        if len(parts) == 2:
            subject_name = parts[0].strip()
            exam_date = parts[1].strip()

            # Insert the examination date into the database
            with app.app_context():
                cursor = get_db().cursor()
                cursor.execute("INSERT INTO exam_dates (subject_name, exam_date) VALUES (?, ?)",
                               (subject_name, exam_date))
                get_db().commit()
            twilio_response.message("Examination date created successfully.")
            lastInput = ''
        else:
            twilio_response.message("Invalid format for creating examination date. Please use: SUBJECT NAME, DATE")

    # End Exam Date

    # Do Research
    elif (lastInput == '' or lastInput == 'hi') and incoming_message.lower() == 'research':
        lastInput = incoming_message
        # Handle "Research" option
        twilio_response.message("You chose option 'research'. Please enter your question:")

    elif lastInput == 'research':
        # Process the research question using the ChatGPT API
        lastInput = ''  # Reset lastInput so that the next message is treated as a new input
        research_question = incoming_message.strip()
        try:
            message = "What is science?"
            for chunk in client.send_message("capybara", message, with_chat_break=True):
                # print(chunk["text_new"], end="", flush=True)
                response = response + chunk["text_new"]

            print("response :", response)
            # delete the 3 latest messages, including the chat break
            client.purge_conversation("capybara", count=3)

            twilio_response.message(f"Here is your answer:\n{response}")
            reset_last_input()
        except Exception as e:
            # twilio_response.message("An error occurred while processing your question. Please try again later.")
            twilio_response.message(e)
    # End Research

    elif incoming_message == '8':
        lastInput = incoming_message.lower()
        # Handle "Exit" option
        twilio_response.message("Goodbye!")
        reset_last_input()

    else:
        pass

    return str(twilio_response)


if __name__ == "__main__":
    app.run(debug=True)
