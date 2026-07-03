from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from app.models.notification import Notification
from app.models.user import User
from app.models.opportunity import Opportunity
from app.models.profile import UserProfile
from app.ml.recommender import get_recommendations
from sqlalchemy.orm import Session

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

async def send_opportunity_email(user: User, opportunities: list):
    if not settings.MAIL_USERNAME:
        print("Email not configured, skipping.")
        return

    opp_list = "".join([
        f"""
        <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px; margin-bottom:12px;">
            <span style="background:#ede9fe; color:#6d28d9; font-size:12px; padding:2px 10px; border-radius:999px;">
                {opp['opportunity'].category}
            </span>
            <h3 style="margin:10px 0 4px; color:#111827;">{opp['opportunity'].title}</h3>
            <p style="color:#6b7280; font-size:14px; margin:0 0 10px;">{opp['opportunity'].description}</p>
            <a href="{opp['opportunity'].url}" style="color:#4f46e5; font-size:14px;">Apply now →</a>
        </div>
        """
        for opp in opportunities[:5]
    ])

    html = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto; padding:24px;">
        <div style="background:#4f46e5; padding:20px; border-radius:12px; text-align:center; margin-bottom:24px;">
            <h1 style="color:white; margin:0; font-size:22px;">FundingHub</h1>
            <p style="color:#c7d2fe; margin:4px 0 0; font-size:14px;">New opportunities matched for you</p>
        </div>
        <p style="color:#374151;">Hi <strong>{user.name}</strong>,</p>
        <p style="color:#6b7280;">We found new funding opportunities that match your profile:</p>
        {opp_list}
        <div style="text-align:center; margin-top:24px;">
            <a href="http://localhost:3000/recommendations"
               style="background:#4f46e5; color:white; padding:12px 28px; border-radius:8px; text-decoration:none; font-weight:600;">
               View all recommendations
            </a>
        </div>
        <p style="color:#9ca3af; font-size:12px; text-align:center; margin-top:24px;">
            FundingHub · Nairobi, Kenya
        </p>
    </div>
    """

    message = MessageSchema(
        subject="🎯 New funding opportunities matched for you",
        recipients=[user.email],
        body=html,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def notify_users_of_new_opportunities(db: Session):
    users = db.query(User).all()
    opportunities = db.query(Opportunity).all()
    notified = 0

    for user in users:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            continue

        recommendations = get_recommendations(profile, opportunities, top_k=5)
        if not recommendations:
            continue

        try:
            await send_opportunity_email(user, recommendations)

            notification = Notification(
                user_id=user.id,
                message=f"We found {len(recommendations)} new opportunities matching your profile.",
            )
            db.add(notification)
            notified += 1
        except Exception as e:
            print(f"Failed to notify {user.email}: {e}")

    db.commit()
    print(f"Notified {notified} users.")
    return notified
