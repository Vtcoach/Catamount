from playwright.sync_api import sync_playwright

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
    print()

    inputs = page.locator("input")

    print("Total inputs found:", inputs.count())
    print()

    for i in range(inputs.count()):
        element = inputs.nth(i)

        try:
            print("------------------------------------")
            print("ID:   ", element.get_attribute("id"))
            print("NAME: ", element.get_attribute("name"))
            print("TYPE: ", element.get_attribute("type"))
            print("VALUE:", element.input_value())
        except Exception:
            pass

    input("\nPress ENTER to close...")