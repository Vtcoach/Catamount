import json
import os

from playwright.sync_api import sync_playwright


TRACTOR_SELECTOR = "#divFinancialInformation_Financialinformation1_tractor1_ComboBoxTextBox"
TRAILER_SELECTOR = "#container"


config_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "config",
    "equipment.json"
)

with open(config_path, "r") as f:
    equipment = json.load(f)

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

    tractor = page.locator(
        TRACTOR_SELECTOR
    ).input_value().strip()

    print("Tractor:")
    print(tractor)

    if tractor in equipment:
        trailer = equipment[tractor]["trailer"]

        print("\nTrailer:")
        print(trailer)

        print("\nWriting trailer to portal...")
        page.locator(TRAILER_SELECTOR).fill(trailer)

        print("Done.")
    else:
        print("\nNo equipment record found.")

    input("\nPress ENTER to close...")

    browser.close()