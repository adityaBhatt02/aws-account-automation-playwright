import os
import time
import random
import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from config import CONFIG
from email_utils import get_email_otp_simple


# CONSTANTS
MAX_ACCOUNTS = 10
OUTPUT_FILE = "generated_accounts.csv"

ACCOUNT_TYPES = {
    "1": "TTN",
    "2": "TTN_US",
    "3": "CK",
}

PROFILES = {
    "TTN": {
        "FULL_NAME":     CONFIG.get("FULL_NAME", ""),
        "COMPANY_NAME":  os.getenv("TTN_NAME", "To The New Private Limited"),
        "ADDRESS_LINE1": CONFIG.get("ADDRESS_LINE1", ""),
        "CITY":          CONFIG.get("CITY", ""),
        "STATE":         CONFIG.get("STATE", ""),
        "POSTAL_CODE":   CONFIG.get("POSTAL_CODE", ""),
        "COUNTRY":       "India",
        "phoneNo":       CONFIG.get("phoneNo", ""),
        "panNo":         os.getenv("panNo_TTN", ""),
        "doi":           os.getenv("doi_ttn", ""),
    },
    "TTN_US": {
        "FULL_NAME":     os.getenv("US_FULL_NAME", CONFIG.get("FULL_NAME", "")),
        "COMPANY_NAME":  os.getenv("TTN_NAME", "To The New Private Limited"),
        "ADDRESS_LINE1": os.getenv("US_ADDRESS_LINE1", ""),
        "CITY":          os.getenv("US_CITY", ""),
        "STATE":         os.getenv("US_STATE", ""),
        "POSTAL_CODE":   os.getenv("US_POSTAL_CODE", ""),
        "COUNTRY":       "United States",
        "phoneNo":       os.getenv("US_PHONE", ""),
        "panNo":         "",
        "doi":           "",
    },
    "CK": {
        "FULL_NAME":     CONFIG.get("FULL_NAME", ""),
        "COMPANY_NAME":  os.getenv("CK_NAME", "Cloudkeeper India Private Limited"),
        "ADDRESS_LINE1": CONFIG.get("ADDRESS_LINE1", ""),
        "CITY":          CONFIG.get("CITY", ""),
        "STATE":         CONFIG.get("STATE", ""),
        "POSTAL_CODE":   CONFIG.get("POSTAL_CODE", ""),
        "COUNTRY":       "India",
        "phoneNo":       CONFIG.get("phoneNo", ""),
        "panNo":         os.getenv("panNo_Ck", ""),
        "doi":           os.getenv("doi_ck", ""),
    },
}

MONTH_MAP = {
    "01": "January",  "02": "February", "03": "March",
    "04": "April",    "05": "May",      "06": "June",
    "07": "July",     "08": "August",   "09": "September",
    "10": "October",  "11": "November", "12": "December",
}


# PROMPTS
def prompt_inputs():
    print("\n" + "="*50)
    print("       AWS ACCOUNT AUTO-CREATOR")
    print("="*50)

    while True:
        try:
            count = int(input(f"\nHow many accounts do you want to create? (1-{MAX_ACCOUNTS}): ").strip())
            if 1 <= count <= MAX_ACCOUNTS:
                break
            print(f"❌ Enter a number between 1 and {MAX_ACCOUNTS}.")
        except ValueError:
            print("❌ Invalid input. Enter a number.")

    print("\nSelect account type:")
    print("  1 → TTN    (India)")
    print("  2 → TTN_US (United States)")
    print("  3 → CK     (India)")

    while True:
        choice = input("\nEnter 1, 2 or 3: ").strip()
        if choice in ACCOUNT_TYPES:
            account_type = ACCOUNT_TYPES[choice]
            break
        print("❌ Invalid choice. Enter 1, 2 or 3.")

    print(f"\n[✓] Creating {count} account(s) — Type: {account_type}")
    return count, account_type


# CSV LOGGER
def init_csv():
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Password", "Account Type", "Status", "Timestamp"])
    print(f"[✓] Output file: {OUTPUT_FILE}")


def log_result(email, password, account_type, status):
    with open(OUTPUT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            email, password, account_type, status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    print(f"[✓] Logged: {email} → {status}")


# HELPERS
def pause(a=1, b=3):
    time.sleep(random.uniform(a, b))


def slow_type(locator, text):
    locator.click(delay=random.randint(150, 400))
    time.sleep(random.uniform(0.4, 0.8)) # Pause before typing
    for ch in text:
        locator.type(ch, delay=random.uniform(200, 450)) # Very slow typing
        if random.random() < 0.15: # 15% chance to hesitate
            time.sleep(random.uniform(0.5, 1.5))


def generate_alias_email(base_email):
    name, domain = base_email.split("@")
    tag = random.randint(10000, 99999)
    return f"{name}+aws{tag}@{domain}"


def get_otp_from_email(wait_first=25):
    print(f"[*] Waiting {wait_first}s for OTP email...")
    time.sleep(wait_first)
    for i in range(15):
        print(f"[INFO] OTP attempt {i+1}/15")
        otp = get_email_otp_simple(CONFIG["EMAIL"], CONFIG["APP_PASSWORD"])
        if otp:
            print(f"[✓] OTP: {otp}")
            return otp
        time.sleep(5)
    return None


def dismiss_cookie_banner(page):
    try:
        btn = page.locator(
            'button[data-id="awsccc-cb-btn-accept"], .awsccc-u-btn-primary'
        ).first
        btn.wait_for(timeout=5000)
        btn.click(delay=random.randint(150, 400))
        print("[✓] Cookie banner dismissed")
        pause(1, 2)
    except Exception:
        pass


def select_dropdown(page, btn_selector, value, is_month=False):
    display_value = MONTH_MAP.get(value, value) if is_month else value
    btn = page.locator(btn_selector)
    btn.wait_for(timeout=10000)
    btn.click(delay=random.randint(150, 400))
    pause(1, 2)

    all_opts = page.locator('[role="option"], [role="listbox"] li').all()
    print(f"[DEBUG] Dropdown {len(all_opts)} opts, looking for '{display_value}'")

    for opt in all_opts:
        try:
            txt = opt.inner_text().strip().split("\n")[0].strip()
            if txt == display_value:
                opt.click(delay=random.randint(150, 400))
                print(f"[✓] Selected '{display_value}'")
                return True
        except Exception:
            continue

    print(f"⚠️ Could not select '{display_value}'")
    return False


def wait_for_any(page, selectors, timeout=20000):
    """Wait for any of the given CSS/text selectors and return which one matched."""
    start = time.time()
    while (time.time() - start) * 1000 < timeout:
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible():
                    return sel
            except Exception:
                pass
        time.sleep(1)
    return None


# STEP 1: SIGNUP
def signup(page, alias_email, account_type):
    print(f"\n===== STEP 1: SIGNUP [{account_type}] | {alias_email} =====")

    page.goto("https://signin.aws.amazon.com/signup?request_type=register")
    page.wait_for_load_state("domcontentloaded")
    pause(5, 8)

    page.wait_for_selector("#emailAddress", timeout=30000)

    try:
        if page.locator('text=Sorry, there was an error').is_visible():
            print("⚠️ Error on load — reloading...")
            page.reload()
            page.wait_for_load_state("domcontentloaded")
            pause(5, 8)
    except Exception:
        pass

    email_input = page.locator("#emailAddress")
    email_input.click(delay=random.randint(150, 400))
    email_input.fill("")
    slow_type(email_input, alias_email)
    pause(1, 2)

    account_name = f"{CONFIG['ACCOUNT_NAME']}-{random.randint(1000, 9999)}"
    name_input = page.locator("#accountName")
    name_input.click(delay=random.randint(150, 400))
    slow_type(name_input, account_name)
    print(f"[*] Account name: {account_name}")
    pause(1, 2)

    btn = page.locator('[data-testid="collect-email-submit-button"]')
    btn.hover()
    pause(0.5, 1)
    btn.click(delay=random.randint(150, 400))
    pause(3, 5)

    try:
        if page.locator('text=Sorry, there was an error').is_visible():
            raise Exception("AWS blocked signup after submit")
    except Exception as e:
        if "blocked" in str(e):
            raise

    page.wait_for_selector("#otp", timeout=30000)
    print("[*] OTP input found")

    otp = get_otp_from_email(wait_first=30)
    if not otp:
        raise Exception("Signup OTP not received")

    # Changed from fill to slow type
    page.locator("#otp").click(delay=random.randint(150, 400))
    page.type("#otp", otp, delay=random.uniform(200, 450))
    page.click('[data-testid="verify-email-submit-button"]', delay=random.randint(150, 400))
    pause(2, 4)

    page.wait_for_selector("#password", timeout=30000)
    page.locator("#password").click(delay=random.randint(150, 400))
    page.type("#password", CONFIG["PASSWORD"], delay=random.uniform(200, 450))
    
    # Blur fix so the second password box unlocks correctly
    page.locator("#password").blur()
    time.sleep(1)
    
    page.locator("#rePassword").click(delay=random.randint(150, 400))
    page.type("#rePassword", CONFIG["PASSWORD"], delay=random.uniform(200, 450))
    page.click('[data-testid="create-password-submit-button"]', delay=random.randint(150, 400))
    pause(3, 5)

    print("[✓] Signup done")


# STEP 2: PLAN SELECTION
# STEP 2: PLAN SELECTION
def handle_plan_selection(page):
    print("\n===== STEP 2: PLAN SELECTION =====")
    try:
        page.wait_for_selector('text=Choose your account plan', timeout=15000)
        print("[✓] Plan page detected — selecting FREE plan")

        # 1. Use the exact data-analytics attribute from your screenshot
        # 2. Fallback to the text selector just in case
        free_btn = page.locator(
            '[data-analytics="Free_Tier_V2_Account_Plan_Selection_Trial_Button_Text"], '
            'button:has-text("Choose free plan")'
        ).first
        
        # Ensure it's fully visible on screen before clicking
        free_btn.wait_for(state="visible", timeout=10000)
        free_btn.scroll_into_view_if_needed()
        
        # Execute the slow click
        free_btn.click(delay=random.randint(150, 400))
        pause(3, 5)
        print("[✓] Free plan selected")
        
    except Exception as e:
        print(f"[INFO] No plan selection page or error (skipping): {e}")


# STEP 3: CONTACT INFO
def fill_contact(page, profile):
    print("\n===== STEP 3: CONTACT INFO =====")
    pause(3, 5)

    # Phone country code
    try:
        print("[*] Selecting phone country code...")
        phone_btn = page.locator('#address\\.phoneCode').first
        phone_btn.click(delay=random.randint(150, 400))
        pause(2, 3)
        country_value = "IN" if profile["COUNTRY"] == "India" else "US"
        page.locator(f'[data-value="{country_value}"]').last.wait_for(timeout=5000)
        page.locator(f'[data-value="{country_value}"]').last.click(delay=random.randint(150, 400))
        print(f"[✓] Phone code: {country_value}")
        pause(1, 2)
    except Exception as e:
        print(f"⚠️ Phone code: {e}")

    # Country
    try:
        print("[*] Selecting country...")
        country_btn = page.locator('button#address\\.country').first
        country_btn.click(delay=random.randint(150, 400))
        pause(1, 2)
        country_value = "IN" if profile["COUNTRY"] == "India" else "US"
        page.locator(f'[data-value="{country_value}"]').last.click(delay=random.randint(150, 400))
        print(f"[✓] Country: {profile['COUNTRY']}")
        pause(1, 2)
    except Exception as e:
        print(f"⚠️ Country: {e}")

    # Text fields
    fields = {
        "Full Name":         profile["FULL_NAME"],
        "Organization name": profile["COMPANY_NAME"],
        "Phone Number":      profile["phoneNo"],
        "Address line 1":    profile["ADDRESS_LINE1"],
        "City":              profile["CITY"],
        "Postal Code":       profile["POSTAL_CODE"],
    }

    for label, value in fields.items():
        try:
            loc = page.get_by_label(label)
            loc.click(delay=random.randint(150, 400))
            pause(0.5, 1)
            loc.fill("")
            for ch in value:
                loc.type(ch, delay=random.uniform(200, 450))
                if random.random() < 0.10:
                    time.sleep(random.uniform(0.5, 1.5))
            pause(0.5, 1)
        except Exception as e:
            print(f"⚠️ Field '{label}': {e}")

    # State
    try:
        print("[*] Filling state...")
        state_input = page.get_by_label("State, Province, or Region")
        state_input.click(delay=random.randint(150, 400))
        pause(1, 2)
        state_input.fill("")
        for ch in profile["STATE"]:
            state_input.type(ch, delay=random.uniform(200, 450))
            if random.random() < 0.10:
                    time.sleep(random.uniform(0.5, 1.5))
        pause(2, 3)
        page.keyboard.press("ArrowDown")
        pause(0.5, 1)
        page.keyboard.press("Enter")
        print(f"[✓] State: {profile['STATE']}")
        pause(1, 2)
    except Exception as e:
        print(f"⚠️ State: {e}")

    # Agreement checkbox
    try:
        page.locator('[aria-label="AWS Customer Agreement checkbox"]').click(delay=random.randint(150, 400))
        pause(1, 2)
        print("[✓] Agreement checked")
    except Exception as e:
        print(f"⚠️ Checkbox: {e}")

    # Submit
    try:
        pause(2, 3)
        page.click('[data-testid="contact-information-submit-button"]', delay=random.randint(150, 400))
        pause(5, 8)
        print("[✓] Contact submitted")
    except Exception as e:
        print(f"⚠️ Contact submit: {e}")


# STEP 4: BILLING
def billing(page, profile, account_type):
    print("\n===== STEP 4: BILLING =====")

    try:
        page.wait_for_selector('text=Payment method type', timeout=30000)
        print("[✓] Billing page loaded")
    except Exception:
        print("[*] Navigating to billing manually...")
        page.goto("https://portal.aws.amazon.com/billing/signup#/paymentmethod")
        page.wait_for_load_state("domcontentloaded")
        pause(5, 7)
        page.wait_for_selector('text=Payment method type', timeout=20000)

    dismiss_cookie_banner(page)
    page.get_by_text("Credit or debit card").click(delay=random.randint(150, 400))
    pause(2, 3)

    # Find card iframe
    print("[*] Looking for card iframe...")
    card_frame = None
    page.wait_for_timeout(3000)

    for frame in page.frames:
        print(f"[DEBUG] Frame: {frame.url}")
        if any(k in frame.url for k in ["payments", "billing", "iframe", "pay"]):
            card_frame = frame
            print("[✓] Card iframe found")
            break

    if card_frame is None:
        for f in page.frames:
            try:
                f.wait_for_selector('input[name="cardNumber"]', timeout=3000)
                card_frame = f
                print("[✓] Card iframe found by input")
                break
            except Exception:
                continue

    if card_frame:
        try:
            card_frame.wait_for_selector('input[name="cardNumber"]', timeout=10000)
            # Changed fill to slow type
            card_frame.type('input[name="cardNumber"]', CONFIG["CardNo"], delay=random.uniform(200, 450))
            pause(1, 2)
            card_frame.type('input[name="sor.cvv"]', CONFIG["cvvNo"], delay=random.uniform(200, 450))
            pause(1, 2)
            card_frame.type('input[name="accountHolderName"]', CONFIG["nameOnCard"], delay=random.uniform(200, 450))
            pause(1, 2)
            print("[✓] Card fields filled")
        except Exception as e:
            print(f"⚠️ Card fill: {e}")
    else:
        try:
            page.type('input[name="cardNumber"]', CONFIG["CardNo"], delay=random.uniform(200, 450))
            page.type('input[name="sor.cvv"]', CONFIG["cvvNo"], delay=random.uniform(200, 450))
            page.type('input[name="accountHolderName"]', CONFIG["nameOnCard"], delay=random.uniform(200, 450))
            print("[✓] Direct card fill done")
        except Exception as e:
            print(f"⚠️ Direct fill: {e}")

    pause(1, 2)

    try:
        select_dropdown(page, 'button#expirationMonth', CONFIG["cardExpiryMonth"], is_month=True)
        pause(1, 2)
    except Exception as e:
        print(f"⚠️ Month: {e}")

    try:
        select_dropdown(page, 'button#expirationYear', CONFIG["cardExpiryYear"], is_month=False)
        pause(1, 2)
    except Exception as e:
        print(f"⚠️ Year: {e}")

    pause(1, 2)

    # Billing address
    try:
        use_contact = page.locator(
            'label:has-text("Use my contact address"), input[value="existing"]'
        ).first
        if use_contact.count() > 0:
            use_contact.click(delay=random.randint(150, 400))
            print("[✓] Using contact address")
        pause(1, 2)
    except Exception:
        pass

    # PAN
    try:
        page.wait_for_selector('text=Do you have a PAN', timeout=10000)
        pan_no = profile.get("panNo", "")
        if account_type in ("TTN", "CK") and pan_no:
            page.locator('input[name="sor.panStatus"][value="Yes"]').first.click(delay=random.randint(150, 400))
            pause(1, 2)
            page.locator('input[name="sor.pan"], input[placeholder*="PAN" i]').first.type(pan_no, delay=random.uniform(200, 450))
            print(f"[✓] PAN filled: {pan_no}")
        else:
            page.locator('input[name="sor.panStatus"][value="No"]').first.click(delay=random.randint(150, 400))
            print("[✓] PAN = No")
        pause(1, 2)
    except Exception as e:
        print(f"[INFO] PAN: {e}")

    dismiss_cookie_banner(page)

    # Click Continue
    try:
        continue_btn = page.locator(
            'button:has-text("Continue"):not([data-id="awsccc-cb-btn-accept"]), '
            'button:has-text("Verify and Add"), '
            'button:has-text("Next")'
        ).first
        continue_btn.wait_for(timeout=10000)
        continue_btn.click(delay=random.randint(150, 400))
        print("[✓] Billing Continue clicked")
        pause(5, 8)
    except Exception as e:
        raise Exception(f"Billing Continue failed: {e}")


# STEP 5: IDENTITY VERIFICATION (Phone OTP)
def handle_identity_verification(page, profile):
    print("\n===== STEP 5: IDENTITY VERIFICATION =====")

    # Wait for identity verification page
    matched = wait_for_any(page, [
        'text=Identity verification',
        'text=Verify your identity',
        'text=We need to verify',
        'text=Enter the PIN',
        'text=verification code',
        'text=Support plan',         # skipped identity
        'text=Congratulations',      # account already done
        'text=Welcome to AWS',
    ], timeout=30000)

    if matched is None:
        print("[WARN] No identity verification page detected — continuing")
        return

    if any(x in matched for x in ['Support plan', 'Congratulations', 'Welcome to AWS']):
        print("[INFO] Skipped identity verification — already past it")
        return

    print(f"[✓] Identity verification page detected: {matched}")

    # Select phone verification method if asked
    try:
        phone_option = page.locator(
            'input[value="voice"], input[value="sms"], '
            'label:has-text("Text message"), label:has-text("Voice call")'
        ).first
        if phone_option.is_visible():
            phone_option.click(delay=random.randint(150, 400))
            print("[✓] Selected phone verification method")
            pause(1, 2)
    except Exception:
        pass

    # Fill phone number if asked
    try:
        phone_input = page.locator(
            'input[name="phoneNumber"], input[id*="phone"], '
            'input[placeholder*="phone" i], input[type="tel"]'
        ).first
        if phone_input.is_visible():
            phone_input.fill("")
            phone_input.type(profile["phoneNo"], delay=random.uniform(200, 450))
            print(f"[✓] Phone filled: {profile['phoneNo']}")
            pause(1, 2)
    except Exception:
        pass

    # Click Send SMS / Call Me / Continue
    try:
        send_btn = page.locator(
            'button:has-text("Send SMS"), button:has-text("Call me"), '
            'button:has-text("Send code"), button:has-text("Continue"), '
            'button:has-text("Contact me")'
        ).first
        send_btn.wait_for(timeout=10000)
        send_btn.click(delay=random.randint(150, 400))
        print("[✓] Verification request sent")
        pause(5, 8)
    except Exception as e:
        print(f"⚠️ Send verification: {e}")

    # Wait for PIN/OTP input to appear
    try:
        pin_input = page.locator(
            'input[name="pin"], input[id*="pin"], input[id*="otp"], '
            'input[placeholder*="PIN" i], input[placeholder*="code" i], '
            'input[maxlength="4"], input[maxlength="6"]'
        ).first
        pin_input.wait_for(timeout=30000)
        print("[*] PIN input found — waiting for SMS/call OTP...")

        # Get OTP from email (AWS sometimes sends it to email too)
        # Wait and try email first, then pause for manual if needed
        otp = get_otp_from_email(wait_first=15)

        if otp:
            pin_input.type(otp, delay=random.uniform(200, 450))
            print(f"[✓] PIN filled: {otp}")
        else:
            print("⚠️ OTP not found in email — waiting 60s for manual SMS entry...")
            time.sleep(60)  # Give time for SMS to arrive and user to see

        pause(1, 2)

        # Click Continue / Verify
        verify_btn = page.locator(
            'button:has-text("Continue"), button:has-text("Verify"), '
            'button:has-text("Submit"), button[type="submit"]'
        ).first
        verify_btn.wait_for(timeout=10000)
        verify_btn.click(delay=random.randint(150, 400))
        print("[✓] PIN submitted")
        pause(5, 8)

    except Exception as e:
        print(f"⚠️ PIN step: {e}")


# STEP 6: 3D SECURE / CARD OTP (Bank verification)
def handle_3ds_verification(page):
    print("\n===== STEP 6: 3DS CARD VERIFICATION =====")

    # Check if 3DS page appeared (usually an iframe from bank)
    matched = wait_for_any(page, [
        'text=Enter OTP',
        'text=One Time Password',
        'text=Secure Authentication',
        'text=Verified by Visa',
        'text=Mastercard SecureCode',
        'text=Authentication',
        'text=Support plan',       # 3DS skipped
        'text=Congratulations',    # done
        'text=Welcome to AWS',
    ], timeout=20000)

    if matched is None:
        print("[INFO] No 3DS page — continuing")
        return

    if any(x in matched for x in ['Support plan', 'Congratulations', 'Welcome to AWS']):
        print("[INFO] No 3DS needed — already past it")
        return

    print(f"[✓] 3DS page detected: {matched}")

    # 3DS is inside a bank iframe — try to find OTP input
    otp_input = None

    # Check all frames for OTP input
    for frame in page.frames:
        try:
            inp = frame.locator(
                'input[name*="otp" i], input[name*="password" i], '
                'input[placeholder*="OTP" i], input[placeholder*="password" i], '
                'input[type="password"], input[maxlength="6"]'
            ).first
            if inp.is_visible():
                otp_input = inp
                print(f"[✓] 3DS OTP input found in frame: {frame.url}")
                break
        except Exception:
            continue

    if otp_input:
        otp = get_otp_from_email(wait_first=15)
        if otp:
            otp_input.type(otp, delay=random.uniform(200, 450))
            print(f"[✓] 3DS OTP filled: {otp}")
            pause(1, 2)

            # Submit
            for frame in page.frames:
                try:
                    submit = frame.locator(
                        'button:has-text("Submit"), button:has-text("Verify"), '
                        'button[type="submit"], input[type="submit"]'
                    ).first
                    if submit.is_visible():
                        submit.click(delay=random.randint(150, 400))
                        print("[✓] 3DS submitted")
                        pause(5, 8)
                        break
                except Exception:
                    continue
        else:
            print("⚠️ 3DS OTP not found in email — bank SMS may be needed")
            print("[*] Waiting 90s for bank OTP...")
            time.sleep(90)
    else:
        print("[INFO] No 3DS OTP input found — may have auto-passed")

    pause(3, 5)


# STEP 7: SUPPORT PLAN SELECTION
def handle_support_plan(page):
    print("\n===== STEP 7: SUPPORT PLAN =====")

    try:
        page.wait_for_selector('text=Support plan', timeout=20000)
        print("[✓] Support plan page detected — selecting Basic (Free)")

        # Try clicking Basic/Free plan
        basic_btn = page.locator(
            'button:has-text("Basic support"), '
            'button:has-text("Free"), '
            'button:has-text("Basic"), '
            '[data-testid*="basic"], '
            'label:has-text("Basic")'
        ).first

        basic_btn.wait_for(timeout=10000)
        basic_btn.click(delay=random.randint(150, 400))
        print("[✓] Basic (Free) support selected")
        pause(2, 3)

        # Click Continue / Complete
        try:
            cont = page.locator(
                'button:has-text("Complete sign up"), '
                'button:has-text("Continue"), '
                'button:has-text("Get started"), '
                'button[type="submit"]'
            ).first
            cont.wait_for(timeout=10000)
            cont.click(delay=random.randint(150, 400))
            print("[✓] Support plan confirmed")
            pause(5, 8)
        except Exception as e:
            print(f"⚠️ Support plan continue: {e}")

    except Exception:
        print("[INFO] No support plan page detected (skipping)")


# STEP 8: WAIT FOR ACCOUNT CREATION SUCCESS
def wait_for_success(page):
    print("\n===== STEP 8: WAITING FOR ACCOUNT CREATION =====")

    matched = wait_for_any(page, [
        'text=Congratulations',
        'text=Welcome to AWS',
        'text=Your AWS account is ready',
        'text=account is being activated',
        'text=You have successfully',
        'text=Go to the AWS Management Console',
        'text=Console',
    ], timeout=60000)

    if matched:
        print(f"[✓] Account creation confirmed: {matched}")
        return True
    else:
        print("[WARN] Could not confirm account creation — check browser manually")
        return False


# SINGLE ACCOUNT FLOW
def create_one_account(browser, account_type, index):
    profile = PROFILES[account_type]
    alias_email = generate_alias_email(CONFIG["EMAIL"])
    password = CONFIG["PASSWORD"]

    print(f"\n{'='*55}")
    print(f"  ACCOUNT {index} | TYPE: {account_type} | EMAIL: {alias_email}")
    print(f"{'='*55}")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]

    context = browser.new_context(
        viewport={"width": random.randint(1200, 1400), "height": random.randint(700, 900)},
        user_agent=random.choice(user_agents),
        locale=random.choice(["en-US", "en-GB"]),
        timezone_id="Asia/Kolkata" if account_type != "TTN_US" else "America/New_York",
    )

    page = context.new_page()

    try:
        Stealth().apply_stealth_sync(page)
    except Exception:
        pass

    status = "FAILED"

    try:
        # FULL FLOW — no breaks
        signup(page, alias_email, account_type)          # Step 1
        handle_plan_selection(page)                       # Step 2
        fill_contact(page, profile)                       # Step 3
        billing(page, profile, account_type)              # Step 4
        handle_identity_verification(page, profile)       # Step 5
        handle_3ds_verification(page)                     # Step 6
        handle_support_plan(page)                         # Step 7
        success = wait_for_success(page)                  # Step 8

        status = "SUCCESS" if success else "PARTIAL"
        print(f"\n✅ Account {index} — {status}")

    except Exception as e:
        status = f"FAILED: {str(e)[:80]}"
        print(f"\n❌ Account {index} failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        log_result(alias_email, password, account_type, status)
        try:
            context.close()
        except Exception:
            pass

    return status


# MAIN
def run():
    lock_file = os.path.join("user_data", "SingletonLock")
    if os.path.exists(lock_file):
        os.remove(lock_file)
        print("[✓] Removed stale SingletonLock")

    # ── CI / Jenkins non-interactive mode ──────────────────────────────────
    ci_count    = os.getenv("AWS_ACCOUNT_COUNT")
    ci_type_key = os.getenv("AWS_ACCOUNT_TYPE_KEY")  # "1" = TTN, "2" = TTN_US, "3" = CK

    if ci_count and ci_type_key:
        # Validate count
        try:
            count = int(ci_count)
            if not (1 <= count <= MAX_ACCOUNTS):
                raise ValueError(f"AWS_ACCOUNT_COUNT must be 1-{MAX_ACCOUNTS}, got {count}")
        except ValueError as e:
            print(f"❌ Invalid AWS_ACCOUNT_COUNT: {e}")
            raise SystemExit(1)

        # Validate type key
        if ci_type_key not in ACCOUNT_TYPES:
            print(f"❌ Invalid AWS_ACCOUNT_TYPE_KEY '{ci_type_key}' — must be 1, 2, or 3")
            raise SystemExit(1)

        account_type = ACCOUNT_TYPES[ci_type_key]
        print(f"\n[CI Mode] Creating {count} account(s) — Type: {account_type}")
        print(f"[CI Mode] AWS_ACCOUNT_COUNT={count} | AWS_ACCOUNT_TYPE_KEY={ci_type_key}\n")

    else:
        # ── Interactive mode (local / manual run) ──────────────────────────
        count, account_type = prompt_inputs()
    # ───────────────────────────────────────────────────────────────────────

    init_csv()

    results = {"SUCCESS": 0, "PARTIAL": 0, "FAILED": 0}

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--no-sandbox"],
        )

        for i in range(1, count + 1):
            print(f"\n[*] Starting account {i}/{count}...")
            status = create_one_account(browser, account_type, i)

            if "SUCCESS" in status:
                results["SUCCESS"] += 1
            elif "PARTIAL" in status:
                results["PARTIAL"] += 1
            else:
                results["FAILED"] += 1

            if i < count:
                wait_time = random.randint(15, 30)
                print(f"[*] Waiting {wait_time}s before next account...")
                time.sleep(wait_time)

        browser.close()

    print(f"\n{'='*50}")
    print(f"  DONE — {results['SUCCESS']} success, {results['PARTIAL']} partial, {results['FAILED']} failed")
    print(f"  Results saved to: {OUTPUT_FILE}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run()
