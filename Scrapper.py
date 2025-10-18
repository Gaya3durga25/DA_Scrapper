from playwright.sync_api import sync_playwright
import time
import csv
from urllib.parse import urljoin

BASE_URL = "https://www3.shoalhaven.nsw.gov.au/masterviewUI/modules/ApplicationMaster/Default.aspx"

def scrape_shoalhaven_da():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Step 1: Open site and click Agree
        page.goto(BASE_URL)
        page.wait_for_selector("#ctl00_cphContent_ctl01_btnOk", timeout=20000).click()
        print("✅ 'Agree' clicked")
        time.sleep(2)

        # Step 2: Click DA Tracking
        page.wait_for_selector("text='DA Tracking'", timeout=10000).click()
        print("✅ 'DA Tracking' clicked")
        time.sleep(2)

        # Step 3: Click Advanced Search
        page.wait_for_selector("text='Advanced Search'", timeout=10000).click()
        print("✅ 'Advanced Search' clicked")
        time.sleep(2)

        # Step 4: Fill date range
        page.fill("#ctl00_cphContent_ctl00_ctl03_dateInput_text", "01/09/2025")  # From
        page.fill("#ctl00_cphContent_ctl00_ctl05_dateInput_text", "30/09/2025")  # To
        print("✅ Date range filled")

        # Step 5: Click Search
        page.click("#ctl00_cphContent_ctl00_btnSearch")
        print("✅ Search clicked, waiting for results...")
        time.sleep(5)

        all_records = []

        while True:
            # Wait for grid rows
            page.wait_for_selector("table[id*='RadGrid1'] tr.rgRow, table[id*='RadGrid1'] tr.rgAltRow", timeout=15000)
            rows = page.query_selector_all("table[id*='RadGrid1'] tr.rgRow, table[id*='RadGrid1'] tr.rgAltRow")

            for row in rows:
                cells = row.query_selector_all("td")
                if len(cells) >= 4:
                    da_number = cells[1].inner_text().strip()
                    address = cells[3].inner_text().strip()
                    link_tag = cells[0].query_selector("a")
                    details_href = link_tag.get_attribute("href") if link_tag else None
                    if details_href:
                        details_url = urljoin(BASE_URL, details_href)
                    else:
                        details_url = None

                    all_records.append({
                        "DA_Number": da_number,
                        "Property_Address": address,
                        "Detail_URL": details_url
                    })

            # Check for next page
            next_button = page.query_selector("a[id*='_Next']")
            if next_button and "rcDisabled" not in next_button.get_attribute("class"):
                next_button.click()
                print("➡️ Moving to next page...")
                time.sleep(3)
            else:
                print("🏁 All pages collected")
                break

        print(f"🎉 Total records found: {len(all_records)}")

        # Step 6: Visit each detail page
        for idx, record in enumerate(all_records):
            if not record["Detail_URL"]:
                continue
            page.goto(record["Detail_URL"])
            time.sleep(2)

            # Description
            try:
                desc_el = page.query_selector("span[id*='lblDescription']")
                record["Description"] = desc_el.inner_text().strip() if desc_el else ""
            except:
                record["Description"] = ""

            # Submitted Date
            try:
                sub_el = page.query_selector("span[id*='lblSubmittedDate']")
                record["Submitted_Date"] = sub_el.inner_text().strip() if sub_el else ""
            except:
                record["Submitted_Date"] = ""

            # Decision
            try:
                dec_el = page.query_selector("span[id*='lblDecision']")
                record["Decision"] = dec_el.inner_text().strip() if dec_el else ""
            except:
                record["Decision"] = ""

            # Categories
            try:
                cat_el = page.query_selector("span[id*='lblCategories']")
                record["Categories"] = cat_el.inner_text().strip() if cat_el else ""
            except:
                record["Categories"] = ""

            # Applicant
            try:
                app_el = page.query_selector("span[id*='lblApplicant']")
                record["Applicant"] = app_el.inner_text().strip() if app_el else ""
            except:
                record["Applicant"] = ""

            # Progress
            try:
                prog_el = page.query_selector("div[id*='Progress']")
                record["Progress"] = prog_el.inner_text().strip() if prog_el else ""
            except:
                record["Progress"] = ""

            # Fees
            try:
                fees_el = page.query_selector("span[id*='lblFees']")
                fees_text = fees_el.inner_text().strip() if fees_el else ""
                record["Fees"] = "Not required" if fees_text == "No fees recorded against this application." else fees_text
            except:
                record["Fees"] = ""

            # Documents
            try:
                docs_el = page.query_selector("div[id*='Documents']")
                record["Documents"] = docs_el.inner_text().strip() if docs_el else ""
            except:
                record["Documents"] = ""

            # Contact Council
            try:
                cc_el = page.query_selector("div[id*='ContactCouncil']")
                cc_text = cc_el.inner_text().strip() if cc_el else ""
                record["Contact_Council"] = "Not required" if cc_text == "Application Is Not on exhibition, please call Council on 1300 293 111 if you require assistance." else cc_text
            except:
                record["Contact_Council"] = ""

            print(f"✅ Scraped detail page {idx+1}/{len(all_records)}")

        # Step 7: Save to CSV
        headers = ["DA_Number", "Detail_URL", "Description", "Submitted_Date", "Decision", "Categories",
                   "Property_Address", "Applicant", "Progress", "Fees", "Documents", "Contact_Council"]

        with open("da_records_full.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for rec in all_records:
                writer.writerow(rec)

        print("✅ Data saved to da_records_full.csv")
        browser.close()


if __name__ == "__main__":
    scrape_shoalhaven_da()
