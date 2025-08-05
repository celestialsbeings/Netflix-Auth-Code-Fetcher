import os
import re
import re
import html
import poplib
import poplib
import quopri
from email import parser
from email import parser
from dotenv import load_dotenv
load_dotenv()

pop3_server = os.getenv("POP3_SERVER")
pop3_port = int(os.getenv("POP3_PORT"))
mailbox = poplib.POP3_SSL(pop3_server, pop3_port)


def extract_signin_otp(username, password):
    mailbox = poplib.POP3_SSL(pop3_server, pop3_port)  # Create new connection
    mailbox.user(username)
    mailbox.pass_(password)

    num_messages = len(mailbox.list()[1])
    num_to_fetch = min(5, num_messages)
    
    for i in range(num_messages, num_messages - num_to_fetch, -1):
        response, lines, octets = mailbox.retr(i)
        msg_content = b"\r\n".join(lines).decode("utf-8", errors="replace")
        msg = parser.Parser().parsestr(msg_content)
        
        # Handle multipart
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True)
                    if body:
                        data = body.decode("utf-8", errors="replace")
                        otp_match = re.search(r'>\s*(\d{4})\s*</td>', data)
                        if otp_match:  # Add error handling
                            mailbox.quit()
                            return otp_match.group(1)
    
    mailbox.quit()
    return None  # Return None if no OTP found

# extract_login_otp(username, password)
def extract_household_otp(username, password):
    mailbox = poplib.POP3_SSL(pop3_server, pop3_port)  # Use environment variables
    mailbox.user(username)
    mailbox.pass_(password)

    num_messages = len(mailbox.list()[1])
    num_to_fetch = min(5, num_messages)

    for i in range(num_messages, num_messages - num_to_fetch, -1):
        response, lines, octets = mailbox.retr(i)
        msg_content = b"\r\n".join(lines).decode("utf-8", errors="replace")
        msg = parser.Parser().parsestr(msg_content)

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if content_type == "text/html" and "attachment" not in content_disposition:
                    # Decode quoted-printable HTML
                    raw_html = part.get_payload(decode=False)
                    decoded_html = quopri.decodestring(raw_html).decode("utf-8", errors="replace")

                    # Unescape HTML entities like &amp; -> &
                    clean_html = html.unescape(decoded_html)

                    # Extract link that includes "update-primary-location" and nftoken=
                    match = re.search(r'https://www\.netflix\.com/account/update-primary-location\?[^"\s>]+', clean_html)

                    if match:
                        return match.group(0)

        else:
            # Non-multipart email (rare)
            raw_html = msg.get_payload(decode=False)
            decoded_html = quopri.decodestring(raw_html).decode("utf-8", errors="replace")
            clean_html = html.unescape(decoded_html)
            match = re.search(r'https://www\.netflix\.com/account/update-primary-location\?[^"\s>]+', clean_html)
            if match:
                return match.group(0)

    mailbox.quit()
    return False

def extract_temp_auth_otp(username, password):
    mailbox = poplib.POP3_SSL(pop3_server, pop3_port)  # Use environment variables
    mailbox.user(username)
    mailbox.pass_(password)

    num_messages = len(mailbox.list()[1])
    num_to_fetch = min(5, num_messages)

    for i in range(num_messages, num_messages - num_to_fetch, -1):
        response, lines, octets = mailbox.retr(i)
        msg_content = b"\r\n".join(lines).decode("utf-8", errors="replace")
        msg = parser.Parser().parsestr(msg_content)

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                if content_type == "text/html" and "attachment" not in content_disposition:
                    raw_body = part.get_payload(decode=False)

                    # Decode quoted-printable
                    body_decoded = quopri.decodestring(raw_body)
                    html_str = body_decoded.decode("utf-8", errors="replace")

                    # Unescape HTML entities (&amp;, =3D, etc.)
                    clean_html = html.unescape(html_str)

                    # Extract OTP (if in format: > 1234 </td>)
                    otp_match = re.search(r'>\s*(\d{4})\s*</td>', clean_html)
                    if otp_match:
                        return otp_match.group(1)

        else:
            # Handle non-multipart (rare for HTML OTPs)
            body = msg.get_payload(decode=True)
            if body:
                html_str = body.decode("utf-8", errors="replace")
                clean_html = html.unescape(quopri.decodestring(html_str).decode("utf-8", errors="replace"))
                otp_match = re.search(r'>\s*(\d{4})\s*</td>', clean_html)
                if otp_match:
                    return otp_match.group(1)

    return None
