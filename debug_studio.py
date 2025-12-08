#!/usr/bin/env python3
"""Debug script to inspect NotebookLM Studio structure."""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.auth.google_auth import GoogleAuthenticator
from src.generators.notebooklm import NotebookLMClient
from selenium.webdriver.common.by import By


def inspect_page(driver):
    """Inspect page elements for debugging."""
    print("\n" + "=" * 60)
    print("PAGE INSPECTION")
    print("=" * 60)
    
    print(f"\nURL: {driver.current_url}")
    print(f"Title: {driver.title}")
    
    # Find all checkboxes
    print("\n--- CHECKBOXES ---")
    checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
    print(f"Found {len(checkboxes)} checkboxes")
    for i, cb in enumerate(checkboxes[:20]):
        try:
            aria = cb.get_attribute("aria-label") or "(no aria)"
            name = cb.get_attribute("name") or "(no name)"
            vis = "visible" if cb.is_displayed() else "hidden"
            print(f"  [{i}] {vis}: aria='{aria[:50]}' name='{name}'")
        except Exception as e:
            print(f"  [{i}] Error: {e}")
    
    # Find elements with "Quelle" text
    print("\n--- ELEMENTS WITH 'Quelle' ---")
    quelle_elems = driver.find_elements(By.XPATH, "//*[contains(text(), 'Quelle')]")
    print(f"Found {len(quelle_elems)} elements")
    for i, el in enumerate(quelle_elems[:15]):
        try:
            tag = el.tag_name
            text = el.text[:60].replace('\n', ' ')
            vis = "visible" if el.is_displayed() else "hidden"
            print(f"  [{i}] <{tag}> {vis}: '{text}'")
        except Exception as e:
            print(f"  [{i}] Error: {e}")
    
    # Find Studio panel buttons
    print("\n--- STUDIO BUTTONS ---")
    button_texts = ["Audio", "Video", "Mindmap", "Quiz", "Karteikarten", "Infografik"]
    for btn_text in button_texts:
        elems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{btn_text}')]")
        visible = [e for e in elems if e.is_displayed()]
        print(f"  '{btn_text}': found {len(visible)} visible elements")
        for el in visible[:3]:
            tag = el.tag_name
            aria = el.get_attribute("aria-label") or ""
            print(f"    <{tag}> aria='{aria[:40]}'")
    
    # Find mat-icon elements (material icons)
    print("\n--- MATERIAL ICONS (mat-icon) ---")
    icons = driver.find_elements(By.TAG_NAME, "mat-icon")
    icon_texts = set()
    for icon in icons[:50]:
        try:
            if icon.is_displayed():
                text = icon.text.strip()
                if text and text not in icon_texts:
                    icon_texts.add(text)
        except:
            pass
    print(f"  Icon texts: {sorted(icon_texts)[:20]}")
    
    # Find source list items
    print("\n--- SOURCE LIST STRUCTURE ---")
    # Try different container patterns
    patterns = [
        ("source-list", "[class*='source-list']"),
        ("sources-panel", "[class*='sources']"),
        ("quellen", "[aria-label*='Quelle']"),
        ("mat-list", "mat-list"),
        ("list items", "[role='listitem']"),
    ]
    for name, selector in patterns:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, selector)
            visible = [e for e in elems if e.is_displayed()]
            if visible:
                print(f"  {name} ({selector}): {len(visible)} visible")
                for el in visible[:3]:
                    text = el.text[:60].replace('\n', ' ')
                    print(f"    '{text}'")
        except Exception as e:
            print(f"  {name}: Error - {e}")
    
    # Find left sidebar content
    print("\n--- LEFT SIDEBAR ---")
    sidebars = driver.find_elements(By.CSS_SELECTOR, "[class*='sidebar'], [class*='panel'], [class*='drawer']")
    for sb in sidebars[:5]:
        if sb.is_displayed():
            text = sb.text[:200].replace('\n', ' | ')
            print(f"  Sidebar: '{text}'")


def main():
    notebook_url = sys.argv[1] if len(sys.argv) > 1 else "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"
    
    print(f"Inspecting: {notebook_url}")
    
    auth = GoogleAuthenticator()
    client = NotebookLMClient(auth)
    
    if not client.navigate_to_notebook(notebook_url):
        print("Failed to navigate!")
        return 1
    
    time.sleep(5)  # Let page fully load
    
    inspect_page(client.driver)
    
    print("\n" + "=" * 60)
    print("Browser open for manual inspection...")
    print("Press Ctrl+C to exit")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
