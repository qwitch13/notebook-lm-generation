#!/usr/bin/env python3
"""
Debug script to inspect NotebookLM page elements.
Uses undetected-chromedriver to bypass Google's bot detection.

Usage:
    cd /Users/qwitch13/IdeaProjects/notebook-lm-generation
    source venv/bin/activate
    python3 debug_selectors.py
"""

import time
import sys
from pathlib import Path

# Use undetected-chromedriver to bypass Google's bot detection
try:
    import undetected_chromedriver as uc
    print("✅ Using undetected-chromedriver (bypasses Google bot detection)")
except ImportError:
    print("❌ undetected-chromedriver not installed!")
    print("   Run: pip install undetected-chromedriver")
    sys.exit(1)

from selenium.webdriver.common.by import By

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"

def main():
    print("\n🔍 NotebookLM Selector Debug Tool")
    print("=" * 60)
    
    # Create undetected Chrome driver with more robust options
    print("\nCreating undetected Chrome driver...")
    print("(This bypasses Google's 'browser not secure' detection)\n")
    
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun")
        options.add_argument("--password-store=basic")
        
        # Create driver with explicit version
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,  # More stable
        )
        
        # Give browser time to fully initialize
        time.sleep(3)
        
        print("✅ Driver created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create driver: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure Chrome is installed and up to date")
        print("  2. Close all Chrome windows and try again")
        print("  3. Try: pip install --upgrade undetected-chromedriver selenium")
        return
    
    try:
        print(f"\n📍 Navigating to: {NOTEBOOK_URL}")
        driver.get(NOTEBOOK_URL)
        
        print("\n" + "=" * 60)
        print("⏳ WAITING FOR LOGIN")
        print("=" * 60)
        print("\n👉 Please log into your Google account in the browser window.")
        print("   You have 2 minutes to complete login.")
        print("   The script will continue automatically once you reach the notebook.\n")
        
        # Wait for login - check every 3 seconds for up to 2 minutes
        max_wait = 120
        start_time = time.time()
        logged_in = False
        
        while time.time() - start_time < max_wait:
            try:
                current_url = driver.current_url
                
                # Check if we made it to the notebook
                if "notebooklm.google.com/notebook" in current_url:
                    print("\n✅ Successfully reached the notebook!")
                    logged_in = True
                    break
                
                # Check if still on login/signin page
                if "accounts.google.com" in current_url:
                    elapsed = int(time.time() - start_time)
                    print(f"   ⏳ Waiting for login... ({elapsed}s / {max_wait}s)", end="\r")
            except Exception as e:
                print(f"\n⚠️ Error checking URL: {e}")
                break
            
            time.sleep(3)
        
        if not logged_in:
            print("\n\n❌ Login timeout or error! Could not reach the notebook.")
            try:
                print(f"   Current URL: {driver.current_url}")
            except:
                pass
            return
        
        # Give the notebook page time to fully load
        print("\n⏳ Waiting 10 seconds for notebook to fully load...")
        time.sleep(10)
        
        run_analysis(driver)
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nPress Enter to close the browser...")
        input()
        if driver:
            try:
                driver.quit()
            except:
                pass

def run_analysis(driver):
    """Analyze the page elements."""
    
    print("\n" + "=" * 60)
    print("📋 PAGE INFO")
    print("=" * 60)
    print(f"URL: {driver.current_url}")
    print(f"Title: {driver.title}")
    
    # Take screenshot
    screenshot_path = Path.home() / "notebooklm_debug_screenshot.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"📸 Screenshot saved: {screenshot_path}")
    
    print("\n" + "=" * 60)
    print("🔘 ALL BUTTONS")
    print("=" * 60)
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"Found {len(buttons)} buttons\n")
    
    button_info = []
    for i, btn in enumerate(buttons):
        try:
            text = btn.text.replace('\n', ' ').strip()[:60] if btn.text else ""
            aria = btn.get_attribute("aria-label") or ""
            classes = btn.get_attribute("class") or ""
            data_testid = btn.get_attribute("data-testid") or btn.get_attribute("data-test-id") or ""
            visible = btn.is_displayed()
            
            # Only show buttons with some identifying info
            if text or aria or data_testid:
                info = {
                    "index": i,
                    "text": text,
                    "aria": aria,
                    "testid": data_testid,
                    "class": classes[:80],
                    "visible": visible
                }
                button_info.append(info)
                
                vis_marker = "👁" if visible else "🚫"
                print(f"{vis_marker} Button {i}:")
                if text:
                    print(f"    text: '{text}'")
                if aria:
                    print(f"    aria-label: '{aria}'")
                if data_testid:
                    print(f"    data-testid: '{data_testid}'")
                print(f"    class: '{classes[:80]}...'")
                print()
        except Exception as e:
            pass
    
    print("\n" + "=" * 60)
    print("📝 ALL TEXTAREAS & INPUT FIELDS")
    print("=" * 60)
    
    # Textareas
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    print(f"Found {len(textareas)} textareas")
    
    for i, ta in enumerate(textareas):
        try:
            placeholder = ta.get_attribute("placeholder") or "(none)"
            aria = ta.get_attribute("aria-label") or "(none)"
            classes = ta.get_attribute("class") or "(none)"
            visible = "👁 visible" if ta.is_displayed() else "🚫 hidden"
            
            print(f"\nTextarea {i}: {visible}")
            print(f"    placeholder: '{placeholder}'")
            print(f"    aria-label: '{aria}'")
            print(f"    class: '{classes}'")
        except Exception as e:
            print(f"Textarea {i}: Error - {e}")
    
    # Input fields
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"\nFound {len(inputs)} input fields")
    
    for i, inp in enumerate(inputs):
        try:
            inp_type = inp.get_attribute("type") or "text"
            placeholder = inp.get_attribute("placeholder") or ""
            aria = inp.get_attribute("aria-label") or ""
            visible = inp.is_displayed()
            
            if visible and (placeholder or aria):
                print(f"\nInput {i}: type='{inp_type}'")
                if placeholder:
                    print(f"    placeholder: '{placeholder}'")
                if aria:
                    print(f"    aria-label: '{aria}'")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("✏️ CONTENTEDITABLE ELEMENTS")
    print("=" * 60)
    editables = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
    print(f"Found {len(editables)} contenteditable elements")
    
    for i, elem in enumerate(editables):
        try:
            tag = elem.tag_name
            classes = elem.get_attribute("class") or "(none)"
            aria = elem.get_attribute("aria-label") or "(none)"
            visible = "👁 visible" if elem.is_displayed() else "🚫 hidden"
            role = elem.get_attribute("role") or "(none)"
            
            print(f"\nEditable {i}: <{tag}> {visible}")
            print(f"    role: '{role}'")
            print(f"    class: '{classes}'")
            print(f"    aria-label: '{aria}'")
        except Exception as e:
            print(f"Editable {i}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("🏷️ MATERIAL DESIGN TABS (mdc-tab)")
    print("=" * 60)
    tabs = driver.find_elements(By.CSS_SELECTOR, ".mdc-tab")
    print(f"Found {len(tabs)} Material Design tabs")
    
    for i, tab in enumerate(tabs):
        try:
            text = tab.text.replace('\n', ' ').strip()
            aria = tab.get_attribute("aria-label") or ""
            selected = tab.get_attribute("aria-selected") or "false"
            visible = "👁 visible" if tab.is_displayed() else "🚫 hidden"
            tab_id = tab.get_attribute("id") or ""
            
            print(f"\nTab {i}: {visible}")
            print(f"    id: '{tab_id}'")
            print(f"    text: '{text}'")
            print(f"    aria-label: '{aria}'")
            print(f"    selected: {selected}")
        except Exception as e:
            print(f"Tab {i}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("🔍 SEARCHING FOR KEY ELEMENTS BY TEXT")
    print("=" * 60)
    
    # Search for Audio (German: Audio-Zusammenfassung)
    print("\n🎵 Elements containing 'Audio':")
    audio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Audio')]")
    for elem in audio_elements[:10]:
        try:
            tag = elem.tag_name
            text = elem.text[:60].replace('\n', ' ')
            visible = "👁" if elem.is_displayed() else "🚫"
            print(f"  {visible} <{tag}>: '{text}'")
        except:
            pass
    
    # Search for Studio
    print("\n🎬 Elements containing 'Studio':")
    studio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Studio')]")
    for elem in studio_elements[:10]:
        try:
            tag = elem.tag_name
            text = elem.text[:60].replace('\n', ' ')
            visible = "👁" if elem.is_displayed() else "🚫"
            print(f"  {visible} <{tag}>: '{text}'")
        except:
            pass
    
    # Search for Chat
    print("\n💬 Elements containing 'Chat':")
    chat_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Chat')]")
    for elem in chat_elements[:10]:
        try:
            tag = elem.tag_name
            text = elem.text[:60].replace('\n', ' ')
            visible = "👁" if elem.is_displayed() else "🚫"
            print(f"  {visible} <{tag}>: '{text}'")
        except:
            pass
    
    # Search for edit icons/buttons
    print("\n✏️ Elements containing 'edit':")
    edit_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'edit')]")
    for elem in edit_elements[:15]:
        try:
            tag = elem.tag_name
            text = elem.text[:40].replace('\n', ' ')
            visible = "👁" if elem.is_displayed() else "🚫"
            parent_tag = elem.find_element(By.XPATH, "..").tag_name if elem else ""
            print(f"  {visible} <{tag}> (parent: <{parent_tag}>): '{text}'")
        except:
            pass
    
    # Search for mat-icon elements
    print("\n🎨 Material Icons (mat-icon):")
    mat_icons = driver.find_elements(By.TAG_NAME, "mat-icon")
    for i, icon in enumerate(mat_icons[:20]):
        try:
            text = icon.text.strip()
            visible = "👁" if icon.is_displayed() else "🚫"
            if text and visible == "👁":
                print(f"  {visible} mat-icon: '{text}'")
        except:
            pass
    
    # Save page source
    html_path = Path.home() / "notebooklm_debug_page.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"\n📄 Full page HTML saved: {html_path}")
    
    print("\n" + "=" * 60)
    print("✅ Debug complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
