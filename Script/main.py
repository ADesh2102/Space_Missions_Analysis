from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = 'https://nextspaceflight.com/launches/past/?search='

option = Options()
option.add_argument("--headless")
option.add_argument("--disable-gpu")
option.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=option)
driver.get(URL)

wait = WebDriverWait(driver, 10)
launch_data = []
page_count = 1
MAX_PAGE = 235

while page_count <= MAX_PAGE:
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'launch')))
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    launch_cards = soup.find_all("div", class_='launch')
    selenium_cards = driver.find_elements(By.CLASS_NAME, "launch")

    for i, card in enumerate(launch_cards, start=1):
        Details = card.find("h5", class_="header-style")
        mission_details = Details.get_text(strip=True) if Details else None

        organization = card.find("div", class_="mdl-card__title-text")
        organization_name = organization.find("span", style="color: black").get_text(
            strip=True) if organization else None

        Location = card.find("div", class_="mdl-card__supporting-text")
        if Location:
            br = Location.find("br")
            if br and br.next_sibling:
                Location = br.next_sibling.strip()
        else:
            Location = None

        date_span = card.find("span", id=lambda x: x and x.startswith("localized"))
        Date = date_span.get_text(strip=True) if date_span else None


        selenium_card = selenium_cards[i - 1]

        try:
            detail_button = selenium_card.find_element(By.CSS_SELECTOR, 'a.mdc-button')
            detail_url = detail_button.get_attribute("href")
        except Exception as e:
            print(f"Could not find details link for card {i}: {e}")
            detail_url = None

        Rocket_status = Price = Mission_status = None

        # If details link is found, open and scrape it
        if detail_url:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(detail_url)

            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'rcorners')))
                detail_html = driver.page_source
                soup = BeautifulSoup(detail_html, 'html.parser')

                rocket_info_div = soup.find("div", class_="mdl-grid a", style="margin: -10px")
                if rocket_info_div:
                    for cell in rocket_info_div.find_all("div", class_="mdl-cell"):
                        text = cell.get_text(strip=True)
                        if "Status:" in text:
                            Rocket_status = text.split("Status:")[1].strip()
                        elif "Price:" in text:
                            Price = text.split("Price:")[1].replace("$", "").replace("million", "").strip()

                mission_status_div = soup.find("h6", class_="rcorners status")
                if mission_status_div:
                    Mission_status = mission_status_div.get_text(strip=True)

            except Exception as e:
                print(f"Failed to scrape details page for card {i}: {e}")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        launch_data.append([organization_name, Location, Date, mission_details, Rocket_status, Price, Mission_status])

    # Find the "Next" button 
    try:
        buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.mdc-button.mdc-button--raised')))
        next_button = None
        for button in buttons:
            label = button.find_element(By.CSS_SELECTOR, 'span.mdc-button__label').text.strip().lower()
            if label == 'next':
                next_button = button
                break

        if next_button:
            next_button.click()
            page_count += 1
            print(f"Navigating to page {page_count}: {driver.current_url}")
            time.sleep(3)
        else:
            print("No more pages")
            break
    except Exception as e:
        print(f"Error while finding next button: {e}")
        break

driver.quit()

df = pd.DataFrame(launch_data,
                  columns=['Organization', 'Location', 'Date', 'Details', 'Rocket_Status', 'Price', 'Mission_Status'])

df.to_csv('past_launches1.csv', index=False)

print("Scraping complete")
