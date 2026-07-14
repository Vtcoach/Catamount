from playwright.sync_api import sync_playwright
import time

TEST_CITY = "Baltimore"

def find_billing_page(context):
    for page in context.pages:
        if "agents.evansdelivery.com/billing" in page.url:
            return page
    return None

def print_visible_inputs(page):
    print("\nVISIBLE INPUTS")
    print("=" * 60)

    for el in page.locator("input").all():
        try:
            if not el.is_visible():
                continue

            print(
                f"TYPE={el.get_attribute('type')} | "
                f"ID={el.get_attribute('id')} | "
                f"NAME={el.get_attribute('name')} | "
                f"VALUE={el.get_attribute('value')}"
            )
        except:
            pass

def print_all_visible_tables(page):
    print("\nVISIBLE TABLES AFTER SEARCH")
    print("=" * 60)

    tables = page.locator("table")
    print("Total tables:", tables.count())

    for i in range(tables.count()):
        table = tables.nth(i)

        try:
            if not table.is_visible():
                continue

            text = table.inner_text().strip()

            if not text:
                continue

            print(f"\nTABLE {i}")
            print("-" * 60)
            print(text[:3000])
        except:
            pass

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]

    page = find_billing_page(context)

    if page is None:
        print("Billing page not found.")
        input("Press ENTER to exit...")
        browser.close()
        raise SystemExit

    print("Connected to Billing:")
    print(page.url)

    print("\nOpening FROM Enhanced Lookup...")
    page.evaluate("__doPostBack('from$accountSelection1','enhancedlookup')")
    page.wait_for_load_state("networkidle", timeout=15000)

    time.sleep(1)

    print("\nLookup opened. Visible inputs:")
    print_visible_inputs(page)

    print(f"\nTyping city: {TEST_CITY}")
    page.locator("#AccountLookupControl1_City").fill(TEST_CITY)

    print("Triggering Go search...")
    page.evaluate("__doPostBack('AccountLookupControl1$GoButton','')")

    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1)

    print("\nSearch complete.")
    print_visible_inputs(page)
    print_all_visible_tables(page)

    input("\nPress ENTER to disconnect...")
    browser.close()