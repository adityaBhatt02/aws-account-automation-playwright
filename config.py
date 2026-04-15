from dotenv import load_dotenv
import os

load_dotenv()

CONFIG = {
    "EMAIL": os.getenv("MAIN_EMAIL"),
    "APP_PASSWORD": os.getenv("APP_PASSWORD"),
    "PASSWORD": os.getenv("Password_test"),
    "ACCOUNT_NAME": os.getenv("ACCOUNT_NAME"),
    "phoneNo": os.getenv("phoneNo"),

    # ✅ ADD THESE
    "FULL_NAME": os.getenv("FULL_NAME"),
    "COMPANY_NAME": os.getenv("COMPANY_NAME"),
    "ADDRESS_LINE1": os.getenv("ADDRESS_LINE1"),
    "CITY": os.getenv("CITY"),
    "STATE": os.getenv("STATE"),
    "POSTAL_CODE": os.getenv("POSTAL_CODE"),

    # billing
    "CardNo": os.getenv("CardNo"),
    "cvvNo": os.getenv("cvvNo"),
    "nameOnCard": os.getenv("nameOnCard"),
    "cardExpiryMonth": os.getenv("cardExpiryMonth"),
    "cardExpiryYear": os.getenv("cardExpiryYear"),

    # KYC
    "panNo_TTN": os.getenv("panNo_TTN"),
    "doi_ttn": os.getenv("doi_ttn"),
}