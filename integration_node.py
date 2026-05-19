import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
from compression_node import tokenize_and_squeeze

load_dotenv()
# Set your Gmail App Password in your Windows Environment Variables
GMAIL_USER = os.getenv("GMAIL_USER") 
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def fetch_important_emails(search_keyword: str = "UNSEEN") -> str:
    """Pulls recent emails, perfect for finding BCA assignments or alerts."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return "Gmail credentials missing. Tell the Director to set GMAIL_USER and GMAIL_APP_PASSWORD."
        
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        
        # Search for unread or specific keywords (like "MAIMS")
        status, messages = mail.search(None, search_keyword)
        email_ids = messages[0].split()[-5:] # Get the 5 most recent
        
        briefing = []
        for e_id in email_ids:
            res, msg = mail.fetch(e_id, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    briefing.append(f"Subject: {subject}")
                    
        mail.logout()
        return "\n".join(briefing) if briefing else "No recent emails found matching that criteria."
    except Exception as e:
        return f"Gmail bridge failed: {str(e)}"

def send_email(recipient: str, subject: str, body: str) -> str:
    """Sends an email using SMTP with Gmail App Passwords."""
    # --- THE IDENTITY INTERCEPTOR ---
    import os
    
    # If F.R.I.D.A.Y. tries to use a pronoun instead of a real address, 
    # we dynamically route it to your personal inbox from the .env file.
    target = recipient.lower().strip()
    if target in ["me", "my email", "director", "myself", "gandhar"]:
        recipient = os.getenv("GMAIL_USER")
        
        if not recipient:
            return "Failed: GMAIL_USER is missing from the .env file. I cannot find the Director's address."
    # --------------------------------

    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return "Gmail credentials missing. Tell the Director to set GMAIL_USER and GMAIL_APP_PASSWORD."

    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = recipient

        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipient, msg.as_string())

        return f"Successfully sent email to {recipient}."
    except Exception as e:
        return f"Gmail send failed: {str(e)}"

async def scrape_tradingview_asset(asset_symbol: str = "XAUUSD") -> str:
    """Uses the Playwright bridge to dynamically read live chart data."""
    from browser_node import web_hands
    
    if not web_hands.context:
        await web_hands.start()
        
    try:
        page = await web_hands.context.new_page()
        # Route directly to the TradingView symbol page
        await page.goto(f"https://www.tradingview.com/symbols/{asset_symbol}/", wait_until="domcontentloaded")
        
        # Extract the primary price element (TradingView's standard DOM class for the main price)
        price_element = await page.query_selector('.tv-symbol-price-quote__value')
        if price_element:
            price = await price_element.inner_text()
            await page.close()
            return f"The current live price of {asset_symbol} is {price}."
        else:
            await page.close()
            return f"Could not scrape the price for {asset_symbol}. The DOM may have changed."
    except Exception as e:
        return f"TradingView snipe failed: {str(e)}"