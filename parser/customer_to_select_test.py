from playwright.sync_api import sync_playwright

from customer_lookup import (
    open_lookup,
    search_lookup_city,
    read_lookup_results,
    find_matching_location,
    select_lookup_location,
)

TEST_CITY = "New Castle"
TEST_ADDRESS = "1000 Centerpoint Blvd"


def find_billing_page(context):
    for page in context.pages:
        if "agents.evansdelivery.com/billing" in page.url:
            return page
    return None


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]

    page = find_billing_page(context)

    if page is None:
        print("Billing page not found.")
        input("Press ENTER to exit...")
        browser.close()
        raise SystemExit

    print("Opening To lookup...")
    open_lookup(page, "to")

    print(f"Searching city: {TEST_CITY}")
    search_lookup_city(page, TEST_CITY)

    locations = read_lookup_results(page)
    print(f"Found {len(locations)} locations")

    match = find_matching_location(TEST_ADDRESS, locations)

    if not match:
        print("No match found.")
        input("Press ENTER to exit...")
        browser.close()
        raise SystemExit

    print()
    print("MATCH FOUND")
    print("=" * 60)
    print(f"Account : {match.account}")
    print(f"Name    : {match.name}")
    print(f"Address : {match.address}")
    print(f"City    : {match.city}")
    print(f"State   : {match.state}")
    print(f"Zip     : {match.zip}")

    print()
    print("Selecting matched customer...")
    select_lookup_location(page, match)

    print()
    print("Done. Check the To box on the Evans billing screen.")

    input("\nPress ENTER to exit...")
    browser.close()