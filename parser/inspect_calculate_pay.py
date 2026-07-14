from playwright.sync_api import sync_playwright


CALCULATE_PAY_SELECTOR = (
    "#divFinancialInformation_Financialinformation1_addcalculatepaypercentagebutton > img"
)


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

    print("\nClicking Calculate Pay Percentage...")
    page.locator(CALCULATE_PAY_SELECTOR).click()

    page.wait_for_timeout(2000)

    print("\nDone. Check the Independent Contractor Pay fields.")

    input("\nPress ENTER to close...")

    browser.close()