from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]

    page = None

    for candidate in context.pages:
        if "billing" in candidate.url.lower() or "agents.evansdelivery.com" in candidate.url.lower():
            page = candidate
            break

    if page is None:
        print("Could not find Evans page.")
        print("\nOpen pages:")
        for candidate in context.pages:
            print(candidate.url)
        input("\nPress ENTER to close...")
        browser.close()
        exit()

    print("URL:", page.url)
    print("TITLE:", page.title())

    print("\nLINKS")
    print("=" * 50)

    links = page.locator("a")

    for i in range(links.count()):
        text = links.nth(i).inner_text().strip()
        href = links.nth(i).get_attribute("href")
        onclick = links.nth(i).get_attribute("onclick")

        if text or href or onclick:
            print("-" * 50)
            print("TEXT:", text)
            print("HREF:", href)
            print("ONCLICK:", onclick)

    input("\nPress ENTER to close...")
    browser.close()