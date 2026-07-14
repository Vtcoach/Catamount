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
        raise Exception("Could not find Evans Billing page.")

    print("Connected to:", page.url)
    print()

    inputs = page.locator("input")

    print("VISIBLE TEXT INPUTS")
    print("=" * 40)

    for i in range(inputs.count()):
        element = inputs.nth(i)

        try:
            input_type = element.get_attribute("type")
            visible = element.is_visible()
            readonly = element.get_attribute("readonly")
            value = element.input_value()

            if input_type == "text" and visible:
                box = element.bounding_box()

                print("------------------------------------")
                print("Index:   ", i)
                print("ID:      ", element.get_attribute("id"))
                print("NAME:    ", element.get_attribute("name"))
                print("VALUE:   ", value)
                print("READONLY:", readonly)
                print("BOX:     ", box)
        except Exception:
            pass

    print()
    print("BUTTONS / SUBMIT INPUTS")
    print("=" * 40)

    for i in range(inputs.count()):
        element = inputs.nth(i)

        try:
            input_type = element.get_attribute("type")
            visible = element.is_visible()
            value = element.input_value()

            if input_type in ["button", "submit"] and visible:
                box = element.bounding_box()

                print("------------------------------------")
                print("Index: ", i)
                print("ID:    ", element.get_attribute("id"))
                print("NAME:  ", element.get_attribute("name"))
                print("VALUE: ", value)
                print("BOX:   ", box)
        except Exception:
            pass

    input("\nPress ENTER to close...")