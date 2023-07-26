import os

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import random
import datetime
from flask import Flask, request, g
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)


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
        lastInput = incoming_message
        twilio_response.message(
            "Welcome! Ruwa Vocational Training Centre:\n0. Register\n1. Ask a question\n2. View Notifications\n3. Update "
            "Profile\n4. Submit Assignment\n5. Assignment Results\n6. Financial Account\n7. Examination Dates\n8. Exit")

    #     Registration
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '0':
        lastInput = incoming_message
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
    # End Registration register user


    # Asking Questioms
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '1':
        lastInput = incoming_message
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
    # End Questions


    # Deal With Notifications
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '2':
        lastInput = incoming_message
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

        # Send the notifications to the user
        twilio_response.message(message)
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '11':
        lastInput = incoming_message
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
        lastInput = incoming_message
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
        lastInput = incoming_message
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
                twilio_response.message("No file was submitted. Please try again.")
        else:
            # If no file was submitted, inform the user
            twilio_response.message("No file was submitted. Please try again.")

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

        twilio_response.message(message)
    # End Submit assignment


    # Assignment Results
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '5':
        lastInput = incoming_message
        # Handle "Assignment Results" option
        twilio_response.message("You chose option 5 - Assignment Results")
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '6':
        lastInput = incoming_message
        # Handle "Financial Account" option
        twilio_response.message("You chose option 6 - Financial Account")
        lastInput = incoming_message
    elif (lastInput == '' or lastInput == 'hi') and incoming_message == '7':
        lastInput = incoming_message
        # Handle "Examination Dates" option
        twilio_response.message("You chose option 7 - Examination Dates")
    elif incoming_message == '8':
        lastInput = incoming_message
        # Handle "Exit" option
        twilio_response.message("Goodbye!")
    elif incoming_message.lower() == "reset":
        # Handle "reset" command to reset lastInput to an empty string
        reset_last_input()
        twilio_response.message("Command reset successful. lastInput is now empty.")

    else:
        # Check if the user is in the registration process
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM users WHERE phone_number=?", (request.form['From'],))
        existing_user = cursor.fetchone()
        if existing_user and not existing_user[1]:
            # If the user is in the registration process and hasn't entered a username yet
            # Store the username and user ID in the database
            username = incoming_message
            user_id = generate_user_id()
            cursor.execute("UPDATE users SET username=?, user_id=? WHERE phone_number=?",
                           (username, user_id, request.form['From']))
            get_db().commit()
            twilio_response.message(f"Welcome, {username}! Your user ID is {user_id}.")
        elif existing_user and existing_user[1]:
            # If the user is already registered and wants to update their username
            new_username = incoming_message
            cursor.execute("UPDATE users SET username=? WHERE phone_number=?", (new_username, request.form['From']))
            get_db().commit()
            twilio_response.message(f"Your username has been updated to {new_username}.")
        else:
            # Handle invalid input
            twilio_response.message("Invalid choice. Please try again.")

    return str(twilio_response)


if __name__ == "__main__":
    app.run(debug=True)
