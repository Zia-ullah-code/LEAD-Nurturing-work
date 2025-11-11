import imaplib, email

imap = imaplib.IMAP4_SSL("imap.gmail.com")
imap.login("laybaa.fiaz@gmail.com", "niwk tnqb yaec sryf")
imap.select("INBOX")

status, messages = imap.search(None, "ALL")
print("Search status:", status)
print("Messages:", messages)

for num in messages[0].split():
    _, data = imap.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(data[0][1])
    print("From:", msg["From"])
    print("Subject:", msg["Subject"])
    break  # just show first message
