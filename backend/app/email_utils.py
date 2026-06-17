import smtplib
from email.mime.text import MIMEText


def send_email(salon, to_email: str | None, subject: str, body: str) -> tuple[bool, str]:
    if not to_email:
        return False, "Alıcı e-posta adresi yok"
    if not salon.smtp_host or not salon.smtp_username or not salon.smtp_password:
        return False, "SMTP ayarları eksik"
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = salon.smtp_from_email or salon.smtp_username
        msg["To"] = to_email
        with smtplib.SMTP(salon.smtp_host, salon.smtp_port or 587, timeout=10) as server:
            if salon.smtp_use_tls:
                server.starttls()
            server.login(salon.smtp_username, salon.smtp_password)
            server.send_message(msg)
        return True, ""
    except Exception as e:
        return False, str(e)
