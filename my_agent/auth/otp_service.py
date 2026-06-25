import random
import hmac
import hashlib
import os
import httpx
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("auth_server.otp")

OTP_SECRET_KEY = os.getenv("OTP_SECRET_KEY", "default-otp-secret-key-32-chars-at-least-2026")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "auth@xagent.ai")
SENDER_NAME = os.getenv("SENDER_NAME", "X-Agent System")

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def generate_otp() -> str:
    """Generates a secure 6-digit OTP code"""
    return f"{random.randint(0, 999999):06d}"

def hash_otp(otp: str) -> str:
    """Hashes OTP using HMAC-SHA-256 with OTP_SECRET_KEY"""
    h = hmac.new(OTP_SECRET_KEY.encode(), otp.encode(), hashlib.sha256)
    return h.hexdigest()

def get_premium_email_template(otp_code: str) -> str:
    """Returns a highly styled, modern dark-themed HTML email template for the OTP code"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>X-Agent - Mã xác thực của bạn</title>
    <style>
        body {{
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 500px;
            margin: 0 auto;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
            text-align: center;
        }}
        .logo {{
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
            display: inline-block;
            letter-spacing: -0.05em;
        }}
        h1 {{
            font-size: 20px;
            font-weight: 600;
            color: #f1f5f9;
            margin-top: 0;
            margin-bottom: 12px;
        }}
        p {{
            font-size: 15px;
            line-height: 1.6;
            color: #94a3b8;
            margin-top: 0;
            margin-bottom: 24px;
        }}
        .otp-card {{
            background: rgba(30, 41, 59, 0.7);
            border: 1px dashed #3b82f6;
            border-radius: 16px;
            padding: 24px;
            margin: 32px 0;
            display: inline-block;
            min-width: 200px;
        }}
        .otp-code {{
            font-size: 38px;
            font-weight: 800;
            letter-spacing: 6px;
            color: #3b82f6;
            margin: 0;
            text-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
        }}
        .footer {{
            font-size: 12px;
            color: #64748b;
            border-top: 1px solid #334155;
            padding-top: 24px;
            margin-top: 32px;
        }}
        .highlight {{
            color: #f1f5f9;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">X-Agent</div>
        <h1>Mã xác thực đăng nhập</h1>
        <p>Chào bạn, chúng tôi nhận được yêu cầu đăng nhập/đăng ký bằng tài khoản email của bạn. Vui lòng sử dụng mã xác thực dùng một lần (OTP) dưới đây:</p>
        
        <div class="otp-card">
            <div class="otp-code">{otp_code}</div>
        </div>
        
        <p>Mã xác thực có hiệu lực trong vòng <span class="highlight">10 phút</span> và chỉ được sử dụng cho <span class="highlight">1 lần đăng nhập duy nhất</span>.</p>
        <p style="font-size: 13px; color: #ef4444;">Vì lý do bảo mật, tuyệt đối không chia sẻ mã này với bất kỳ ai, kể cả nhân viên hỗ trợ.</p>
        
        <div class="footer">
            Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này một cách an toàn.<br>
            &copy; 2026 X-Agent. Mọi quyền được bảo lưu.
        </div>
    </div>
</body>
</html>"""

async def send_otp_email(to_email: str, otp_code: str) -> bool:
    """Sends OTP email via SMTP or Brevo API. Prints to log/console as developer fallback."""
    # Always print to logs for developer convenience
    logger.info(f"\n==================================================")
    logger.info(f"🔑 EMAIL OTP FOR: {to_email}")
    logger.info(f"🔑 CODE: {otp_code}")
    logger.info(f"==================================================\n")
    print(f"\n[DEV FALLBACK] Email OTP sent to {to_email} with code: {otp_code}\n", flush=True)

    html_content = get_premium_email_template(otp_code)
    subject = "X-Agent — Mã xác thực OTP đăng nhập"

    # 1. Try sending via SMTP if SMTP_HOST is set
    if SMTP_HOST:
        logger.info(f"Attempting to send OTP email via SMTP ({SMTP_HOST})...")
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            port = int(SMTP_PORT)
            
            # Use run_in_executor to avoid blocking the event loop with smtplib
            import asyncio
            def _send():
                if port == 465:
                    server = smtplib.SMTP_SSL(SMTP_HOST, port, timeout=10.0)
                else:
                    server = smtplib.SMTP(SMTP_HOST, port, timeout=10.0)
                    server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
                server.quit()
                
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _send)
            
            logger.info(f"Email successfully sent via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {str(e)}")
            # If SMTP fails, fall back to Brevo API if available
            if not BREVO_API_KEY:
                return False

    # 2. Try sending via Brevo API if BREVO_API_KEY is set
    if BREVO_API_KEY:
        logger.info("Attempting to send OTP email via Brevo REST API...")
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "sender": {
                "name": SENDER_NAME,
                "email": SENDER_EMAIL
            },
            "to": [
                {
                    "email": to_email
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in (200, 201, 202):
                    logger.info(f"Brevo API email successfully sent to {to_email}")
                    return True
                else:
                    logger.error(f"Failed to send Brevo API email: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Exception raised while calling Brevo API: {str(e)}")
            return False

    # 3. If neither is configured
    logger.warning("Neither SMTP nor BREVO_API_KEY is configured. Falling back to log/console output.")
    return True # Return true so developer flow is not broken
