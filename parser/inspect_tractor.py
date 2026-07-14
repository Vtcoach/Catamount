from playwright.sync_api import sync_playwright


TRACTOR_SELECTOR = "#divFinancialInformation_Financialinformation1_tractor1_ComboBoxTextBox"


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

    tractor_field = page.locator(TRACTOR_SELECTOR)

    tractor_value = tractor_field.input_value()

    print("Tractor 1 value:")
    print(tractor_value)

    input("\nPress ENTER to close...")

    browser.close()