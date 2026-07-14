from dataclasses import dataclass
import re


@dataclass
class Location:
    account: str
    name: str
    address: str
    city: str
    state: str
    zip: str


@dataclass
class MatchResult:
    location: Location | None
    method: str
    confidence: str
    message: str


ADDRESS_REPLACEMENTS = {
    "STREET": "ST",
    "AVENUE": "AVE",
    "ROAD": "RD",
    "BOULEVARD": "BLVD",
    "HIGHWAY": "HWY",
    "DRIVE": "DR",
    "LANE": "LN",
    "COURT": "CT",
    "PLACE": "PL",
    "PARKWAY": "PKWY",
    "TERRACE": "TER",
    "CIRCLE": "CIR",
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
}


def wait_for_evans_ready(page):
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1200)


def safe_postback(page, target, argument, retries=3):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            wait_for_evans_ready(page)

            page.evaluate(
                """([targetName, eventArgument]) => {
                    __doPostBack(targetName, eventArgument);
                }""",
                [target, argument],
            )

            wait_for_evans_ready(page)
            return

        except Exception as error:
            last_error = error
            print(f"Postback attempt {attempt} failed. Retrying...")
            page.wait_for_timeout(2000)

    raise last_error


def parse_city_state_zip(text):
    match = re.search(r"(.+?),\s*([A-Z]{2})\s*(\d{5})?", text.strip())

    if not match:
        return "", "", ""

    return (
        match.group(1).strip(),
        match.group(2).strip(),
        match.group(3).strip() if match.group(3) else "",
    )


def normalize_address(address):
    value = address.upper().strip()
    value = re.sub(r"[.,#]", " ", value)
    value = re.sub(r"\s+", " ", value)

    value = re.sub(
    r"\s+(N|S|E|W|NE|NW|SE|SW)$",
    "",
    value
    )

    words = value.split()

    normalized_words = [
        ADDRESS_REPLACEMENTS.get(word, word)
        for word in words
    ]

    return " ".join(normalized_words)


def normalize_name(name):
    value = name.upper().strip()
    value = re.sub(r"[.,#()]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def find_location_by_address(target_address, locations):
    if not target_address or target_address == "UNKNOWN":
        return None

    normalized_target = normalize_address(target_address)

    for location in locations:
        normalized_location = normalize_address(location.address)

        if normalized_target == normalized_location:
            return location

    return None


def find_location_by_name(target_name, locations):
    if not target_name or target_name == "UNKNOWN":
        return None

    normalized_target = normalize_name(target_name)
    matches = []

    for location in locations:
        normalized_location = normalize_name(location.name)

        if normalized_target == normalized_location:
            matches.append(location)
        elif normalized_target in normalized_location:
            matches.append(location)
        elif normalized_location in normalized_target:
            matches.append(location)

    if len(matches) == 1:
        return matches[0]

    return None


def resolve_customer(target_address, target_name, locations):
    address_match = find_location_by_address(target_address, locations)

    if address_match:
        return MatchResult(
            location=address_match,
            method="address",
            confidence="HIGH",
            message="Exact street address match."
        )

    name_match = find_location_by_name(target_name, locations)

    if name_match:
        return MatchResult(
            location=name_match,
            method="name",
            confidence="MEDIUM-HIGH",
            message="Matched by customer/facility name. Address was not matched."
        )

    if len(locations) == 1:
        return MatchResult(
            location=locations[0],
            method="single_city_result",
            confidence="MEDIUM",
            message="Only one customer found in searched city."
        )

    return MatchResult(
        location=None,
        method="manual_review",
        confidence="LOW",
        message="No reliable address, name, or single-result match found."
    )


def open_lookup(page, section):
    if section not in ["from", "to"]:
        raise ValueError("section must be 'from' or 'to'")

    safe_postback(
        page,
        f"{section}$accountSelection1",
        "enhancedlookup"
    )


def search_lookup_city(page, city):
    wait_for_evans_ready(page)

    page.locator("#AccountLookupControl1_City").fill(city)

    safe_postback(
        page,
        "AccountLookupControl1$GoButton",
        ""
    )

    page.wait_for_function(
        "() => document.body.innerText.includes('TDW')",
        timeout=15000,
    )

    wait_for_evans_ready(page)


def read_current_page_results(page):
    locations = []
    rows = page.locator("tr")

    for row_index in range(rows.count()):
        row = rows.nth(row_index)
        cells = row.locator("td")

        if cells.count() < 3:
            continue

        account = cells.nth(0).inner_text().strip()

        if not account.startswith("TDW"):
            continue

        name = cells.nth(1).inner_text().strip()
        location_text = cells.nth(2).inner_text().strip()

        parts = [
            line.strip()
            for line in location_text.splitlines()
            if line.strip()
        ]

        address = parts[0] if len(parts) >= 1 else ""
        city_state_zip = parts[1] if len(parts) >= 2 else ""

        if len(parts) == 1 and "," in address:
            city, state, zipcode = parse_city_state_zip(address)
            address = ""
        else:
            city, state, zipcode = parse_city_state_zip(city_state_zip)

        locations.append(
            Location(
                account=account,
                name=name,
                address=address,
                city=city,
                state=state,
                zip=zipcode,
            )
        )

    return locations


def click_next_results_page(page):
    next_link = page.locator(
        "a",
        has_text=re.compile(r"^\s*Next\s*$", re.IGNORECASE)
    )

    if next_link.count() == 0:
        return False

    link = next_link.first

    if not link.is_visible():
        return False

    link.click()
    wait_for_evans_ready(page)
    return True


def read_lookup_results(page):
    wait_for_evans_ready(page)

    all_locations = []
    seen_accounts = set()
    page_number = 1

    while True:
        current_locations = read_current_page_results(page)

        for location in current_locations:
            if location.account in seen_accounts:
                continue

            seen_accounts.add(location.account)
            all_locations.append(location)

        print(f"Lookup page {page_number}: {len(current_locations)} locations")

        if not click_next_results_page(page):
            break

        page_number += 1

        if page_number > 25:
            print("STOP: lookup pagination exceeded 25 pages.")
            break

    return all_locations


def select_lookup_location(page, location):
    event_argument = f"select:{location.account}:{location.name}:TDW"

    safe_postback(
        page,
        "AccountLookupControl1",
        event_argument
    )