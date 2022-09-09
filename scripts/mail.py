"""
Send email with smtplib
"""

import smtplib
import os
from email.mime.text import MIMEText

class Email:
    def __init__(self):
        with open("email.config", "r") as f:
            self.sender = f.readline().strip()
            self.password = f.readline().strip()
            self.receiver = f.readline().strip()

    def send(self, subject, body):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = self.receiver

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(self.sender, self.password)
        server.sendmail(self.sender, self.receiver, msg.as_string())
        server.quit()

if __name__ == '__main__':
    email = Email()
    email.send("Test", "This is a test email")
