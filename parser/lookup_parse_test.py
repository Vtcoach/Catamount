from playwright.sync_api import sync_playwright
import time
import re

TEST_CITY = "Baltimore"


def find_billing_page(context):
    for page in context.pages:
        if "agents.evansdelivery.com/billing" in page.url:
            return page
    return None


def parse_locations(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    locations = []
    i = 0

    while i < len(lines):
        if re.fullmatch(r"TDW\d{5}", lines[i]):

            account = lines[i]

            name = lines[i + 1] if i + 1 < len(lines) else ""

            address = lines[i + 2] if i + 2 < len(lines) else ""

            city = ""
            state = ""
            zipcode = ""

            if i + 3 < len(lines):
                m = re.match(r"(.+?),\s*([A-Z]{2})\s*(\d{5})?", lines[i + 3])

                if m:
                    city = m.group(1).strip()
                    state = m.group(2).strip()
                    zipcode = m.group(3) if m.group(3) else ""

            locations.append({
                "account": account,
                "name": name,
                "address": address,
                "city": city,
                "state": state,
                "zip": zipcode
            })

            i += 4

        else:
            i += 1

    return locations


with sync_playwright() as p:

    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")

    context = browser.contexts[0]

    page = find_billing_page(context)

    if page is None:
        print("Billing page not found.")
        input()
        raise SystemExit

    print("Opening lookup...")

    page.evaluate("__doPostBack('from$accountSelection1','enhancedlookup')")

    page.wait_for_load_state("networkidle")

    page.locator("#AccountLookupControl1_City").fill(TEST_CITY)

    page.evaluate("__doPostBack('AccountLookupControl1$GoButton','')")

    page.wait_for_load_state("networkidle")

    time.sleep(1)

    table_text = page.locator("table").nth(5).inner_text()

    locations = parse_locations(table_text)

    print()
    print("=" * 60)
    print(f"Found {len(locations)} locations")
    print("=" * 60)

    for n, loc in enumerate(locations, start=1):

        print(f"\nLocation {n}")

        print(f"Account : {loc['account']}")
        print(f"Name    : {loc['name']}")
        print(f"Address : {loc['address']}")
        print(f"City    : {loc['city']}")
        print(f"State   : {loc['state']}")
        print(f"Zip     : {loc['zip']}")

    input("\nPress ENTER to exit...")

    browser.close()