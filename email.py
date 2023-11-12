from datetime import datetime
import imaplib
import email
import email.header
import email.utils
import inflect
import yaml

EMAIL_POLL_INTERVAL = 20  # in seconds


def normalize_email(email):
    if not email:
        return None

    result = ""

    for token in email.split():
        if token == "dot":
            result += "."
        elif token == "at":
            result += "@"
        else:
            result += token

    return result


class Email:
    """The email class checks your emails for you
    """

    def __init__(self, account, password, server, folder, port):
        """Init"""
        self.i_engine = inflect.engine()
        self.account = account
        self.password = password
        self.server = server
        self.folder = folder
        self.port = port

    def initialize(self):
        # Start the notification service if needed
        pass

    def _nice_number(self, num):
        return self.i_engine.number_to_words(self.i_engine.ordinal(num))

    def report_email(self, new_emails):
        """Report and display the email"""
        stop_num = 10
        x = 0

        if not new_emails:
            print("No new emails.")
            return

        for idx, new_email in enumerate(list(reversed(new_emails)), start=1):
            print(f"Email {idx}:")
            print(f"  Sender: {new_email['sender']}")
            print(f"  Subject: {new_email['subject']}")
            x += 1

            if x == stop_num:
                more = input("Do you want to see more emails? (yes/no): ")
                if more.lower() == "no":
                    print("No more emails.")
                    break
                elif more.lower() == "yes":
                    stop_num += 10
                    continue

    def list_new_email(self, whitelist=None, mark_as_seen=False):
        M = imaplib.IMAP4_SSL(str(self.server), port=int(self.port))
        M.login(str(self.account), str(self.password))
        M.select(str(self.folder))
        rv, data = M.search(None, "(UNSEEN)")
        message_num = 1
        new_emails = []

        for num in data[0].split():
            rv, data = M.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            hdr = email.header.make_header(email.header.decode_header(msg['Subject']))
            sender = email.header.make_header(email.header.decode_header(msg['From']))
            from_email = email.utils.parseaddr(msg['From'])[1]
            subject = str(hdr)
            sender = str(sender).lower()

            is_in_whitelist = not whitelist or from_email in whitelist or any(
                s.lower() in sender.lower().split(" ") for s in whitelist)
            if is_in_whitelist and mark_as_seen:
                M.store(num, "+FLAGS", '\\SEEN')
            else:
                M.store(num, "-FLAGS", '\\SEEN')

            mail = {"message_num": message_num, "sender": sender, "subject": subject}
            if not is_in_whitelist:
                continue

            new_emails.append(mail)
            message_num += 1

        M.close()
        M.logout()

        return list(new_emails)

    def poll_emails(self):
        try:
            new_emails = self.list_new_email(whitelist=None, mark_as_seen=True)
        except Exception as e:
            print(f"Error: {e}")
            return

        if not new_emails:
            print("No new mail.")
            return

        stop_num = 10
        num_emails = len(new_emails)
        response = input(f"{num_emails} new emails found. Do you want to read them? (yes/no): ")

        if response.lower() == "yes":
            self.report_email(new_emails)
        else:
            print("No emails read.")

    def enquire_new_email(self):
        sender = input("Enter the email address to inquire about: ").lower()
        whitelist = [sender]

        try:
            new_emails = self.list_new_email(whitelist=whitelist, mark_as_seen=True)
        except Exception as e:
            print(f"Error: {e}")
            return

        if not new_emails:
            print(f"No new emails from {sender}.")
            return

        self.report_email(new_emails)

    def enable_email_polling(self):
        sender = normalize_email(input("Enter the sender's email address to enable email polling: "))
        whitelist = [sender]

        print("Update notification data.")

        try:
            new_emails = self.list_new_email(whitelist=whitelist, mark_as_seen=True)
        except Exception as e:
            print(f"Error: {e}")
            return

        if not new_emails:
            print("No new emails.")
            return

        self.report_email(new_emails)
        print("Settings saved.")

    def disable_email_polling(self):
        sender = normalize_email(input("Enter the sender's email address to disable email polling: "))
        whitelist = [sender]

        try:
            new_emails = self.list_new_email(whitelist=whitelist, mark_as_seen=True)
        except Exception as e:
            print(f"Error: {e}")
            return

        if not new_emails:
            print(f"No new emails from {sender}.")
            return

        self.report_email(new_emails)
        print("Settings saved.")

    def handle_email(self):
        try:
            new_emails = self.list_new_email(whitelist=None, mark_as_seen=True)
        except Exception as e:
            print(f"Error: {e}")
            return

        if not new_emails:
            print("No new emails.")
            return

        self.report_email(new_emails)


# Example of usage:
account = "bhavaniprasadt369@gmail.com"
password = "vexl zmjr bzkk ailu"
server = "imap.gmail.com"
folder = "inbox"
port = "993"

email_handler = Email(account, password, server, folder, port)

try:
    email_handler.poll_emails()
except Exception as e:
    print(f"Error: {e}")
