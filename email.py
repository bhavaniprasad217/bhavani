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

    def _init_(self):
        """Init"""
        self.i_engine = inflect.engine()

    def update_credentials(self):
        self.server = True

        # Update your email credentials logic here
        self.account = input("Enter your email address: ")
        self.password = input("Enter your email password: ")
        self.server = input("Enter your email server address (e.g., imap.gmail.com): ")
        self.folder = input("Enter the folder to check (e.g., inbox): ")
        self.port = input("Enter the port (e.g., 993 for IMAP over SSL): ")

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

    def list_new_email(self, account, folder, password, port, address, whitelist=None, mark_as_seen=False):
        if self.update_credentials() is False:  # No credentials
            return []

        M = imaplib.IMAP4_SSL(str(address), port=int(port))
        M.login(str(account), str(password))
        M.select(str(folder))
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
        setting = {"whitelist": None}  # Assuming no whitelist initially
        try:
            new_emails = self.list_new_email(account=self.account, folder=self.folder, password=self.password,
                                             port=self.port, address=self.server, whitelist=setting['whitelist'],
                                             mark_as_seen=True)
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
        if self.update_credentials() is False:  # No credentials
            return

        sender = input("Enter the email address to inquire about: ").lower()
        setting = {"whitelist": [sender]}

        try:
            new_emails = self.list_new_email(account=self.account, folder=self.folder, password=self.password,
                                             port=self.port, address=self.server, whitelist=setting['whitelist'],
                                             mark_as_seen=True)
        except Exception as e:
            print(f"Error: {e}")
            return

        if not new_emails:
            print(f"No new emails from {sender}.")
            return

        self.report_email(new_emails)

    def enable_email_polling(self):
        if self.update_credentials() is False:  # No credentials
            return

        sender = normalize_email(input("Enter the sender's email address to enable email polling: "))
        setting = {"whitelist": [sender]}

        if not setting:
            print("Email notification service is not active yet.")
            if sender:
                setting['whitelist'] = [sender]
            else:
                setting['whitelist'] = None

            print("Start the notification service.")
            self.poll_emails()
        else:
            if not setting['whitelist'] and sender:
                replace = input(f"Cancel looking for all and look for {sender} only? (yes/no): ")
                if replace.lower() == "yes":
                    setting['whitelist'] = [sender]
                else:
                    return
            elif not setting['whitelist'] and not sender:
                print("Already looking for all new emails.")
                return
            elif sender in setting['whitelist']:
                print(f"Already looking for emails from {sender}.")
                return
            elif setting['whitelist'] and not sender:
                replace = input(f"Cancel looking for specific sender and look for all? (yes/no): ")
                if replace.lower() == "yes":
                    setting['whitelist'] = None
                else:
                    return
            else:
                setting['whitelist'].append(sender)

            print("Update notification data.")
        print("Settings saved.")

    def disable_email_polling(self):
        setting = {"whitelist": None}

        if not setting:
            print("Email polling is not started.")
            return

        sender = normalize_email(input("Enter the sender's email address to disable email polling: "))

        if not sender:
            setting['whitelist'] = None
            print("Stop polling emails.")
            self.poll_emails()
        else:
            if not setting['whitelist']:
                print("No specific sender to stop looking for.")
                return

            if sender not in setting['whitelist']:
                print(f"Not looking for emails from {sender}.")
                return

            if len(setting['whitelist']) > 1:
                setting['whitelist'].remove(sender)
                print(f"Stop looking for emails from {sender}.")
            else:
                setting['whitelist'] = None
                print("Stop polling emails. Last email removed.")

        print("Settings saved.")

    def handle_email(self):
        try:
            new_emails = self.list_new_email(account=self.account, folder=self.folder, password=self.password,
                                             port=self.port, address=self.server)
        except Exception as e:
            print(f"Error: {e}")
            return

        if not new_emails:
            print("No new emails.")
            return

        self.report_email(new_emails)


# Example of usage:
email_handler = Email()

try:
    email_handler.update_credentials()
    email_handler.poll_emails()
except Exception as e:
    print(f"Error: {e}")
