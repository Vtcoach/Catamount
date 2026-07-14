from playwright.sync_api import sync_playwright
import time

TEST_CITY = "Baltimore"

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

    print("Opening lookup...")
    page.evaluate("__doPostBack('from$accountSelection1','enhancedlookup')")
    page.wait_for_load_state("networkidle")

    page.locator("#AccountLookupControl1_City").fill(TEST_CITY)

    print("Searching city:", TEST_CITY)
    page.evaluate("__doPostBack('AccountLookupControl1$GoButton','')")
    page.wait_for_load_state("networkidle")

    time.sleep(1)

    print("\nInspecting result rows...")
    print("=" * 60)

    tables = page.locator("table")
    print("Total tables:", tables.count())

    for table_index in range(tables.count()):
        table = tables.nth(table_index)

        try:
            if not table.is_visible():
                continue

            rows = table.locator("tr")
            row_count = rows.count()

            if row_count == 0:
                continue

            print(f"\nTABLE {table_index} — rows: {row_count}")
            print("-" * 60)

            for row_index in range(min(row_count, 25)):
                row = rows.nth(row_index)
                cells = row.locator("td")
                cell_count = cells.count()

                text = row.inner_text().strip()

                if not text:
                    continue

                print(f"ROW {row_index} | cells={cell_count}")
                print(text)

                if cell_count > 0:
                    for cell_index in range(cell_count):
                        cell_text = cells.nth(cell_index).inner_text().strip()
                        print(f"  CELL {cell_index}: {cell_text}")

                print("-" * 30)

        except:
            pass

    input("\nPress ENTER to exit...")
    browser.close()