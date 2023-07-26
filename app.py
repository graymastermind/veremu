from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/sms", methods=["POST"])
def reply_to_sms():
    """Respond to incoming SMS with the same message."""
    incoming_message = request.form.get("Body", "").strip()
    sender_phone_number = request.form.get("From", "")

    twilio_response = MessagingResponse()
    twilio_response.message(incoming_message)

    return str(twilio_response)

if __name__ == "__main__":
    app.run(debug=True)
