import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from config import CONFIG
from email_utils import get_email_otp_simple


def pause(a=1, b=3):
    time.sleep(random.uniform(a, b))


# MONTH MAP
MONTH_MAP = {
    "01": "January",  "02": "February", "03": "March",
    "04": "April",    "05": "May",      "06": "June",
    "07": "July",     "08": "August",   "09": "September",
    "10": "October",  "11": "November", "12": "December"
}


# DROPDOWN HELPER 
def select_dropdown(page, btn_selector, value, is_month=False):
    """
    Clicks dropdown button then selects option by text.
    For month: converts '04' -> 'April' etc.
    For year: handles multiline text like '2028\n2028'.
    """
    display_value = MONTH_MAP.get(value, value) if is_month else value

    btn = page.locator(btn_selector)
    btn.wait_for(timeout=10000)
    btn.click()
    pause(1, 2)

    all_opts = page.locator('[role="option"], [role="listbox"] li').all()
    print(f"[DEBUG] Dropdown has {len(all_opts)} options, looking for '{display_value}'")

    for opt in all_opts:
        try:
            # Take only first line to handle '2028\n2028' style text
            txt = opt.inner_text().strip().split("\n")[0].strip()
            if txt == display_value:
                opt.click()
                print(f"[✓] Selected '{display_value}'")
                return True
        except Exception:
            continue

    print(f"⚠️ Could not select '{display_value}' from dropdown")
    return False


# LOGIN
def login(page):
    print("[*] Opening AWS Console")

    page.goto("https://console.aws.amazon.com/")
    page.wait_for_load_state("domcontentloaded")

    print("[*] Checking for Root User option")
    try:
        root_btn = page.get_by_role("button", name="Sign in using root user email")
        root_btn.wait_for(timeout=5000)
        print("[*] Switching to Root User Login")
        root_btn.click()
    except Exception:
        print("[INFO] Root user button not shown")

    page.wait_for_selector("#resolving_input", timeout=30000)
    page.fill("#resolving_input", CONFIG["EMAIL"])
    page.keyboard.press("Enter")
    pause(2, 4)

    page.wait_for_selector("#password", timeout=30000)
    page.fill("#password", CONFIG["PASSWORD"])
    page.keyboard.press("Enter")
    pause(5, 8)

    print("[*] Checking for OTP step")
    try:
        otp_input = page.locator(
            "#otp, input[name='otpCode'], input[name='mfaCode'], "
            "input[type='text'][autocomplete='one-time-code'], "
            "input[placeholder*='code' i], input[placeholder*='OTP' i]"
        ).first
        otp_input.wait_for(timeout=10000)
        print("[*] OTP input found")
        print("[*] Waiting 20s for AWS email...")
        time.sleep(20)

        otp = None
        for i in range(12):
            print(f"[INFO] OTP fetch attempt {i+1}/12")
            otp = get_email_otp_simple(CONFIG["EMAIL"], CONFIG["APP_PASSWORD"])
            if otp:
                print(f"[✓] OTP: {otp}")
                break
            time.sleep(5)

        if not otp:
            print("❌ OTP not found after all attempts")
            return False

        otp_input.fill(otp)
        page.keyboard.press("Enter")
        pause(5, 8)

    except Exception as e:
        print(f"[INFO] No OTP required or error: {e}")

    print("✅ Logged in successfully")
    return True


# OPEN BILLING
def open_billing(page):
    print("[*] Opening billing page")

    page.goto("https://portal.aws.amazon.com/billing/signup/incomplete")
    page.wait_for_load_state("domcontentloaded")
    pause(3, 5)

    try:
        btn = page.locator('a[data-testid="complete-registration-button"]')
        btn.wait_for(timeout=10000)
        btn.click()
        print("[✓] Clicked Complete Registration button")
    except Exception:
        try:
            page.get_by_text("Complete your AWS registration").click()
            print("[✓] Clicked via text fallback")
        except Exception as e:
            print(f"⚠️ Could not click registration button: {e}")

    pause(5, 7)


# DISMISS COOKIE BANNER 
def dismiss_cookie_banner(page):
    try:
        cookie_btn = page.locator(
            'button[data-id="awsccc-cb-btn-accept"], '
            '.awsccc-u-btn-primary'
        ).first
        cookie_btn.wait_for(timeout=5000)
        cookie_btn.click()
        print("[✓] Cookie banner dismissed")
        pause(1, 2)
    except Exception:
        print("[INFO] No cookie banner found")


# BILLING 
def billing(page):
    print("[*] Billing step started")

    # Dismiss cookie banner before anything else
    dismiss_cookie_banner(page)

    page.wait_for_selector('text=Payment method type', timeout=20000)
    page.get_by_text("Credit or debit card").click()
    pause(2, 3)

    # ---- Find card iframe ----
    print("[*] Looking for card iframe...")
    card_frame = None
    page.wait_for_timeout(3000)

    for frame in page.frames:
        print(f"[DEBUG] Frame URL: {frame.url}")
        if any(k in frame.url for k in ["payments", "billing", "iframe", "pay"]):
            card_frame = frame
            print(f"[✓] Found card iframe by URL: {frame.url}")
            break

    if card_frame is None:
        for f in page.frames:
            try:
                f.wait_for_selector('input[name="cardNumber"]', timeout=3000)
                card_frame = f
                print(f"[✓] Found card frame by input: {f.url}")
                break
            except Exception:
                continue

    # ---- Fill card fields ----
    if card_frame:
        try:
            card_frame.wait_for_selector('input[name="cardNumber"]', timeout=10000)
            card_frame.fill('input[name="cardNumber"]', CONFIG["CardNo"])
            pause(1, 2)
            card_frame.fill('input[name="sor.cvv"]', CONFIG["cvvNo"])
            pause(1, 2)
            card_frame.fill('input[name="accountHolderName"]', CONFIG["nameOnCard"])
            pause(1, 2)
            print("[✓] Card fields filled")
        except Exception as e:
            print(f"⚠️ Card fill error: {e}")
    else:
        print("⚠️ No iframe, trying direct fill...")
        try:
            page.fill('input[name="cardNumber"]', CONFIG["CardNo"])
            page.fill('input[name="sor.cvv"]', CONFIG["cvvNo"])
            page.fill('input[name="accountHolderName"]', CONFIG["nameOnCard"])
            print("[✓] Direct fill done")
        except Exception as e:
            print(f"⚠️ Direct fill failed: {e}")

    pause(1, 2)

    # ---- Expiry Month ----
    print("[*] Setting expiry month...")
    try:
        select_dropdown(page, 'button#expirationMonth', CONFIG["cardExpiryMonth"], is_month=True)
        pause(1, 2)
    except Exception as e:
        print(f"⚠️ Month error: {e}")

    # ---- Expiry Year ----
    print("[*] Setting expiry year...")
    try:
        select_dropdown(page, 'button#expirationYear', CONFIG["cardExpiryYear"], is_month=False)
        pause(1, 2)
    except Exception as e:
        print(f"⚠️ Year error: {e}")

    pause(1, 2)

    # ---- Billing Address ----
    print("[*] Setting billing address...")
    try:
        use_contact = page.locator(
            'label:has-text("Use my contact address"), '
            'input[value="existing"]'
        ).first
        if use_contact.count() > 0:
            use_contact.click()
            print("[✓] Using contact address")
        pause(1, 2)
    except Exception as e:
        print(f"[INFO] Address selection skipped: {e}")

    # ---- PAN (India KYC) ----
    print("[*] Handling PAN question...")
    try:
        page.wait_for_selector('text=Do you have a PAN', timeout=10000)

        no_radio = page.locator(
            'input[name="sor.panStatus"][value="No"]'
        ).first
        no_radio.wait_for(timeout=5000)
        no_radio.click()
        print("[✓] PAN = No (personal account)")
        pause(1, 2)

    except Exception as e:
        print(f"[INFO] PAN section: {e}")

    # ---- Dismiss cookie banner again before clicking Continue ----
    dismiss_cookie_banner(page)

    # ---- Continue Button ----
    print("[*] Clicking Continue...")
    try:
        # Exclude the cookie accept button explicitly
        continue_btn = page.locator(
            'button:has-text("Continue"):not([data-id="awsccc-cb-btn-accept"]), '
            'button:has-text("Verify and Add"), '
            'button:has-text("Next")'
        ).first
        continue_btn.wait_for(timeout=10000)
        continue_btn.click()
        print("[✓] Continue clicked")
        pause(5, 8)
    except Exception as e:
        print(f"⚠️ Continue button error: {e}")


# RUN 
def run():
    with Stealth().use_sync(sync_playwright()) as p:
        context = p.chromium.launch_persistent_context(
            "user_data",
            headless=False,
            args=["--start-maximized"],
        )

        page = context.new_page()
        billing(page)

        input("✅ Done. Press Enter to close...")
        context.close()


if __name__ == "__main__":
    run()