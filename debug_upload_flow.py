#!/usr/bin/env python3
"""Debug the exact upload flow step by step."""

import time
import sys
import os

# Add project root to path
project_root = '/Users/qwitch13/IdeaProjects/notebook-lm-generation'
sys.path.insert(0, project_root)
os.chdir(project_root)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def main():
    print("🔍 Debug: Upload Flow Step by Step")
    print("=" * 70)
    
    # Setup Chrome with persistent profile
    options = Options()
    profile_dir = os.path.expanduser("~/.nlm_chrome_profile")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Navigate to NotebookLM
        print("\n1️⃣ Navigating to NotebookLM...")
        driver.get("https://notebooklm.google.com/")
        time.sleep(3)
        print(f"   URL: {driver.current_url}")
        
        # Find and click create button
        print("\n2️⃣ Creating new notebook...")
        try:
            create_btn = driver.find_element(By.XPATH, "//button[@aria-label='Neues Notebook erstellen']")
            print(f"   Found create button")
            create_btn.click()
            time.sleep(3)
            print(f"   New URL: {driver.current_url}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            input("Press Enter...")
            return
        
        # Dismiss any welcome dialog
        print("\n3️⃣ Dismissing welcome dialog if present...")
        try:
            dismiss_texts = ['Verstanden', 'Got it', 'OK', 'Schließen', 'Close']
            for text in dismiss_texts:
                try:
                    btn = driver.find_element(By.XPATH, f"//button[contains(., '{text}')]")
                    if btn.is_displayed():
                        btn.click()
                        print(f"   Clicked '{text}'")
                        time.sleep(1)
                        break
                except:
                    pass
        except:
            print("   No welcome dialog found")
        
        # Look for add source button
        print("\n4️⃣ Looking for 'Quellen hinzufügen' button...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Total buttons: {len(buttons)}")
        
        add_btn = None
        for i, btn in enumerate(buttons):
            try:
                text = btn.text.replace('\n', ' ')[:50]
                aria = btn.get_attribute('aria-label') or ''
                if 'quelle' in text.lower() or 'quelle' in aria.lower() or 'source' in text.lower():
                    visible = btn.is_displayed()
                    print(f"   [{i}] '{text}' | aria='{aria}' | visible={visible}")
                    if 'hinzufügen' in text.lower() or aria == 'Quelle hinzufügen':
                        add_btn = btn
            except:
                pass
        
        if not add_btn:
            print("   ❌ Could not find add source button!")
            input("Press Enter...")
            return
        
        # Click add source button
        print(f"\n5️⃣ Clicking add source button...")
        add_btn.click()
        time.sleep(2)
        print("   ✅ Clicked!")
        
        # Check what buttons are visible now
        print("\n6️⃣ Checking for upload-related buttons AFTER clicking add source...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        upload_btn = None
        
        for i, btn in enumerate(buttons):
            try:
                text = btn.text.replace('\n', ' ')[:50].lower()
                aria = (btn.get_attribute('aria-label') or '').lower()
                keywords = ['upload', 'hochladen', 'datei', 'file', 'öffnet']
                if any(kw in text or kw in aria for kw in keywords):
                    visible = btn.is_displayed()
                    print(f"   [{i}] '{btn.text[:40]}' | aria='{btn.get_attribute('aria-label')}' | visible={visible}")
                    if visible and 'hochladen' in text:
                        upload_btn = btn
            except:
                pass
        
        # Check for file inputs
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        print(f"\n   File inputs found: {len(file_inputs)}")
        
        # Click upload button if found
        if upload_btn:
            print(f"\n7️⃣ Clicking upload button...")
            upload_btn.click()
            time.sleep(2)
            print("   ✅ Clicked!")
            
            # Check for file inputs again
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            print(f"\n   File inputs AFTER upload click: {len(file_inputs)}")
            for i, inp in enumerate(file_inputs):
                accept = inp.get_attribute('accept')
                visible = inp.is_displayed()
                print(f"   [{i}] accept='{accept}' visible={visible}")
        
        # Look for "Datei auswählen" link
        print("\n8️⃣ Looking for 'Datei auswählen' clickable element...")
        try:
            # Try span first
            select_elem = driver.find_element(By.XPATH, "//span[contains(text(), 'Datei auswählen')]")
            print(f"   Found span: '{select_elem.text}'")
            select_elem.click()
            time.sleep(2)
            print("   ✅ Clicked!")
        except Exception as e:
            print(f"   Span not found: {e}")
            try:
                # Try any element
                select_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'Datei auswählen')]")
                print(f"   Found element: {select_elem.tag_name} '{select_elem.text}'")
                select_elem.click()
                time.sleep(2)
                print("   ✅ Clicked!")
            except Exception as e2:
                print(f"   ❌ Element not found: {e2}")
        
        # Final check for file inputs
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        print(f"\n9️⃣ Final file input check: {len(file_inputs)}")
        for i, inp in enumerate(file_inputs):
            accept = inp.get_attribute('accept')
            visible = inp.is_displayed()
            print(f"   [{i}] accept='{accept}' visible={visible}")
            
            # Try sending a file
            if not visible:
                print("   📁 Trying to send file to hidden input...")
                test_file = "/Users/qwitch13/Documents/study/Enchanted_Networking_Protocols_AND_Layers_Study_Guide.pdf"
                try:
                    inp.send_keys(test_file)
                    print("   ✅ File sent!")
                    time.sleep(3)
                except Exception as e:
                    print(f"   ❌ Send failed: {e}")
        
        # Save screenshot
        driver.save_screenshot(f"{project_root}/debug_upload_screenshot.png")
        print("\n📸 Screenshot saved")
        
        input("\n Press Enter to close browser...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
