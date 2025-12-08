#!/usr/bin/env python3
"""
Simple test script using regular Selenium.
You'll need to log in manually, but this avoids the undetected-chromedriver issues.

Usage:
    cd /Users/qwitch13/IdeaProjects/notebook-lm-generation
    source venv/bin/activate
    python3 test_selectors_simple.py
"""

import time
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"

def main():
    print("\n🔍 NotebookLM Selector Test (Simple Selenium)")
    print("=" * 60)
    print("\n⚠️  NOTE: This uses regular Selenium, not undetected-chromedriver.")
    print("    Google may show 'browser not secure' - try logging in anyway.")
    print("    Or use a Chrome profile with saved login.\n")
    
    # Create regular Chrome driver
    print("Creating Chrome driver...")
    
    try:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Use a persistent profile to keep login
        profile_dir = Path.home() / ".nlm_chrome_profile"
        profile_dir.mkdir(exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("✅ Driver created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create driver: {e}")
        return
    
    try:
        print(f"\n📍 Navigating to: {NOTEBOOK_URL}")
        driver.get(NOTEBOOK_URL)
        
        print("\n" + "=" * 60)
        print("⏳ WAITING FOR LOGIN")
        print("=" * 60)
        print("\n👉 Please log into your Google account in the browser window.")
        print("   If you see 'browser not secure', try clicking 'Advanced' and 'Proceed'.")
        print("   You have 3 minutes to complete login.")
        print("   The script will continue automatically once you reach the notebook.\n")
        
        # Wait for login
        max_wait = 180
        start_time = time.time()
        logged_in = False
        
        while time.time() - start_time < max_wait:
            try:
                current_url = driver.current_url
                
                if "notebooklm.google.com/notebook" in current_url:
                    print("\n✅ Successfully reached the notebook!")
                    logged_in = True
                    break
                
                if "accounts.google.com" in current_url:
                    elapsed = int(time.time() - start_time)
                    print(f"   ⏳ Waiting for login... ({elapsed}s / {max_wait}s)", end="\r")
            except:
                pass
            
            time.sleep(2)
        
        if not logged_in:
            print("\n\n❌ Login timeout!")
            return
        
        # Wait for page to load
        print("\n⏳ Waiting 8 seconds for notebook to fully load...")
        time.sleep(8)
        
        run_tests(driver)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nPress Enter to close the browser...")
        input()
        driver.quit()


def run_tests(driver):
    """Test the selectors we've implemented."""
    
    print("\n" + "=" * 60)
    print("📋 PAGE INFO")
    print("=" * 60)
    print(f"URL: {driver.current_url}")
    print(f"Title: {driver.title}")
    
    # Save screenshot
    screenshot_path = Path.home() / "nlm_test_screenshot.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"📸 Screenshot: {screenshot_path}")
    
    print("\n" + "=" * 60)
    print("🧪 TESTING SELECTORS")
    print("=" * 60)
    
    # Test 1: Find Studio tab
    print("\n1️⃣ Looking for 'Studio' tab...")
    studio_xpaths = [
        "//div[contains(@class, 'mdc-tab')][contains(., 'Studio')]",
        "//*[contains(text(), 'Studio')]",
    ]
    studio_found = False
    for xpath in studio_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed():
                    print(f"   ✅ Found: {xpath[:50]}...")
                    print(f"      Text: '{elem.text[:40]}...'")
                    studio_found = True
                    break
            if studio_found:
                break
        except:
            pass
    if not studio_found:
        print("   ❌ Not found")
    
    # Test 2: Find Chat tab
    print("\n2️⃣ Looking for 'Chat' tab...")
    chat_xpaths = [
        "//div[contains(@class, 'mdc-tab')][contains(., 'Chat')]",
        "//*[contains(text(), 'Chat')]",
    ]
    chat_found = False
    for xpath in chat_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed():
                    print(f"   ✅ Found: {xpath[:50]}...")
                    print(f"      Text: '{elem.text[:40]}'")
                    chat_found = True
                    break
            if chat_found:
                break
        except:
            pass
    if not chat_found:
        print("   ❌ Not found")
    
    # Test 3: Find Audio-Zusammenfassung
    print("\n3️⃣ Looking for 'Audio-Zusammenfassung' or 'Audio Overview'...")
    audio_xpaths = [
        "//*[contains(text(), 'Audio-Zusammenfassung')]",
        "//*[contains(text(), 'Audio Overview')]",
        "//*[contains(text(), 'Audio')]",
    ]
    audio_found = False
    for xpath in audio_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed():
                    print(f"   ✅ Found: {xpath[:50]}...")
                    print(f"      Text: '{elem.text[:40]}...'")
                    audio_found = True
                    break
            if audio_found:
                break
        except:
            pass
    if not audio_found:
        print("   ❌ Not found")
    
    # Test 4: Find edit buttons
    print("\n4️⃣ Looking for edit buttons (mat-icon with 'edit')...")
    try:
        edit_icons = driver.find_elements(By.XPATH, "//mat-icon[contains(text(), 'edit')]")
        visible_count = sum(1 for e in edit_icons if e.is_displayed())
        print(f"   ✅ Found {visible_count} visible edit icons")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Find textareas
    print("\n5️⃣ Looking for textareas/inputs...")
    try:
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        visible_ta = sum(1 for t in textareas if t.is_displayed())
        visible_inp = sum(1 for i in inputs if i.is_displayed())
        print(f"   Found {visible_ta} visible textareas, {visible_inp} visible text inputs")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: List all visible mdc-tabs
    print("\n6️⃣ All visible Material Design tabs:")
    try:
        tabs = driver.find_elements(By.CSS_SELECTOR, ".mdc-tab")
        for i, tab in enumerate(tabs):
            if tab.is_displayed():
                text = tab.text.replace('\n', ' ').strip()[:30]
                selected = tab.get_attribute("aria-selected") == "true"
                marker = "👉" if selected else "  "
                print(f"   {marker} Tab {i}: '{text}' {'(selected)' if selected else ''}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: List items in Studio (if visible)
    print("\n7️⃣ Looking for Studio items (Audio, Video, Quiz, etc.)...")
    studio_items = [
        "Audio-Zusammenfassung",
        "Videoübersicht",
        "Mindmap",
        "Karteikarten",
        "Quiz",
        "Infografik",
        "Präsentation",
    ]
    for item in studio_items:
        try:
            elem = driver.find_element(By.XPATH, f"//*[contains(text(), '{item}')]")
            if elem.is_displayed():
                print(f"   ✅ {item}")
            else:
                print(f"   🚫 {item} (hidden)")
        except:
            print(f"   ❌ {item} (not found)")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
