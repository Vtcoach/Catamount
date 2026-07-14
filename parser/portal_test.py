from playwright.sync_api import sync_playwright

print("Starting portal test...")

PROFILE_DIR = r"C:\Users\Trent Benoit\AppData\Local\Google\Chrome\User Data"

with sync_playwright() as p:
    print("Launching persistent browser profile...")

    context = p.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=False,
        channel="chrome",
        slow_mo=250,
        args=["--profile-directory=Default"]
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("Opening Evans billing screen directly...")

    page.goto("https://agents.evansdelivery.com/billing/ecdefault.aspx")

    print("Current page title:")
    print(page.title())
    print("Current URL:")
    print(page.url)

    input("Press ENTER to close...")

    context.close()