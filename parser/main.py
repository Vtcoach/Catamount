from browser import fill_billing_screen
import json
import os
import fitz
import re
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from diagnostics import run_diagnostics


VERSION = "1.0.0-beta"


def load_brokers():
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "config",
        "brokers.json"
    )

    with open(config_path, "r") as f:
        return json.load(f)


def load_concepts():
    concepts_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "config",
        "concepts.json"
    )

    with open(concepts_path, "r") as f:
        return json.load(f)


def read_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()
    return text


def get_concept_labels(concepts, concept_name):
    return concepts["concepts"][concept_name]["labels"]


def identify_broker(text, brokers):
    for broker in brokers["brokers"]:
        for alias in broker["aliases"]:
            if alias.upper() in text.upper():
                return broker

    return None


def extract_load_number(text, concepts):
    labels = get_concept_labels(concepts, "Primary Operational Reference")

    for label in labels:
        escaped = re.escape(label)
        pattern = rf"{escaped}[:\s#]*([A-Za-z0-9-]+)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1)

    return "UNKNOWN"


def extract_revenue(text, concepts):
    labels = get_concept_labels(concepts, "Revenue")

    for label in labels:
        escaped = re.escape(label)
        pattern = rf"{escaped}[:\s]*\$?([0-9,]+\.[0-9]{{2}})"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1)

    return "UNKNOWN"


def extract_weight(text, concepts):
    labels = get_concept_labels(concepts, "Weight")

    for label in labels:
        escaped = re.escape(label)
        pattern = rf"{escaped}[:\s]*([0-9,]+)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1)

    return "UNKNOWN"


def extract_pickup(text, concepts):
    labels = get_concept_labels(concepts, "Pickup")

    for label in labels:
        escaped = re.escape(label)
        pattern = rf"{escaped}.*?\n([A-Za-z .'-]+,\s*[A-Z]{{2}})"

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            return match.group(1).strip()

    return "UNKNOWN"


def extract_delivery(text, concepts):
    labels = get_concept_labels(concepts, "Delivery")

    for label in labels:
        escaped = re.escape(label)
        pattern = rf"{escaped}.*?\n([A-Za-z .'-]+,\s*[A-Z]{{2}})"

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if matches:
            return matches[-1].strip()

    return "UNKNOWN"


def clean_name_line(name):
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    return name


def extract_tql_stop_data(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    pickup_name = "UNKNOWN"
    delivery_name = "UNKNOWN"
    pickup_address = "UNKNOWN"
    delivery_address = "UNKNOWN"

    pickup_section_index = None

    for index, line in enumerate(lines):
        upper_line = line.upper()

        if upper_line == "PICKUPS":
            pickup_section_index = index

    if pickup_section_index is not None:
        for index in range(pickup_section_index + 1, len(lines)):
            line = lines[index]
            upper_line = line.upper()

            if upper_line in ["SHED", "CITY", "STATE ZIP", "PU#", "DATE", "TIME"]:
                continue

            pickup_name = clean_name_line(line)
            break

    for index, line in enumerate(lines):
        if line.upper() == "CONSIGNEE":
            delivery_parts = []

            for nearby in lines[index + 1:index + 6]:
                upper_nearby = nearby.upper()

                if upper_nearby in ["CITY", "STATE ZIP", "DELIVERY PO", "DATE", "TIME"]:
                    continue

                if re.search(r"\d", nearby):
                    break

                delivery_parts.append(nearby)

            if delivery_parts:
                delivery_name = clean_name_line(" ".join(delivery_parts))

            break

    information_addresses = []

    for index, line in enumerate(lines):
        if line.upper() == "INFORMATION:":
            if index + 1 < len(lines):
                address = lines[index + 1].strip()

                if re.search(r"\d+\s+[A-Za-z0-9 .'-]+", address):
                    information_addresses.append(address)

    if len(information_addresses) >= 1:
        pickup_address = information_addresses[0]

    if len(information_addresses) >= 2:
        delivery_address = information_addresses[-1]

    return {
        "pickup_name": pickup_name,
        "pickup_address": pickup_address,
        "delivery_name": delivery_name,
        "delivery_address": delivery_address
    }


def format_city_state(line):
    parts = line.strip().split()

    if len(parts) >= 3 and len(parts[-2]) == 2:
        city = " ".join(parts[:-2]).title()
        state = parts[-2].upper()
        return f"{city}, {state}"

    return line.strip()


def extract_hub_stop_data(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    def extract_stop(start_label):
        stop_index = None

        for index, line in enumerate(lines):
            if line.upper() == start_label:
                stop_index = index
                break

        if stop_index is None:
            return {
                "name": "UNKNOWN",
                "address": "UNKNOWN",
                "city_state": "UNKNOWN"
            }

        for index in range(stop_index + 1, min(stop_index + 15, len(lines))):
            line = lines[index]

            if not line.upper().startswith("ADDRESS:"):
                continue

            remainder = line.split(":", 1)[1].strip()

            if remainder:
                name = remainder
                detail_start = index + 1
            else:
                name = lines[index + 1] if index + 1 < len(lines) else "UNKNOWN"
                detail_start = index + 2

            street_address = "UNKNOWN"
            city = "UNKNOWN"
            state = "UNKNOWN"

            detail_lines = lines[
                detail_start:min(detail_start + 10, len(lines))
            ]

            for detail_index, detail_line in enumerate(detail_lines):
                if re.match(r"^\d+\s+", detail_line):
                    street_address = detail_line
                    continue

                if (
                    detail_index + 2 < len(detail_lines)
                    and re.fullmatch(r"[A-Za-z .'-]+", detail_line)
                    and re.fullmatch(r"[A-Z]{2}", detail_lines[detail_index + 1])
                    and re.fullmatch(r"\d{5,9}", detail_lines[detail_index + 2])
                ):
                    city = detail_line.title()
                    state = detail_lines[detail_index + 1].upper()
                    break

                combined_match = re.match(
                    r"^(.+?)\s+([A-Z]{2})\s+(\d{5,9})$",
                    detail_line,
                    re.IGNORECASE
                )

                if combined_match:
                    city = combined_match.group(1).title()
                    state = combined_match.group(2).upper()
                    break

            city_state = (
                f"{city}, {state}"
                if city != "UNKNOWN" and state != "UNKNOWN"
                else "UNKNOWN"
            )

            return {
                "name": clean_name_line(name),
                "address": street_address,
                "city_state": city_state
            }

        return {
            "name": "UNKNOWN",
            "address": "UNKNOWN",
            "city_state": "UNKNOWN"
        }

    pickup = extract_stop("ORIGIN #1:")
    delivery = extract_stop("CONSIGNEE #1:")

    return {
        "pickup_name": pickup["name"],
        "pickup_address": pickup["address"],
        "pickup": pickup["city_state"],
        "delivery_name": delivery["name"],
        "delivery_address": delivery["address"],
        "delivery": delivery["city_state"]
    }

def extract_hub_revenue(text):
    match = re.search(
        r"Grand Total:\s*\$?([0-9,]+\.[0-9]{2})",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return "UNKNOWN"


def extract_hub_load_number(text):
    match = re.search(
        r"Load\s*#\s*([0-9]+)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return "UNKNOWN"


def extract_hub_delivery_appointment(text):
    consignee_match = re.search(
        r"Consignee\s*#1:.*?Appointment:\s*Start:\s*"
        r"(\d{1,2})/(\d{1,2})/(\d{4})\s+"
        r"(\d{1,2}):(\d{2})\s*(AM|PM)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not consignee_match:
        return {
            "date": "UNKNOWN",
            "time": "UNKNOWN"
        }

    month, day, year, hour, minute, ampm = consignee_match.groups()
    hour = int(hour)

    if ampm.upper() == "PM" and hour != 12:
        hour += 12
    elif ampm.upper() == "AM" and hour == 12:
        hour = 0

    return {
        "date": f"{int(month):02d}{int(day):02d}{year}",
        "time": f"{hour:02d}{minute}"
    }



def extract_armstrong_stop_data(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    def extract_stop(label):
        try:
            stop_index = next(
                index
                for index, line in enumerate(lines)
                if line.upper() == label
            )
        except StopIteration:
            return {
                "name": "UNKNOWN",
                "address": "UNKNOWN",
                "city_state": "UNKNOWN"
            }

        name = (
            lines[stop_index + 1]
            if stop_index + 1 < len(lines)
            else "UNKNOWN"
        )

        address = "UNKNOWN"
        city_state = "UNKNOWN"

        for line in lines[stop_index + 1:stop_index + 12]:
            if address == "UNKNOWN" and re.match(r"^\d+\s+", line):
                address = line
                continue

            city_match = re.match(
                r"^(.+?),\s*([A-Z]{2}),?\s*\d{5}(?:-\d{4})?$",
                line,
                re.IGNORECASE
            )

            if city_match:
                city = city_match.group(1).strip().title()
                state = city_match.group(2).upper()
                city_state = f"{city}, {state}"
                break

        return {
            "name": clean_name_line(name),
            "address": address,
            "city_state": city_state
        }

    pickup = extract_stop("PICKUP")
    delivery = extract_stop("DROPOFF")

    return {
        "pickup_name": pickup["name"],
        "pickup_address": pickup["address"],
        "pickup": pickup["city_state"],
        "delivery_name": delivery["name"],
        "delivery_address": delivery["address"],
        "delivery": delivery["city_state"]
    }


def extract_armstrong_delivery_appointment(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    try:
        dropoff_index = next(
            index
            for index, line in enumerate(lines)
            if line.upper() == "DROPOFF"
        )
    except StopIteration:
        return {
            "date": "UNKNOWN",
            "time": "UNKNOWN"
        }

    delivery_date = "UNKNOWN"

    for index in range(dropoff_index - 1, max(-1, dropoff_index - 5), -1):
        date_match = re.fullmatch(
            r"(\d{1,2})/(\d{1,2})/(\d{4})",
            lines[index]
        )

        if date_match:
            month, day, year = date_match.groups()
            delivery_date = f"{int(month):02d}{int(day):02d}{year}"
            break

    delivery_time = "UNKNOWN"

    for line in lines[dropoff_index + 1:dropoff_index + 15]:
        time_match = re.search(r"\b(\d{1,2}):(\d{2})\b", line)

        if time_match:
            hour, minute = time_match.groups()
            delivery_time = f"{int(hour):02d}{minute}"
            break

    return {
        "date": delivery_date,
        "time": delivery_time
    }



def extract_information_addresses(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    addresses = []

    for index, line in enumerate(lines):
        if line.upper() == "INFORMATION:":
            if index + 1 < len(lines):
                address = lines[index + 1].strip()

                if re.search(r"\d+\s+[A-Za-z0-9 .'-]+", address):
                    addresses.append(address)

    return addresses


def extract_pickup_address(text):
    addresses = extract_information_addresses(text)

    if addresses:
        return addresses[0]

    return "UNKNOWN"


def extract_delivery_address(text):
    addresses = extract_information_addresses(text)

    if len(addresses) >= 2:
        return addresses[-1]

    return "UNKNOWN"


brokers = load_brokers()
concepts = load_concepts()

print("=" * 50)
print(f"Catamount COA v{VERSION}")
print("Carrier Onboarding Assistant")
print("=" * 50)

Tk().withdraw()

rate_pdf = askopenfilename(
    title="Select Rate Confirmation PDF",
    filetypes=[("PDF Files", "*.pdf")]
)

if not rate_pdf:
    print("No rate confirmation selected.")
    exit()

print(f"\nReading Rate Confirmation:\n{rate_pdf}\n")

rate_text = read_pdf(rate_pdf)

broker_profile = identify_broker(rate_text, brokers)

if broker_profile:
    broker_name = broker_profile["name"]
    bill_to_code = broker_profile.get("bill_to_code", "UNKNOWN")
else:
    broker_name = "UNKNOWN"
    bill_to_code = "UNKNOWN"
    broker_profile = {}

workflow = broker_profile.get("workflow", {})
field_sources = broker_profile.get("field_sources", {})

requires_supporting_document = workflow.get(
    "requires_supporting_document",
    False
)

supporting_document_name = workflow.get(
    "supporting_document_name",
    "Supporting Document"
)

supporting_text = ""

if requires_supporting_document:
    supporting_pdf = askopenfilename(
        title=f"Select {supporting_document_name} PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )

    if not supporting_pdf:
        print(f"No {supporting_document_name} selected.")
        exit()

    print(f"\nReading {supporting_document_name}:\n{supporting_pdf}\n")
    supporting_text = read_pdf(supporting_pdf)

combined_text = rate_text + "\n" + supporting_text

load_number = extract_load_number(combined_text, concepts)
revenue = extract_revenue(rate_text, concepts)
weight = extract_weight(combined_text, concepts)
pickup = extract_pickup(combined_text, concepts)
delivery = extract_delivery(combined_text, concepts)

pickup_name = "UNKNOWN"
delivery_name = "UNKNOWN"
pickup_address = "UNKNOWN"
delivery_address = "UNKNOWN"

delivery_appointment = {
    "date": "07072026",
    "time": "0830"
}

broker_id = broker_profile.get("id", "")

if requires_supporting_document and broker_id == "TQL":
    stop_data = extract_tql_stop_data(supporting_text)

    pickup_name = stop_data["pickup_name"]
    delivery_name = stop_data["delivery_name"]
    pickup_address = stop_data["pickup_address"]
    delivery_address = stop_data["delivery_address"]

elif broker_id == "HUB":
    stop_data = extract_hub_stop_data(rate_text)

    load_number = extract_hub_load_number(rate_text)
    revenue = extract_hub_revenue(rate_text)
    delivery_appointment = extract_hub_delivery_appointment(rate_text)

    pickup_name = stop_data["pickup_name"]
    pickup_address = stop_data["pickup_address"]
    pickup = stop_data["pickup"]

    delivery_name = stop_data["delivery_name"]
    delivery_address = stop_data["delivery_address"]
    delivery = stop_data["delivery"]

elif broker_id == "ARMSTRONG":
    stop_data = extract_armstrong_stop_data(rate_text)
    delivery_appointment = extract_armstrong_delivery_appointment(rate_text)

    pickup_name = stop_data["pickup_name"]
    pickup_address = stop_data["pickup_address"]
    pickup = stop_data["pickup"]

    delivery_name = stop_data["delivery_name"]
    delivery_address = stop_data["delivery_address"]
    delivery = stop_data["delivery"]

else:
    pickup_address_source = field_sources.get(
        "pickup_address",
        "rate_confirmation"
    )

    delivery_address_source = field_sources.get(
        "delivery_address",
        "rate_confirmation"
    )

    if pickup_address_source == "supporting_document":
        pickup_address = extract_pickup_address(supporting_text)
    else:
        pickup_address = extract_pickup_address(rate_text)

    if delivery_address_source == "supporting_document":
        delivery_address = extract_delivery_address(supporting_text)
    else:
        delivery_address = extract_delivery_address(rate_text)

if revenue != "UNKNOWN":
    total_revenue = float(revenue.replace(",", ""))
    freight_charges = round(total_revenue * 0.72, 2)
    fuel_charges = round(total_revenue - freight_charges, 2)
else:
    total_revenue = "UNKNOWN"
    freight_charges = "UNKNOWN"
    fuel_charges = "UNKNOWN"

load = {
    "broker": broker_name,
    "bill_to_code": bill_to_code,
    "load_number": load_number,
    "revenue": total_revenue,
    "pickup": pickup,
    "pickup_name": pickup_name,
    "pickup_address": pickup_address,
    "delivery": delivery,
    "delivery_name": delivery_name,
    "delivery_address": delivery_address,

    "delivery_appointment": delivery_appointment,

    "billing": {
        "total_revenue": total_revenue,
        "freight_charges": freight_charges,
        "fuel_charges": fuel_charges
    },

    "status": "",
    "warnings": [],
    "confidence": {}
}

if load["broker"] == "UNKNOWN":
    load["warnings"].append("Broker could not be identified.")

if load["bill_to_code"] == "UNKNOWN":
    load["warnings"].append("Bill To code could not be identified.")

if load["load_number"] == "UNKNOWN":
    load["warnings"].append("Load number could not be identified.")

if revenue == "UNKNOWN":
    load["warnings"].append("Revenue could not be identified.")

if load["pickup"] == "UNKNOWN":
    load["warnings"].append("Pickup location could not be identified.")

if load["pickup_address"] == "UNKNOWN" and load["pickup_name"] == "UNKNOWN":
    load["warnings"].append(
        "Pickup customer could not be identified by address or name."
    )

if load["delivery"] == "UNKNOWN":
    load["warnings"].append("Delivery location could not be identified.")

if load["delivery_address"] == "UNKNOWN" and load["delivery_name"] == "UNKNOWN":
    load["warnings"].append(
        "Delivery customer could not be identified by address or name."
    )

load["confidence"]["Broker"] = 100 if load["broker"] != "UNKNOWN" else 0

required_fields_found = all([
    load["broker"] != "UNKNOWN",
    load["bill_to_code"] != "UNKNOWN",
    load["load_number"] != "UNKNOWN",
    load["revenue"] != "UNKNOWN",
    load["pickup"] != "UNKNOWN",
    load["delivery"] != "UNKNOWN",
    (
        load["pickup_address"] != "UNKNOWN"
        or load["pickup_name"] != "UNKNOWN"
    ),
    (
        load["delivery_address"] != "UNKNOWN"
        or load["delivery_name"] != "UNKNOWN"
    )
])

if not required_fields_found:
    load["status"] = "REVIEW REQUIRED"
elif load["warnings"]:
    load["status"] = "READY WITH WARNINGS"
else:
    load["status"] = "READY"

validation = {
    "Broker": load["broker"] != "UNKNOWN",
    "Bill To Code": load["bill_to_code"] != "UNKNOWN",
    "Load Number": load["load_number"] != "UNKNOWN",
    "Revenue": load["revenue"] != "UNKNOWN",
    "Pickup": load["pickup"] != "UNKNOWN",
    "Pickup Customer": (
        load["pickup_address"] != "UNKNOWN"
        or load["pickup_name"] != "UNKNOWN"
    ),
    "Delivery": load["delivery"] != "UNKNOWN",
    "Delivery Customer": (
        load["delivery_address"] != "UNKNOWN"
        or load["delivery_name"] != "UNKNOWN"
    )
}

print("\nBroker:")
print(load["broker"])

print("\nBill To Code:")
print(load["bill_to_code"])

print("\nLoad Number:")
print(load["load_number"])

print("\nRevenue:")
print(load["revenue"])

print("\nPickup:")
print(load["pickup"])

print("\nPickup Name:")
print(load["pickup_name"])

print("\nPickup Address:")
print(load["pickup_address"])

print("\nDelivery:")
print(load["delivery"])

print("\nDelivery Name:")
print(load["delivery_name"])

print("\nDelivery Address:")
print(load["delivery_address"])

print("\nDelivery Appointment:")
print(load["delivery_appointment"]["date"])
print(load["delivery_appointment"]["time"])

if load["status"] == "READY":
    status_icon = "🟢"
elif load["status"] == "READY WITH WARNINGS":
    status_icon = "🟡"
else:
    status_icon = "🔴"

print("\nStatus:")
print(f"{status_icon} {load['status']}")

print("\nValidation:")

for field, passed in validation.items():
    if passed:
        print(f"✓ {field}")
    else:
        print(f"✗ {field}")

if load["warnings"]:
    print("\nWarnings:")
    for warning in load["warnings"]:
        print(f"• {warning}")

run_diagnostics(load, validation)

if load["status"] == "READY":
    print("\nSending load to Evans portal...")
    fill_billing_screen(load)
else:
    print("\nLoad not sent to Evans portal.")
    print("Reason: Load status is not READY.")

print("\nFinished.")