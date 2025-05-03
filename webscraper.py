import re
import asyncio
from playwright.async_api import async_playwright

# Helper functions

# The function uses Playwright to extract job listings from a given URL in a
# headless browser, making it suitable for cloud-based environments like
# Render.com which is what I use. It navigates to the URL, waits for a specific
# element to load, processes the element, and returns the extracted data. The
# function accepts three arguments: the URL, and a callback function for
# processing. 
# LaunchNExtract
async def lne(url, fcn):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        out = await fcn(page)

        await browser.close()
        return out
    
def filter_description(description):
    sections = {
        "role_summary": "",
        "responsibilities": "",
        "qualifications": ""
    }

    # Normalize line breaks and spacing
    text = re.sub(r'\s+', ' ', description)

    # Pattern to identify the sections
    role_pattern = re.search(r'(Role Summary)(.*?)(?=Responsibilities|Qualifications|Pay Disclosure|Equal Opportunity)', text, re.IGNORECASE)
    resp_pattern = re.search(r'(Responsibilities)(.*?)(?=Qualifications|Pay Disclosure|Equal Opportunity)', text, re.IGNORECASE)
    qual_pattern = re.search(r'(Qualifications)(.*?)(?=Pay Disclosure|Equal Opportunity)', text, re.IGNORECASE)

    if role_pattern:
        sections["role_summary"] = role_pattern.group(2).strip()
    if resp_pattern:
        sections["responsibilities"] = resp_pattern.group(2).strip()
    if qual_pattern:
        sections["qualifications"] = qual_pattern.group(2).strip()

    return sections

async def scrape_rivian(page):
    await page.wait_for_selector("mat-expansion-panel")

    job_urls = []
    job_data = []
    filters = ["Internships"]

    # Before extracting job URLs, we will filter the jobs out using the categories
    # and locations we are interested in.
    print("Filtering jobs...")
    
    # Click the "Categories" dropdown based on its label
    label = await page.query_selector('label:has-text("Categories")')
    select_id = await label.get_attribute('for')  # e.g., 'mat-select-2'
    dropdown_selector = f'#{select_id}'
    await page.click(dropdown_selector)
    await page.wait_for_selector('mat-option')

    # Apply each filter. We only do Internships b/c Rivian stacks the filter results
    for filter in filters:
        option = await page.query_selector(f'mat-option:has-text("{filter}")')
        if option:
            await option.scroll_into_view_if_needed()
            await option.click()

    # Refresh page
    await page.click('body')
    await page.wait_for_load_state('networkidle')
    await page.wait_for_timeout(1000)
    print("Jobs filtered.")

    # First extract all job URLs. Never reuse elements (panel, etc.) after
    # page.goto() – they become invalid.
    # First extract all the data you can from the list view.
    # Then loop through the detailed pages with fresh navigations.
    while True:
        # Extract job URLs from the current page
        job_cards = await page.query_selector_all("mat-expansion-panel")
        for panel in job_cards:
            job_title_el = await panel.query_selector("a.job-title-link")
            if not job_title_el:
                full_url = "N/A"
                continue
            
            full_url = await job_title_el.get_attribute("href")
            if not full_url.startswith("http"):
                full_url = "https://careers.rivian.com" + full_url
            print(f"Found job URL: {full_url}")
            job_urls.append(full_url)            
            title_el = await panel.query_selector("a.job-title-link span")
            location_el = await panel.query_selector("span.location")
            category_el = await panel.query_selector("span.categories")
            apply_el = await panel.query_selector("a.apply-button")
            
            job_data.append({
                "title": await title_el.inner_text() if title_el else "N/A",
                "location": await location_el.inner_text() if location_el else "N/A",
                "category": await category_el.inner_text() if category_el else "N/A",
                "apply_link": await apply_el.get_attribute("href") if apply_el else "N/A",
                "url": full_url
            })
            
        # Attempt to click the "Next Page" button
        try:
            next_button = await page.query_selector('button[aria-label="Next Page of Job Search Results"]:not([disabled])')
            if next_button:
                await next_button.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(1000)  # Wait for new jobs to load
            else:
                print("No more pages to navigate.")
                break
        except Exception as e:
            print(f"Error navigating to next page: {e}")
            break
            
    # Once got all jobs, loop through them and extract the details.
    i = 1
    for url in job_urls:
        await page.goto(url)
        await page.wait_for_load_state("networkidle")

        # Try several possible selectors
        description = "N/A"
        for selector in ["#description-body", "div.job-description", "article.main-description-body"]:
            if await page.query_selector(selector):
                description = await page.inner_text(selector)
                break
        
        filtered_description = filter_description(description)
        
        # Find the job data entry that matches the URL
        for job in job_data:
            if job["url"] == url:
                job["role_summary"] = filtered_description["role_summary"]
                job["responsibilities"] = filtered_description["responsibilities"]
                job["qualifications"] = filtered_description["qualifications"]
                break
        
        print(f"Extracted data from Job ({i}/{len(job_urls)})")
        i += 1
    
    return job_data
    

def main():
    rivian_url = "https://careers.rivian.com/careers-home/jobs"   
    rivian_jobs = asyncio.run(lne(rivian_url, scrape_rivian))
    # Print or store data
    for job in rivian_jobs:
        print("\n======================")
        print(f"Title: {job['title']}\n")
        print(f"Location: {job['location']}\n")
        print(f"Category: {job['category']}\n")
        print(f"Apply Link: {job['apply_link']}\n")
        print(f"URL: {job['url']}\n")
        print(f"Role Summary: {job['role_summary']}\n")
        print(f"Responsibilities: {job['responsibilities']}\n")
        print(f"Qualifications: {job['qualifications']}\n")
        
if __name__ == "__main__":
    main()