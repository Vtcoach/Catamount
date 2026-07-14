from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]

    # Find the Evans billing page
    page = None
    for pg in context.pages:
        if "agents.evansdelivery.com" in pg.url:
            page = pg
            break

    if page is None:
        print("Evans billing page not found.")
        input("Press ENTER to exit...")
        browser.close()
        raise SystemExit

    print("Connected to:", page.url)

    print("\nOpening FROM Enhanced Lookup...")
    page.evaluate("__doPostBack('from$accountSelection1','enhancedlookup')")

    # Give Evans a moment to open the popup
    time.sleep(3)

    print("\nOPEN PAGES")
    print("=" * 60)

    for i, pg in enumerate(context.pages):
        print(f"\nPAGE {i}")
        print("-" * 60)
        print("Title:", pg.title())
        print("URL:", pg.url)

        print("\nINPUTS")
        print("-" * 30)
        for el in pg.locator("input").all():
            try:
                print(
                    f"TYPE={el.get_attribute('type')} | "
                    f"ID={el.get_attribute('id')} | "
                    f"NAME={el.get_attribute('name')}"
                )
            except:
                pass

        print("\nBUTTONS")
        print("-" * 30)
        for el in pg.locator("button, input[type=button], input[type=submit]").all():
            try:
                print(
                    f"TEXT={el.inner_text() if el.evaluate('e => e.tagName') == 'BUTTON' else el.get_attribute('value')}"
                )
                print(f"ID={el.get_attribute('id')}")
                print("-" * 20)
            except:
                pass

        print("\nTABLES")
        print("-" * 30)
        tables = pg.locator("table")
        print("Table count:", tables.count())

    input("\nPress ENTER to disconnect...")
    browser.close()