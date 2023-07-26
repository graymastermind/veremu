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
    twilio_response.message(incoming_message)

    global lastInput
    lastInput = incoming_message

    if incoming_message.lower() == 'hi' & lastInput == '':
        twilio_response.message(
            "Welcome! Ruwa Vocational Training Centre:\n0. Register\n1. Ask a question\n2. View Notifications\n3. Update "
            "Profile\n4. Submit Assignment\n5. Assignment Results\n6. Financial Account\n7. Examination Dates\n8. Exit")
    elif lastInput == '' & incoming_message == '0':
        # Handle "Register" option
        twilio_response.message("You chose option 0 - Register")
        # Ask the user for their username
        twilio_response.message("Please enter your username:")
    elif lastInput == '' & incoming_message == '1':
        # Handle "Ask a question" option
        twilio_response.message("You chose option 1 - Ask a question")
        # Implement the logic to handle asking a question here
    elif lastInput == '' & incoming_message == '2':
        # Handle "View Notifications" option
        twilio_response.message("You chose option 2 - View Notifications")
        # Implement the logic to handle viewing notifications here
    elif lastInput == '' & incoming_message == '3':
        # Handle "Update Profile" option
        twilio_response.message("You chose option 3 - Update Profile")
        # Check if the user is registered
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM users WHERE phone_number=?", (request.form['From'],))
        existing_user = cursor.fetchone()
        if existing_user:
            # If the user is registered, prompt them to enter a new username
            twilio_response.message("Please enter your new username:")
        else:
            twilio_response.message("You are not registered. Please register first.")
    elif lastInput == '' & incoming_message == '4':
        # Handle "Submit Assignment" option
        twilio_response.message("You chose option 4 - Submit Assignment")
        # Implement the logic to handle submitting an assignment here
    elif lastInput == '' & incoming_message == '5':
        # Handle "Assignment Results" option
        twilio_response.message("You chose option 5 - Assignment Results")
    elif lastInput == '' & incoming_message == '6':
        # Handle "Financial Account" option
        twilio_response.message("You chose option 6 - Financial Account")
    elif lastInput == '' & incoming_message == '7':
        # Handle "Examination Dates" option
        twilio_response.message("You chose option 7 - Examination Dates")
    elif lastInput == '' & incoming_message == '8':
        # Handle "Exit" option
        twilio_response.message("Goodbye!")
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
