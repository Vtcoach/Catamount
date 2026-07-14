from playwright.sync_api import sync_playwright

KEYWORDS = [
    "from",
    "source",
    "shipper",
    "account",
    "retrieve",
    "origin",
]

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

    print("MATCHING ELEMENTS")
    print("=" * 50)

    elements = page.locator("*")
    count = elements.count()

    for i in range(count):
        el = elements.nth(i)

        try:
            tag = el.evaluate("e => e.tagName")
            text = ""
            try:
                text = el.inner_text().strip()
            except:
                pass

            element_id = el.get_attribute("id") or ""
            name = el.get_attribute("name") or ""
            href = el.get_attribute("href") or ""
            onclick = el.get_attribute("onclick") or ""
            onchange = el.get_attribute("onchange") or ""
            class_name = el.get_attribute("class") or ""
            value = el.get_attribute("value") or ""

            combined = " ".join([
                tag,
                text,
                element_id,
                name,
                href,
                onclick,
                onchange,
                class_name,
                value,
            ]).lower()

            if any(keyword in combined for keyword in KEYWORDS):
                print("--------------------------------")
                print("TAG:", tag)
                print("TEXT:", text[:200])
                print("ID:", element_id)
                print("NAME:", name)
                print("CLASS:", class_name)
                print("VALUE:", value)
                print("HREF:", href)
                print("ONCLICK:", onclick)
                print("ONCHANGE:", onchange)

        except:
            pass

    input("\nPress ENTER to close...")