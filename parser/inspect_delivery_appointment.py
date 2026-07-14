from playwright.sync_api import sync_playwright


DELIVERY_DATE_SELECTOR = "#DeliveryDate"
DELIVERY_TIME_SELECTOR = "#DeliveryTime"

TEST_DELIVERY_DATE = "07072026"
TEST_DELIVERY_TIME = "0830"


with sync_playwright() as p:

    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]

    page = None

    for candidate in context.pages:
        if "billing" in candidate.url.lower():
            page = candidate
            break

    if page is None:
        raise Exception("Billing page not found.")

    print("Connected to:", page.url)

    print("\nFilling Delivery Appointment Date...")
    page.locator(DELIVERY_DATE_SELECTOR).fill(TEST_DELIVERY_DATE)

    print("Filling Delivery Appointment Time...")
    page.locator(DELIVERY_TIME_SELECTOR).fill(TEST_DELIVERY_TIME)

    print("\nDone. Check the Delivery Appointment fields.")

    input("\nPress ENTER to close...")

    browser.close()