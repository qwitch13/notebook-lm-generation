#!/usr/bin/env python3
"""
Inspect NotebookLM chat page to find the correct response selector.
"""
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"
PROFILE_DIR = Path.home() / ".nlm_chrome_profile"

def create_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--window-size=1400,900")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def main():
    print("🔬 NotebookLM Chat Inspector")
    print("=" * 60)
    
    driver = create_driver()
    
    try:
        print(f"\n📍 Navigating to: {NOTEBOOK_URL}")
        driver.get(NOTEBOOK_URL)
        
        print("\n⏳ Waiting for page to load...")
        time.sleep(10)
        
        # Click Chat tab
        print("\n1️⃣ Clicking Chat tab...")
        chat_elems = driver.find_elements(By.XPATH, "//*[contains(text(), 'Chat')]")
        for elem in chat_elems:
            if elem.is_displayed():
                elem.click()
                break
        time.sleep(3)
        
        # Find chat input
        print("\n2️⃣ Finding chat input...")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        chat_input = None
        for ta in textareas:
            if ta.is_displayed():
                ph = (ta.get_attribute("placeholder") or "").lower()
                if "eingeben" in ph or "text" in ph:
                    chat_input = ta
                    print(f"   Found: '{ph}'")
                    break
        
        if not chat_input:
            print("   No chat input found!")
            return
        
        # Send message
        print("\n3️⃣ Sending test message...")
        chat_input.send_keys("Was sind die wichtigsten Themen?")
        time.sleep(0.5)
        
        # Press Enter
        chat_input.send_keys(Keys.RETURN)
        print("   Message sent!")
        
        # Wait for response
        print("\n4️⃣ Waiting 20 seconds for AI response...")
        time.sleep(20)
        
        # Now inspect the page to find the response
        print("\n" + "=" * 60)
        print("📋 ANALYZING PAGE STRUCTURE")
        print("=" * 60)
        
        # Get body text
        body = driver.find_element(By.TAG_NAME, "body")
        body_text = body.text
        
        # Find all divs with substantial text (potential response containers)
        print("\n🔍 Looking for elements with >100 chars text...")
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        candidates = []
        for div in all_divs:
            try:
                if div.is_displayed():
                    text = div.text
                    if text and len(text) > 100 and len(text) < 5000:
                        # Get class names
                        classes = div.get_attribute("class") or "no-class"
                        # Get first 100 chars of text
                        preview = text[:100].replace('\n', ' ')
                        candidates.append({
                            'classes': classes,
                            'text_len': len(text),
                            'preview': preview
                        })
            except:
                pass
        
        print(f"   Found {len(candidates)} candidate elements\n")
        
        # Sort by text length and show top 10
        candidates.sort(key=lambda x: x['text_len'])
        for i, c in enumerate(candidates[:15]):
            print(f"   {i+1}. [{c['text_len']:4d} chars] class='{c['classes'][:50]}'")
            print(f"      Preview: {c['preview'][:80]}...")
            print()
        
        # Save full HTML
        html_path = Path.home() / "nlm_chat_page.html"
        with open(html_path, 'w') as f:
            f.write(driver.page_source)
        print(f"\n📄 Saved full HTML to: {html_path}")
        
        # Save body text
        text_path = Path.home() / "nlm_chat_text.txt"
        with open(text_path, 'w') as f:
            f.write(body_text)
        print(f"📄 Saved body text to: {text_path}")
        
        input("\n\nPress Enter to close browser...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
