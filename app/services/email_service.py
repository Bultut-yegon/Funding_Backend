from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


async def send_password_reset_email(user_email: str, user_name: str, token: str):
    """Send password reset email with branded template."""
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-color: #f9fafb;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                border-radius: 12px;
                padding: 32px 24px;
                text-align: center;
                margin-bottom: 24px;
            }}
            .header-icon {{
                display: inline-block;
                width: 48px;
                height: 48px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 16px;
                font-size: 24px;
                font-weight: bold;
                color: white;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
            .header p {{
                color: rgba(255, 255, 255, 0.9);
                margin: 0;
                font-size: 14px;
            }}
            .content {{
                background: white;
                border-radius: 12px;
                padding: 32px;
                border: 1px solid #e5e7eb;
                margin-bottom: 24px;
            }}
            .content p {{
                margin: 0 0 16px 0;
                font-size: 16px;
                line-height: 1.5;
                color: #374151;
            }}
            .intro {{
                color: #6b7280;
                font-size: 15px;
                margin-bottom: 24px;
            }}
            .cta-section {{
                text-align: center;
                margin: 32px 0;
            }}
            .cta-button {{
                display: inline-block;
                background: #4f46e5;
                color: white;
                padding: 14px 32px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                font-size: 15px;
                border: 2px solid #4f46e5;
                transition: background 0.2s;
            }}
            .cta-button:hover {{
                background: #4338ca;
            }}
            .footer-note {{
                color: #9ca3af;
                margin: 32px 0 0 0;
                padding-top: 24px;
                border-top: 1px solid #e5e7eb;
                font-size: 13px;
                line-height: 1.5;
            }}
            .footer {{
                text-align: center;
                color: #6b7280;
                font-size: 12px;
                line-height: 1.5;
            }}
            .footer p {{
                margin: 8px 0;
            }}
            .footer a {{
                color: #4f46e5;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="header-icon">FH</div>
                <h1>FundingHub</h1>
                <p>Password Reset Request</p>
            </div>

            <!-- Content -->
            <div class="content">
                <p>Hi <strong>{user_name}</strong>,</p>
                
                <p class="intro">
                    We received a request to reset your FundingHub password. Click the button below to set a new password. This link will expire in 30 minutes for security.
                </p>

                <!-- CTA Button - This is now PROPERLY CLICKABLE -->
                <div class="cta-section">
                    <a href="{reset_link}" class="cta-button">
                        Reset Your Password
                    </a>
                </div>

                <p class="footer-note">
                    <strong>Didn't request this?</strong> You can ignore this email. If you believe this is a mistake, please contact our support team.
                </p>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p>© 2026 FundingHub. All rights reserved.</p>
                <p>
                    Need help? <a href="{settings.FRONTEND_URL}/help">Visit our help center</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Reset Your FundingHub Password – Secure Link",
        recipients=[user_email],
        body=html,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)