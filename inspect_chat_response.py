#!/usr/bin/env python3
"""
Inspect the chat response structure in NotebookLM.
Run this AFTER sending a chat message while the browser is still open.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.auth.google_auth import GoogleAuthenticator
from selenium.webdriver.common.by import By


def inspect_chat_elements():
    """Inspect the page to find chat response elements."""
    print("🔍 Connecting to existing browser session...")
    
    auth = GoogleAuthenticator()
    driver = auth.get_driver()
    
    if not driver:
        print("❌ No browser session found")
        return
    
    print(f"📍 Current URL: {driver.current_url}")
    print(f"📄 Page title: {driver.title}")
    
    # Look for elements that might contain the AI response
    print("\n" + "="*60)
    print("🔍 SEARCHING FOR POTENTIAL RESPONSE CONTAINERS")
    print("="*60)
    
    # Common patterns for AI responses in chat UIs
    search_patterns = [
        # Markdown/prose containers
        ("markdown classes", "//div[contains(@class, 'markdown')]"),
        ("prose classes", "//div[contains(@class, 'prose')]"),
        ("rendered content", "//div[contains(@class, 'rendered')]"),
        
        # Response-specific
        ("response class", "//div[contains(@class, 'response')]"),
        ("answer class", "//div[contains(@class, 'answer')]"),
        ("reply class", "//div[contains(@class, 'reply')]"),
        ("output class", "//div[contains(@class, 'output')]"),
        
        # Chat message containers
        ("assistant message", "//div[contains(@class, 'assistant')]"),
        ("bot message", "//div[contains(@class, 'bot')]"),
        ("ai message", "//div[contains(@class, 'ai')]"),
        ("model message", "//div[@data-message-author-role='model']"),
        
        # Material design patterns (Google uses this)
        ("mat-card", "//mat-card"),
        ("mdc-card", "//div[contains(@class, 'mdc-card')]"),
        
        # Generic content divs with substantial text
        ("content div", "//div[contains(@class, 'content')]"),
        ("text div", "//div[contains(@class, 'text')]"),
        ("body div", "//div[contains(@class, 'body')]"),
        
        # Aria roles
        ("article role", "//*[@role='article']"),
        ("region role", "//*[@role='region']"),
        ("main role", "//*[@role='main']"),
        
        # Chat-specific containers
        ("chat panel", "//div[contains(@class, 'chat')]//div[contains(@class, 'panel')]"),
        ("chat content", "//div[contains(@class, 'chat')]//div[contains(@class, 'content')]"),
        ("message list", "//div[contains(@class, 'message-list')]"),
        ("messages container", "//div[contains(@class, 'messages')]"),
    ]
    
    found_candidates = []
    
    for name, xpath in search_patterns:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            visible_elements = [e for e in elements if e.is_displayed()]
            
            if visible_elements:
                for i, elem in enumerate(visible_elements[:3]):  # Max 3 per pattern
                    text = elem.text.strip()
                    text_len = len(text)
                    
                    # We're looking for substantial text (100+ chars) that looks like a response
                    if text_len >= 100:
                        # Get class and other attributes
                        class_attr = elem.get_attribute("class") or ""
                        data_attrs = {k: v for k, v in elem.get_property('attributes') 
                                      if k.startswith('data-')} if hasattr(elem, 'get_property') else {}
                        
                        preview = text[:150].replace('\n', ' ')
                        found_candidates.append({
                            'name': name,
                            'xpath': xpath,
                            'class': class_attr[:80],
                            'length': text_len,
                            'preview': preview
                        })
                        print(f"\n✅ {name} [{text_len} chars]")
                        print(f"   Class: {class_attr[:80]}")
                        print(f"   Preview: {preview}...")
                        
        except Exception as e:
            pass
    
    if not found_candidates:
        print("\n⚠️ No substantial text elements found with common patterns")
        print("   Let's dump ALL divs with 100+ chars of text...")
        
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        print(f"\n   Total divs on page: {len(all_divs)}")
        
        for i, div in enumerate(all_divs):
            try:
                if div.is_displayed():
                    text = div.text.strip()
                    if 100 <= len(text) <= 5000:  # Reasonable response length
                        class_attr = div.get_attribute("class") or "(no class)"
                        id_attr = div.get_attribute("id") or "(no id)"
                        
                        # Skip obvious UI elements
                        skip_keywords = ["sidebar", "nav", "menu", "header", "footer", "toolbar", "button", "modal"]
                        if any(kw in class_attr.lower() for kw in skip_keywords):
                            continue
                        
                        preview = text[:150].replace('\n', ' ')
                        print(f"\n📝 DIV #{i} [{len(text)} chars]")
                        print(f"   Class: {class_attr[:80]}")
                        print(f"   ID: {id_attr}")
                        print(f"   Preview: {preview}...")
                        
            except:
                pass
    
    # Also specifically look for the chat input area to understand the structure
    print("\n" + "="*60)
    print("🔍 CHAT INPUT CONTEXT (to understand structure)")
    print("="*60)
    
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    for ta in textareas:
        if ta.is_displayed():
            placeholder = ta.get_attribute("placeholder") or "(no placeholder)"
            parent = ta.find_element(By.XPATH, "..")
            parent_class = parent.get_attribute("class") or "(no class)"
            grandparent = parent.find_element(By.XPATH, "..")
            gp_class = grandparent.get_attribute("class") or "(no class)"
            
            print(f"\n   Textarea: '{placeholder[:40]}'")
            print(f"   Parent class: {parent_class[:60]}")
            print(f"   Grandparent class: {gp_class[:60]}")
    
    # Save page source for manual inspection
    print("\n" + "="*60)
    print("💾 SAVING PAGE SOURCE")
    print("="*60)
    
    output_path = Path.home() / "notebooklm_chat_page.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"   Saved to: {output_path}")
    print("   Open this file in a browser and use DevTools to inspect the chat response structure")
    

if __name__ == "__main__":
    inspect_chat_elements()
