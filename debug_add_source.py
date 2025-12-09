#!/usr/bin/env python3
"""Debug script to understand the NotebookLM add source flow."""

import sys
import time
sys.path.insert(0, '/Users/qwitch13/IdeaProjects/notebook-lm-generation')

from selenium.webdriver.common.by import By
from src.auth.google_auth import GoogleAuthenticator

def main():
    print("🔍 Debug: Add Source Flow")
    print("=" * 60)
    
    auth = GoogleAuthenticator()
    driver = auth.get_driver()
    
    if not driver:
        print("❌ Failed to get driver")
        return
    
    # Navigate to NotebookLM
    print("\n1️⃣ Navigating to NotebookLM...")
    driver.get("https://notebooklm.google.com/")
    time.sleep(5)
    
    print(f"   Current URL: {driver.current_url}")
    
    # Check if we need to log in
    if "accounts.google.com" in driver.current_url:
        print("\n⚠️  LOGIN REQUIRED - Please log in manually")
        print("   Waiting up to 2 minutes...")
        for i in range(60):
            time.sleep(2)
            if "notebooklm.google.com" in driver.current_url:
                break
        time.sleep(3)
    
    print(f"   After login URL: {driver.current_url}")
    
    # Create a new notebook
    print("\n2️⃣ Looking for create notebook button...")
    
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"   Found {len(buttons)} buttons:")
    for i, b in enumerate(buttons[:15]):
        try:
            text = b.text.replace('\n', ' ')[:40] if b.text else "(no text)"
            aria = b.get_attribute("aria-label") or ""
            visible = "✓" if b.is_displayed() else "✗"
            print(f"   [{visible}] {i}: text='{text}' aria='{aria[:30]}'")
        except:
            pass
    
    # Try to click create button
    create_btn = None
    for b in buttons:
        try:
            if b.is_displayed():
                text = (b.text or "").lower()
                aria = (b.get_attribute("aria-label") or "").lower()
                if "erstellen" in text or "create" in text or "new" in aria:
                    create_btn = b
                    break
        except:
            pass
    
    if create_btn:
        print(f"\n3️⃣ Clicking create button: '{create_btn.text}'")
        driver.execute_script("arguments[0].click();", create_btn)
        time.sleep(5)
        print(f"   New URL: {driver.current_url}")
    else:
        print("   ❌ Could not find create button")
        return
    
    # Now we're on the new notebook page
    print("\n4️⃣ Analyzing new notebook page...")
    print(f"   URL: {driver.current_url}")
    print(f"   Title: {driver.title}")
    
    # Dump all buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\n   Buttons on page ({len(buttons)}):")
    for i, b in enumerate(buttons[:20]):
        try:
            text = b.text.replace('\n', ' ')[:50] if b.text else "(no text)"
            aria = b.get_attribute("aria-label") or ""
            visible = "✓" if b.is_displayed() else "✗"
            classes = b.get_attribute("class") or ""
            print(f"   [{visible}] {i}: '{text}' | aria='{aria[:25]}' | class='{classes[:30]}'")
        except:
            pass
    
    # Look for file inputs
    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    print(f"\n   File inputs: {len(file_inputs)}")
    for i, fi in enumerate(file_inputs):
        print(f"   {i}: accept='{fi.get_attribute('accept')}' visible={fi.is_displayed()}")
    
    # Look for text containing "Quelle" or "source"
    print("\n   Looking for source-related text...")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    lines = body_text.split('\n')
    for line in lines:
        if 'quelle' in line.lower() or 'source' in line.lower() or 'upload' in line.lower() or 'hochladen' in line.lower():
            print(f"   → '{line[:60]}'")
    
    # Look for dialogs/overlays
    print("\n   Looking for dialogs/modals...")
    dialogs = driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], .mdc-dialog, .mat-dialog-container")
    print(f"   Found {len(dialogs)} dialog elements")
    for i, d in enumerate(dialogs):
        visible = "✓" if d.is_displayed() else "✗"
        print(f"   [{visible}] Dialog {i}")
    
    # Look for mat-icons
    print("\n   mat-icons on page:")
    icons = driver.find_elements(By.TAG_NAME, "mat-icon")
    icon_texts = set()
    for icon in icons[:30]:
        try:
            if icon.text:
                icon_texts.add(icon.text)
        except:
            pass
    print(f"   Icons: {sorted(icon_texts)}")
    
    # Try clicking various things to find the upload flow
    print("\n5️⃣ Trying to find add source flow...")
    
    # Look for links or clickable elements with source text
    clickables = driver.find_elements(By.XPATH, "//*[contains(text(), 'Quelle') or contains(text(), 'Source') or contains(text(), 'hinzufügen') or contains(text(), 'Add')]")
    print(f"   Found {len(clickables)} elements with source/add text:")
    for i, c in enumerate(clickables[:10]):
        try:
            tag = c.tag_name
            text = c.text.replace('\n', ' ')[:40] if c.text else ""
            visible = "✓" if c.is_displayed() else "✗"
            print(f"   [{visible}] {tag}: '{text}'")
        except:
            pass
    
    # Take screenshot
    screenshot_path = "/Users/qwitch13/IdeaProjects/notebook-lm-generation/debug_screenshot.png"
    driver.save_screenshot(screenshot_path)
    print(f"\n📸 Screenshot saved: {screenshot_path}")
    
    # Save HTML
    html_path = "/Users/qwitch13/IdeaProjects/notebook-lm-generation/debug_page.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"📄 HTML saved: {html_path}")
    
    print("\n" + "=" * 60)
    print("Press Enter to close browser...")
    input()
    
    auth.close()

if __name__ == "__main__":
    main()
