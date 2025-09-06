import smtplib

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login("r39132@gmail.com", "jntb zhxj rmin maqf")
    server.sendmail(
        "r39132@gmail.com",
        "sanand@apache.org",
        "Subject: Test Email\n\nThis is a test email from family-tree app.",
    )
print("Email sent successfully!")
