from playwright.sync_api import sync_playwright

LOAD_NUMBER = "37026612"
TOTAL_REVENUE = 900.00

def split_revenue(total_revenue):
    freight = round(total_revenue * 0.72, 2)
    fuel = round(total_revenue - freight, 2)
    return freight, fuel

freight_charge, fuel_charge = split_revenue(TOTAL_REVENUE)

with sync_playwright() as p:
    print("Connecting to Chrome...")

    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]
    page = context.pages[0]

    print("Connected.")
    print("Title:", page.title())
    print("URL:", page.url)

    print("\nCalculated billing split:")
    print("Total Revenue:", TOTAL_REVENUE)
    print("Freight Charge:", freight_charge)
    print("Fuel Charge:", fuel_charge)

    print("\nFilling Reference #1...")
    page.locator("#reference1").fill(LOAD_NUMBER)

    print("Filling Freight Charge Total...")
    page.locator("#divFinancialInformation_Financialinformation1_freightcharge_total").fill(f"{freight_charge:.2f}")

    print("Filling Fuel Surcharge Total...")
    page.locator("#divFinancialInformation_Financialinformation1_fuelsurcharge_total").fill(f"{fuel_charge:.2f}")

    print("Done. Check the billing screen.")

    input("\nPress ENTER to disconnect...")

    browser.close()