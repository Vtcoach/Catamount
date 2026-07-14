from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]

    print("OPEN TABS")
    print("=" * 50)

    evans_page = None

    for i, page in enumerate(context.pages):
        print(f"[{i}] Title: {page.title()}")
        print(f"    URL: {page.url}")

        if "agents.evansdelivery.com" in page.url:
            evans_page = page

    if evans_page is None:
        print("\nNo Evans tab found.")
        input("\nPress ENTER to disconnect...")
        browser.close()
        raise SystemExit

    page = evans_page
    print("\nUsing Evans tab:")
    print(page.url)

    print("\nINPUT ELEMENTS")
    print("=" * 50)
    for el in page.locator("input").all():
        try:
            print("TYPE:", el.get_attribute("type"))
            print("ID:", el.get_attribute("id"))
            print("NAME:", el.get_attribute("name"))
            print("VALUE:", el.get_attribute("value"))
            print("-" * 30)
        except:
            pass

    print("\nLINK ELEMENTS")
    print("=" * 50)
    for el in page.locator("a").all():
        try:
            text = el.inner_text().strip()
            href = el.get_attribute("href")
            onclick = el.get_attribute("onclick")
            if text or href or onclick:
                print("TEXT:", text)
                print("ID:", el.get_attribute("id"))
                print("HREF:", href)
                print("ONCLICK:", onclick)
                print("-" * 30)
        except:
            pass

    input("\nPress ENTER to disconnect...")
    browser.close()