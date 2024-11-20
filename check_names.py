import time
from playwright.sync_api import sync_playwright

def check_available_usernames(usernames, isLogin = False, headless = True):
    url = "https://web.telegram.org"
    user_data_dir = "./user_data"

    available_usernames = []
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless
        )
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        if(isLogin):
            time.sleep(999999)

        page.locator("button[aria-label='Open menu']").click()
        page.locator("div.MenuItem.compact", has_text="Settings").click()
        page.locator("button.Button[title='Edit profile']").click()
        time.sleep(1)

        for username in usernames:
            input_locator = page.locator("div.settings-item:not(.settings-edit-profile)").locator("div.touched.with-label")
            input_locator.locator("input").fill(username)
            time.sleep(0.5)

            while input_locator.locator("label").text_content() == "Checking...":
                time.sleep(0.5)

            if input_locator.locator("label").text_content() == "Username is available.":
                available_usernames.append(username)
                if len(available_usernames)>=25:
                    break

    return available_usernames


# Раскоментировать для входа
# check_available_usernames(["coder"], True, False)