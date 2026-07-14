from playwright.sync_api import sync_playwright
import time

KEYWORDS = [
    "lookup",
    "account",
    "customer",
    "search",
    "city",
    "shipper",
    "consignee",
    "from",
    "to",
    "billing",
]

def interesting(url: str) -> bool:
    lower = url.lower()
    return any(word in lower for word in KEYWORDS)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]

    page = None
    for pg in context.pages:
        if "agents.evansdelivery.com/billing" in pg.url:
            page = pg
            break

    if page is None:
        print("Billing page not found.")
        input("Press ENTER to exit...")
        browser.close()
        raise SystemExit

    print("Connected to Billing:")
    print(page.url)

    print("\nWatching network traffic...")
    print("Now manually do the FROM Enhanced Lookup exactly as you normally would.")
    print("Search by city, select the address, then return here.")
    print("\nPress ENTER in this terminal AFTER you finish the lookup.\n")

    def log_request(request):
        if interesting(request.url):
            print("\nREQUEST")
            print("-" * 60)
            print("METHOD:", request.method)
            print("URL:", request.url)
            try:
                data = request.post_data
                if data:
                    print("POST DATA:")
                    print(data[:2000])
            except:
                pass

    def log_response(response):
        if interesting(response.url):
            print("\nRESPONSE")
            print("-" * 60)
            print("STATUS:", response.status)
            print("URL:", response.url)
            try:
                body = response.text()
                if body:
                    print("BODY PREVIEW:")
                    print(body[:2000])
            except:
                pass

    page.on("request", log_request)
    page.on("response", log_response)

    input()

    print("\nDone watching.")
    browser.close()