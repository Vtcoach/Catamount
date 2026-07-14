import json
import os

from playwright.sync_api import sync_playwright

from customer_lookup import (
    open_lookup,
    search_lookup_city,
    read_lookup_results,
    resolve_customer,
    select_lookup_location,
)


TRACTOR_SELECTOR = "#divFinancialInformation_Financialinformation1_tractor1_ComboBoxTextBox"
TRAILER_SELECTOR = "#container"

DELIVERY_DATE_SELECTOR = "#DeliveryDate"
DELIVERY_TIME_SELECTOR = "#DeliveryTime"

CALCULATE_PAY_SELECTOR = (
    "#divFinancialInformation_Financialinformation1_addcalculatepaypercentagebutton > img"
)


def split_revenue(total_revenue):
    freight = round(total_revenue * 0.72, 2)
    fuel = round(total_revenue - freight, 2)
    return freight, fuel


def load_equipment():
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "config",
        "equipment.json"
    )

    with open(config_path, "r") as f:
        return json.load(f)


def get_location_city(location_text):
    if not location_text:
        return ""

    if "," in location_text:
        return location_text.split(",")[0].strip()

    return location_text.strip()


def get_target_address(load, section):
    if section == "from":
        return load.get("pickup_address", "")

    if section == "to":
        return load.get("delivery_address", "")

    return ""


def get_target_name(load, section):
    if section == "from":
        return load.get("pickup_name", "")

    if section == "to":
        return load.get("delivery_name", "")

    return ""


def lookup_and_select_customer(page, load, section):
    if section == "from":
        label = "From"
        location_text = load.get("pickup", "")
    elif section == "to":
        label = "To"
        location_text = load.get("delivery", "")
    else:
        raise ValueError("section must be 'from' or 'to'")

    city = get_location_city(location_text)
    target_address = get_target_address(load, section)
    target_name = get_target_name(load, section)

    print(f"\nOpening {label} lookup...")
    open_lookup(page, section)

    print(f"Searching city: {city}")
    search_lookup_city(page, city)

    locations = read_lookup_results(page)
    print(f"Found {len(locations)} locations")

    match_result = resolve_customer(
        target_address,
        target_name,
        locations
    )

    match = match_result.location

    if match is None:
        print("\nSTOP")
        print(f"Could not find matching {label} customer.")
        print(f"Target address: {target_address}")
        print(f"Target name: {target_name}")
        print(f"City searched: {city}")
        print(f"Reason: {match_result.message}")
        print("\nAvailable locations:")

        for location in locations:
            print("-" * 50)
            print("Account :", location.account)
            print("Name    :", location.name)
            print("Address :", location.address)
            print("City    :", location.city)
            print("State   :", location.state)
            print("Zip     :", location.zip)

        return False

    print("\nMATCH METHOD")
    print("=" * 50)
    print("Method     :", match_result.method)
    print("Confidence :", match_result.confidence)
    print("Message    :", match_result.message)

    print("\nMATCH FOUND")
    print("=" * 50)
    print("Account :", match.account)
    print("Name    :", match.name)
    print("Address :", match.address)
    print("City    :", match.city)
    print("State   :", match.state)
    print("Zip     :", match.zip)

    print(f"\nSelecting matched {label} customer...")
    select_lookup_location(page, match)

    return True


def fill_billing_screen(load):

    bill_to_code = load["bill_to_code"]
    load_number = load["load_number"]
    total_revenue = load["billing"]["total_revenue"]

    delivery_date = load["delivery_appointment"]["date"]
    delivery_time = load["delivery_appointment"]["time"]

    freight_charge, fuel_charge = split_revenue(total_revenue)
    equipment = load_equipment()

    print("Connecting to Chrome...")

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

        print("Connected.")
        print("Title:", page.title())
        print("URL:", page.url)

        print("\nEntering Bill To Code...")
        page.locator("#billto_accountSelection1_actid").fill(bill_to_code)

        print("Clicking Bill To Retrieve...")
        page.evaluate("__doPostBack('billto$accountSelection1','retrieve')")
        page.wait_for_timeout(2000)

        from_success = lookup_and_select_customer(page, load, "from")

        if not from_success:
            input("\nPress ENTER to disconnect...")
            browser.close()
            return

        to_success = lookup_and_select_customer(page, load, "to")

        if not to_success:
            input("\nPress ENTER to disconnect...")
            browser.close()
            return

        print("\nFilling Reference #1...")
        page.locator("#reference1").fill(load_number)
        page.wait_for_timeout(500)

        print("\nCalculated billing split:")
        print("Total Revenue:", total_revenue)
        print("Freight Charge:", freight_charge)
        print("Fuel Charge:", fuel_charge)

        print("\nFilling Freight Charge Total...")
        page.locator(
            "#divFinancialInformation_Financialinformation1_freightcharge_total"
        ).fill(str(freight_charge))

        print("Filling Fuel Surcharge Total...")
        page.locator(
            "#divFinancialInformation_Financialinformation1_fuelsurcharge_total"
        ).fill(str(fuel_charge))

        print("\nReading Tractor 1...")
        tractor = page.locator(TRACTOR_SELECTOR).input_value().strip()

        if not tractor:
            print("\nSTOP")
            print("No Tractor 1 is selected.")
            print("Please select Tractor 1 and run COA again.")
            input("\nPress ENTER to disconnect...")
            browser.close()
            return

        print("Tractor:")
        print(tractor)

        if tractor not in equipment:
            print("\nSTOP")
            print(f"No equipment record found for tractor: {tractor}")
            input("\nPress ENTER to disconnect...")
            browser.close()
            return

        trailer = equipment[tractor]["trailer"]

        print("\nFilling Trailer...")
        print("Trailer:", trailer)
        page.locator(TRAILER_SELECTOR).fill(trailer)

        print("\nFilling Delivery Appointment Date...")
        page.locator(DELIVERY_DATE_SELECTOR).fill(delivery_date)

        print("Filling Delivery Appointment Time...")
        page.locator(DELIVERY_TIME_SELECTOR).fill(delivery_time)

        print("\nClicking Calculate Pay Percentage...")
        page.locator(CALCULATE_PAY_SELECTOR).click()
        page.wait_for_timeout(2000)

        print("\nDone. Review the billing screen before booking.")

        input("\nPress ENTER to disconnect...")

        browser.close()