#!/usr/bin/env python3
"""
Direct test of NotebookLM audio generation.
This script tests the exact workflow without the main CLI wrapper.
"""
import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"
PROFILE_DIR = Path.home() / ".nlm_chrome_profile"

def create_driver():
    """Create Chrome driver with persistent profile."""
    print(f"📁 Using Chrome profile: {PROFILE_DIR}")
    PROFILE_DIR.mkdir(exist_ok=True)
    
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--window-size=1400,900")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def wait_for_login(driver, timeout=180):
    """Wait for user to be logged in."""
    print("\n⏳ Checking if logged in...")
    start = time.time()
    while time.time() - start < timeout:
        url = driver.current_url
        # Check if we're on a notebook page or NotebookLM home
        if "notebooklm.google.com/notebook/" in url:
            print(f"✅ On notebook page: {url}")
            return True
        if "notebooklm.google.com" in url and "accounts.google" not in url:
            print(f"✅ On NotebookLM: {url}")
            return True
        print(f"   Waiting... Current URL: {url[:60]}...")
        time.sleep(5)
    return False

def click_element_safe(driver, element):
    """Click element using multiple methods."""
    try:
        element.click()
        return True
    except:
        pass
    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except:
        pass
    return False

def find_and_click_text(driver, text, timeout=10):
    """Find element containing text and click it."""
    xpaths = [
        f"//*[contains(text(), '{text}')]",
        f"//button[contains(., '{text}')]",
        f"//div[contains(@class, 'mdc-tab')][contains(., '{text}')]",
        f"//span[contains(., '{text}')]/parent::*",
    ]
    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed():
                    print(f"   Found '{text}' with: {xpath[:50]}")
                    click_element_safe(driver, elem)
                    return True
        except Exception as e:
            continue
    return False

def test_audio_generation(driver):
    """Test clicking on Audio Overview to generate."""
    print("\n" + "=" * 60)
    print("🎵 Testing Audio Generation")
    print("=" * 60)
    
    # Step 1: Click Studio tab
    print("\n1️⃣ Looking for Studio tab...")
    if find_and_click_text(driver, "Studio"):
        print("   ✅ Clicked Studio tab")
    else:
        print("   ⚠️ Could not find Studio tab")
    
    time.sleep(2)
    
    # Step 2: Look for Audio-Zusammenfassung
    print("\n2️⃣ Looking for Audio-Zusammenfassung...")
    audio_texts = ["Audio-Zusammenfassung", "Audio Overview", "Audio"]
    found = False
    for text in audio_texts:
        # First find the text element
        try:
            elems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
            for elem in elems:
                if elem.is_displayed() and text.lower() in elem.text.lower():
                    print(f"   Found: '{elem.text[:40]}...'")
                    # Look for edit icon nearby
                    parent = elem
                    for _ in range(5):  # Go up to 5 levels
                        try:
                            parent = parent.find_element(By.XPATH, "..")
                            edit_icons = parent.find_elements(By.XPATH, ".//mat-icon[contains(text(), 'edit')]")
                            if edit_icons:
                                print(f"   Found edit icon near '{text}'")
                                click_element_safe(driver, edit_icons[0])
                                found = True
                                break
                        except:
                            break
                    if found:
                        break
            if found:
                break
        except Exception as e:
            print(f"   Error: {e}")
    
    if not found:
        print("   ⚠️ Could not find Audio item with edit button")
        print("   Let's look for any 'edit' icons...")
        try:
            edit_icons = driver.find_elements(By.XPATH, "//mat-icon[contains(text(), 'edit')]")
            print(f"   Found {len(edit_icons)} edit icons total")
            for i, icon in enumerate(edit_icons[:6]):
                if icon.is_displayed():
                    parent_text = ""
                    try:
                        parent = icon.find_element(By.XPATH, "..")
                        parent_text = parent.text[:30] if parent.text else "no text"
                    except:
                        pass
                    print(f"   Edit icon {i}: near '{parent_text}'")
        except:
            pass
    
    time.sleep(3)
    
    # Step 3: Look for Generate button in dialog
    print("\n3️⃣ Looking for Generate/Erstellen button...")
    gen_texts = ["Erstellen", "Generate", "Create", "Start"]
    for text in gen_texts:
        if find_and_click_text(driver, text):
            print(f"   ✅ Clicked '{text}' button")
            return True
    
    print("   ⚠️ No generate button found")
    return False

def test_chat(driver, message="Was sind die wichtigsten Themen?"):
    """Test sending a chat message."""
    print("\n" + "=" * 60)
    print("💬 Testing Chat")
    print("=" * 60)
    
    # Step 1: Click Chat tab
    print("\n1️⃣ Looking for Chat tab...")
    if find_and_click_text(driver, "Chat"):
        print("   ✅ Clicked Chat tab")
    else:
        print("   ⚠️ Could not find Chat tab")
    
    time.sleep(2)
    
    # Step 2: Find the correct textarea (NOT the research one)
    print("\n2️⃣ Looking for chat input...")
    print("   (Need to find the chat textarea, NOT research box)")
    
    # List all textareas and their context
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    print(f"   Found {len(textareas)} textareas total")
    
    chat_textarea = None
    for i, ta in enumerate(textareas):
        if ta.is_displayed():
            placeholder = ta.get_attribute("placeholder") or "no placeholder"
            aria = ta.get_attribute("aria-label") or "no aria"
            parent_text = ""
            try:
                parent = ta.find_element(By.XPATH, "./ancestor::*[3]")
                parent_text = parent.text[:30].replace('\n', ' ') if parent.text else ""
            except:
                pass
            print(f"   Textarea {i}: placeholder='{placeholder[:30]}', aria='{aria[:30]}', context='{parent_text}'")
            
            # Try to identify the chat textarea (not research)
            # Chat input usually has placeholder like "Stelle eine Frage" or "Ask a question"
            if any(x in placeholder.lower() for x in ["frage", "ask", "type", "eingabe"]):
                if "research" not in placeholder.lower() and "deep" not in placeholder.lower():
                    chat_textarea = ta
                    print(f"   ✅ This looks like the chat input!")
    
    if not chat_textarea and textareas:
        # Just use the last visible one as fallback
        for ta in reversed(textareas):
            if ta.is_displayed():
                chat_textarea = ta
                print(f"   Using last visible textarea as fallback")
                break
    
    if not chat_textarea:
        print("   ❌ No chat textarea found!")
        return False
    
    # Step 3: Type message
    print(f"\n3️⃣ Typing message: {message[:40]}...")
    try:
        chat_textarea.clear()
    except:
        pass
    chat_textarea.send_keys(message)
    print("   ✅ Message typed")
    
    time.sleep(1)
    
    # Step 4: Send (Enter or button)
    print("\n4️⃣ Sending message...")
    # Try to find send button
    send_found = False
    for btn_text in ["send", "Senden", "arrow_upward"]:
        try:
            btn = driver.find_element(By.XPATH, f"//button[contains(., '{btn_text}')] | //mat-icon[contains(text(), '{btn_text}')]")
            if btn.is_displayed():
                click_element_safe(driver, btn)
                send_found = True
                print(f"   ✅ Clicked send button")
                break
        except:
            pass
    
    if not send_found:
        print("   Pressing Enter to send...")
        chat_textarea.send_keys(Keys.RETURN)
    
    print("\n⏳ Waiting for response (30s)...")
    time.sleep(30)
    
    return True

def main():
    print("🔬 NotebookLM Direct Test")
    print("=" * 60)
    
    driver = create_driver()
    
    try:
        # Navigate to notebook
        print(f"\n📍 Navigating to: {NOTEBOOK_URL}")
        driver.get(NOTEBOOK_URL)
        
        # Wait for login
        if not wait_for_login(driver):
            print("❌ Login timeout!")
            input("Press Enter to close...")
            return
        
        # Wait for page to fully load
        print("\n⏳ Waiting for notebook to load...")
        time.sleep(8)
        
        # Show current page info
        print(f"\n📄 Current URL: {driver.current_url}")
        print(f"📄 Title: {driver.title}")
        
        # Check if we're actually inside the notebook
        if "/notebook/" not in driver.current_url:
            print("\n⚠️ WARNING: Not inside a notebook!")
            print("   The URL should contain '/notebook/' but current URL is:")
            print(f"   {driver.current_url}")
        
        # Menu
        while True:
            print("\n" + "=" * 60)
            print("Choose test:")
            print("  1. Test Audio Generation")
            print("  2. Test Chat")
            print("  3. Show page info")
            print("  4. Take screenshot")
            print("  q. Quit")
            choice = input("\nChoice: ").strip().lower()
            
            if choice == "1":
                test_audio_generation(driver)
            elif choice == "2":
                test_chat(driver)
            elif choice == "3":
                print(f"\nURL: {driver.current_url}")
                print(f"Title: {driver.title}")
                body = driver.find_element(By.TAG_NAME, "body")
                text = body.text[:500].replace('\n', ' | ')
                print(f"Body text: {text}...")
            elif choice == "4":
                path = Path.home() / "nlm_test_screenshot.png"
                driver.save_screenshot(str(path))
                print(f"Saved: {path}")
            elif choice == "q":
                break
            else:
                print("Invalid choice")
        
    finally:
        print("\n👋 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    main()
