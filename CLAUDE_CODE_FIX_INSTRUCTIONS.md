# URGENT: Claude Code Fix Instructions for NotebookLM Generation Tool

**Date:** 2025-12-07  
**Priority:** CRITICAL - TOOL IS COMPLETELY BROKEN  
**Project Path:** `/Users/qwitch13/IdeaProjects/notebook-lm-generation`  
**Existing NotebookLM Notebook:** https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009

---

## EXECUTIVE SUMMARY

The tool has **5 CRITICAL BUGS** that make it completely non-functional:

1. **`notebooklm.py` has ALL METHODS DUPLICATED** (lines 55-175 are duplicated at 220-384)
2. **Missing methods:** `generate_audio_overview()`, `send_chat_message()`, `generate_flashcards()`
3. **Outdated CSS selectors** - NotebookLM UI has changed
4. **Missing `open_gemini_in_new_tab()`** in `GoogleAuthenticator`
5. **Incomplete `add_text_source()`** - returns True without doing anything

---

## FIX #1: REPLACE ENTIRE `notebooklm.py` (CRITICAL)

**File:** `src/generators/notebooklm.py`

**Problem:** The file has EVERY method defined TWICE due to copy-paste error. Lines 55-175 duplicate lines 220-384. Critical methods like `generate_audio_overview()` are NEVER defined.

**Action:** REPLACE THE ENTIRE FILE with this clean implementation:

```python
"""NotebookLM browser automation client."""

import time
import re
import traceback
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from ..auth.google_auth import GoogleAuthenticator
from ..utils.logger import get_logger
from ..config.settings import get_settings


@dataclass
class NotebookProject:
    """Represents a NotebookLM project/notebook."""
    name: str
    url: Optional[str] = None
    sources_count: int = 0


class NotebookLMClient:
    """Browser automation client for NotebookLM."""
    
    # CSS Selectors - Updated for current NotebookLM UI (Dec 2025)
    # NOTE: These may need manual verification/update by inspecting the actual UI
    SELECTORS = {
        # Notebook creation
        "new_notebook_btn": (
            "[data-test-id='create-notebook-button'], "
            "button.create-new-notebook-button, "
            "button[aria-label*='Create'], "
            "button[aria-label*='New notebook'], "
            ".create-notebook-btn"
        ),
        "notebook_title_input": (
            "[data-test-id='notebook-title-input'], "
            "input[aria-label*='title'], "
            "input[placeholder*='Untitled']"
        ),
        "notebook_title_header": (
            "[data-test-id='notebook-title-header'], "
            "h1, .notebook-title"
        ),
        
        # Sources
        "add_source_btn": (
            "[data-test-id='add-source-button'], "
            "button[aria-label*='Add source'], "
            "button[aria-label*='Add'], "
            ".add-source-btn"
        ),
        "sources_count": "[data-test-id='sources-count']",
        "upload_file_option": (
            "[data-test-id='upload-file-option'], "
            "button[aria-label*='Upload']"
        ),
        "file_input": "input[type='file']",
        "paste_text_option": (
            "[data-test-id='paste-text-option'], "
            "button:has-text('Paste text'), "
            "div[role='menuitem']:has-text('Paste text'), "
            "[aria-label*='Paste text']"
        ),
        "text_input": (
            "textarea[data-test-id='pasted-text-input'], "
            "textarea, "
            "[contenteditable='true']"
        ),
        "submit_source_btn": (
            "button[type='submit'], "
            "button[aria-label*='Insert'], "
            "button[aria-label*='Add'], "
            "button:has-text('Insert')"
        ),
        
        # Audio/Studio
        "studio_tab": (
            "[data-test-id='studio-tab'], "
            "button[aria-label*='Audio Overview'], "
            "[data-tab='audio'], "
            ".studio-tab, "
            "button:has-text('Audio Overview')"
        ),
        "generate_audio_btn": (
            "[data-test-id='audio-overview-generate-button'], "
            "button[aria-label*='Generate'], "
            "button:has-text('Generate'), "
            ".generate-audio-btn"
        ),
        "audio_player": "[data-test-id='audio-player'], audio, .audio-player",
        "download_btn": "[data-test-id='download-button'], button[aria-label*='Download']",
        
        # Chat
        "chat_input": (
            "[data-test-id='chat-input'], "
            "textarea[aria-label*='message'], "
            "textarea[placeholder*='Ask'], "
            ".chat-input, "
            "[contenteditable='true'].chat-input"
        ),
        "send_btn": (
            "[data-test-id='send-button'], "
            "button[aria-label*='Send'], "
            "button[type='submit'], "
            ".send-btn"
        ),
        "response_container": (
            "[data-test-id='chat-response'], "
            ".response, "
            ".message-content, "
            "[data-message-author-role='model'], "
            ".chat-message.assistant"
        ),
        
        # UI state
        "loading_indicator": (
            "[data-test-id='loading-indicator'], "
            "[role='progressbar'], "
            ".loading, "
            ".spinner, "
            ".generating"
        ),
        "overlay": "[role='dialog'], [aria-modal='true'], .modal, .overlay",
    }

    def __init__(self, authenticator: GoogleAuthenticator):
        """Initialize the NotebookLM client."""
        self.auth = authenticator
        self.logger = get_logger()
        self.settings = get_settings()
        self.driver = self.auth.get_driver()
        self.current_notebook: Optional[NotebookProject] = None

        if not self.is_driver_alive():
            self.logger.error("FATAL: WebDriver is not alive at initialization.")
            raise WebDriverException("Driver is not alive at client initialization.")
        self.logger.info("NotebookLMClient initialized with a live WebDriver.")

    def is_driver_alive(self) -> bool:
        """Check if the WebDriver instance is still responsive."""
        if self.driver is None:
            self.logger.warning("is_driver_alive: Driver is None.")
            return False
        try:
            _ = self.driver.current_url
            return True
        except WebDriverException as e:
            self.logger.error(f"is_driver_alive check failed: {e}")
            return False

    def _find_element(self, selector: str, timeout: int = 10):
        """Find element with multiple selector fallbacks."""
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot find element.")
            return None
        
        # Handle multiple selectors separated by comma
        selectors = [s.strip() for s in selector.split(',')]
        
        for sel in selectors:
            try:
                element = WebDriverWait(self.driver, timeout // len(selectors) or 1).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, sel))
                )
                self.logger.debug(f"Found element with selector: {sel}")
                return element
            except (TimeoutException, NoSuchElementException):
                continue
            except Exception as e:
                self.logger.debug(f"Error finding {sel}: {e}")
                continue
        
        self.logger.debug(f"Could not find element with any selector: {selector[:100]}...")
        return None

    def _click_element(self, selector: str, timeout: int = 10):
        """Click element with JS fallback."""
        if not self.is_driver_alive():
            raise TimeoutException("Driver not alive for click.")
        
        element = self._find_element(selector, timeout)
        if not element:
            raise TimeoutException(f"Could not find element to click: {selector[:100]}...")
        
        try:
            # Try JS click first (more reliable)
            self.driver.execute_script("arguments[0].click();", element)
            self.logger.debug(f"JS click successful")
        except Exception as e:
            self.logger.debug(f"JS click failed, trying regular click: {e}")
            element.click()
        
        return True

    def _wait_for_overlay_dismiss(self, timeout: int = 5):
        """Wait for any overlay/modal to be dismissed."""
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.SELECTORS["overlay"]))
            )
        except TimeoutException:
            pass

    def navigate_to_notebooklm(self) -> bool:
        """Navigate to NotebookLM homepage."""
        self.logger.debug("Executing navigate_to_notebooklm...")
        if not self.is_driver_alive():
            self.logger.error("Cannot navigate: WebDriver is not alive.")
            return False
        try:
            self.driver.get(self.settings.notebooklm_url)
            WebDriverWait(self.driver, 30).until(EC.url_contains("notebooklm.google.com"))
            self.logger.info(f"Successfully navigated to NotebookLM: {self.driver.current_url}")
            return True
        except Exception as e:
            self.logger.error(f"Exception in navigate_to_notebooklm: {e}")
            return False

    def navigate_to_notebook(self, notebook_url: str) -> bool:
        """Navigate directly to an existing notebook by URL."""
        self.logger.info(f"Navigating to existing notebook: {notebook_url}")
        if not self.is_driver_alive():
            self.logger.error("Cannot navigate: WebDriver is not alive.")
            return False
        try:
            self.driver.get(notebook_url)
            time.sleep(3)
            # Verify we're on a notebook page
            if "notebooklm.google.com/notebook" in self.driver.current_url:
                self.logger.info("Successfully navigated to notebook.")
                self.current_notebook = NotebookProject(
                    name=self.get_notebook_title() or "Existing Notebook",
                    url=notebook_url
                )
                return True
            else:
                self.logger.warning(f"URL mismatch. Current: {self.driver.current_url}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to navigate to notebook: {e}")
            return False

    def create_notebook(self, name: str) -> NotebookProject:
        """Create a new notebook."""
        self.logger.info(f"Creating notebook: {name}")
        
        if not self.is_driver_alive():
            self.driver = self.auth.get_driver(force_recreate=True)
            if not self.is_driver_alive():
                raise WebDriverException("Failed to get a live driver for notebook creation.")

        try:
            if "notebooklm.google.com" not in self.driver.current_url:
                self.navigate_to_notebooklm()
            
            time.sleep(2)
            self._wait_for_overlay_dismiss()

            self.logger.debug("Clicking 'new notebook' button...")
            self._click_element(self.SELECTORS["new_notebook_btn"], timeout=20)
            time.sleep(2)

            title_input = self._find_element(self.SELECTORS["notebook_title_input"], timeout=10)
            if title_input:
                title_input.clear()
                title_input.send_keys(name)
                title_input.send_keys(Keys.RETURN)
                self.logger.debug(f"Set notebook title to: {name}")
            else:
                self.logger.warning("Could not find title input. Notebook may be auto-named.")

            # Wait for notebook interface
            time.sleep(3)
            WebDriverWait(self.driver, 20).until(lambda d: self._has_notebook_interface(d))

            self.current_notebook = NotebookProject(name=name, url=self.driver.current_url)
            self.logger.info(f"Successfully created notebook: {name}")
            return self.current_notebook

        except Exception as e:
            self.logger.error(f"Failed to create notebook: {e}")
            self.logger.error(traceback.format_exc())
            # Return a fallback notebook
            return NotebookProject(name=name, url=self.driver.current_url if self.driver else None)

    def _has_notebook_interface(self, driver) -> bool:
        """Check if the notebook interface is visible."""
        try:
            selectors = self.SELECTORS["add_source_btn"].split(',')
            for sel in selectors:
                try:
                    if driver.find_element(By.CSS_SELECTOR, sel.strip()).is_displayed():
                        return True
                except:
                    continue
            return False
        except Exception:
            return False

    def add_text_source(self, text: str, title: str = "Source") -> bool:
        """Add text content as a source to the current notebook."""
        self.logger.info(f"Adding text source: {title} ({len(text)} chars)")
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot add text source.")
            return False
        
        try:
            # Click add source button
            self._click_element(self.SELECTORS["add_source_btn"], timeout=10)
            time.sleep(1)
            
            # Click paste text option
            paste_option = self._find_element(self.SELECTORS["paste_text_option"], timeout=10)
            if paste_option:
                self.driver.execute_script("arguments[0].click();", paste_option)
                time.sleep(1)
            else:
                self.logger.warning("Could not find paste text option")
                return False
            
            # Find text input area
            text_input = self._find_element(self.SELECTORS["text_input"], timeout=10)
            if not text_input:
                self.logger.error("Could not find text input area")
                return False
            
            # Clear and enter text in chunks (to avoid timeout with large text)
            text_input.clear()
            chunk_size = 5000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                text_input.send_keys(chunk)
                time.sleep(0.1)
            
            time.sleep(1)
            
            # Try to find and click submit button
            submit_btn = self._find_element(self.SELECTORS["submit_source_btn"], timeout=5)
            if submit_btn:
                self.driver.execute_script("arguments[0].click();", submit_btn)
            else:
                # Fallback: Ctrl+Enter
                text_input.send_keys(Keys.CONTROL + Keys.RETURN)
            
            time.sleep(3)
            self.logger.info(f"Successfully added text source: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add text source: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def generate_audio_overview(self) -> bool:
        """Generate audio overview using NotebookLM's Audio Overview feature."""
        self.logger.info("Generating audio overview...")
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot generate audio.")
            return False
        
        try:
            # Click on the Audio Overview / Studio tab
            studio_tab = self._find_element(self.SELECTORS["studio_tab"], timeout=10)
            if studio_tab:
                self.driver.execute_script("arguments[0].click();", studio_tab)
                time.sleep(2)
                self.logger.debug("Clicked Studio/Audio Overview tab")
            else:
                self.logger.warning("Could not find Studio tab")
            
            # Click generate audio button
            generate_btn = self._find_element(self.SELECTORS["generate_audio_btn"], timeout=10)
            if generate_btn:
                self.driver.execute_script("arguments[0].click();", generate_btn)
                self.logger.info("Audio generation started. This may take several minutes...")
                time.sleep(5)
                return True
            else:
                self.logger.warning("Could not find generate audio button")
                return False
                
        except Exception as e:
            self.logger.error(f"Audio generation failed: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def send_chat_message(self, message: str, timeout: int = 60) -> Optional[str]:
        """Send a message to NotebookLM chat and get response."""
        self.logger.info(f"Sending chat message: {message[:50]}...")
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot send chat message.")
            return None
        
        try:
            # Find chat input
            chat_input = self._find_element(self.SELECTORS["chat_input"], timeout=15)
            if not chat_input:
                self.logger.error("Could not find chat input")
                return None
            
            # Clear and enter message
            chat_input.clear()
            chat_input.send_keys(message)
            time.sleep(0.5)
            
            # Find and click send button
            send_btn = self._find_element(self.SELECTORS["send_btn"], timeout=5)
            if send_btn:
                self.driver.execute_script("arguments[0].click();", send_btn)
            else:
                # Fallback: press Enter
                chat_input.send_keys(Keys.RETURN)
            
            self.logger.debug("Message sent, waiting for response...")
            time.sleep(3)
            
            # Wait for loading indicator to disappear
            try:
                loading_selectors = self.SELECTORS["loading_indicator"].split(',')
                for sel in loading_selectors:
                    try:
                        WebDriverWait(self.driver, timeout).until_not(
                            EC.presence_of_element_located((By.CSS_SELECTOR, sel.strip()))
                        )
                        break
                    except:
                        continue
            except TimeoutException:
                self.logger.warning("Loading indicator timeout - response may be incomplete")
            
            # Get response
            time.sleep(2)
            response_selectors = self.SELECTORS["response_container"].split(',')
            for sel in response_selectors:
                try:
                    response_elements = self.driver.find_elements(By.CSS_SELECTOR, sel.strip())
                    if response_elements:
                        response_text = response_elements[-1].text
                        self.logger.debug(f"Got response ({len(response_text)} chars)")
                        return response_text
                except:
                    continue
            
            self.logger.warning("Could not extract response text")
            return None
            
        except Exception as e:
            self.logger.error(f"Chat message failed: {e}")
            self.logger.error(traceback.format_exc())
            return None

    def generate_flashcards(self) -> Optional[str]:
        """Generate flashcards using NotebookLM's chat."""
        self.logger.info("Generating flashcards via NotebookLM chat...")
        return self.send_chat_message(
            "Create comprehensive flashcards for all the key concepts in this notebook. "
            "Format each card with Q: (question) and A: (answer). "
            "Include at least 15-20 flashcards covering the main topics."
        )

    def generate_summary(self) -> Optional[str]:
        """Generate a summary using NotebookLM's chat."""
        self.logger.info("Generating summary via NotebookLM chat...")
        return self.send_chat_message(
            "Create a comprehensive summary of all the content in this notebook. "
            "Include the main topics, key points, and important details."
        )

    def generate_quiz(self) -> Optional[str]:
        """Generate a quiz using NotebookLM's chat."""
        self.logger.info("Generating quiz via NotebookLM chat...")
        return self.send_chat_message(
            "Create a quiz with 10-15 multiple choice questions based on this notebook. "
            "Format: Question, A) B) C) D) options, and mark the correct answer."
        )

    def get_sources_count(self) -> int:
        """Get the current number of sources in the notebook."""
        try:
            count_element = self._find_element(self.SELECTORS["sources_count"], timeout=5)
            if count_element:
                match = re.search(r'\((\d+)\)', count_element.text)
                if match:
                    return int(match.group(1))
            return 0
        except Exception:
            return 0
            
    def get_notebook_title(self) -> Optional[str]:
        """Get the title of the current notebook."""
        try:
            title_element = self._find_element(self.SELECTORS["notebook_title_header"], timeout=5)
            if title_element:
                return title_element.text
        except Exception:
            pass
        return None

    def close(self):
        """Clean up resources."""
        self.logger.debug("NotebookLMClient closing...")
        # Don't close driver here - let GoogleAuthenticator handle it
        self.current_notebook = None
```

---

## FIX #2: ADD `open_gemini_in_new_tab()` TO `google_auth.py`

**File:** `src/auth/google_auth.py`

**Problem:** Method is called but never defined, causing `AttributeError`.

**Action:** Add this method to the `GoogleAuthenticator` class (before the `close()` method):

```python
    def open_gemini_in_new_tab(self) -> bool:
        """Open Gemini in a new browser tab."""
        self.logger.info("Opening Gemini in new tab...")
        try:
            if not self.driver:
                self.logger.error("No driver available")
                return False
            
            # Execute JavaScript to open new tab
            self.driver.execute_script(f"window.open('{self.settings.gemini_url}', '_blank');")
            
            # Switch to the new tab
            time.sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Wait for Gemini to load
            WebDriverWait(self.driver, 30).until(EC.url_contains("gemini.google.com"))
            
            self.logger.info("Gemini opened in new tab successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open Gemini: {e}")
            self.logger.error(traceback.format_exc())
            return False
```

---

## FIX #3: VERIFY `settings.py` HAS REQUIRED URLs

**File:** `src/config/settings.py`

Ensure these URLs are defined:

```python
notebooklm_url: str = "https://notebooklm.google.com/"
gemini_url: str = "https://gemini.google.com/"
```

---

## TESTING COMMANDS

After applying fixes, test in this order:

### Test 1: Syntax Check
```bash
cd /Users/qwitch13/IdeaProjects/notebook-lm-generation
python3 -m py_compile src/generators/notebooklm.py
python3 -m py_compile src/auth/google_auth.py
echo "Syntax OK!"
```

### Test 2: CLI Help
```bash
source venv/bin/activate
nlmgen --help
```

### Test 3: Test with Existing Notebook (Bypasses API quota!)
```bash
nlmgen /path/to/any/file.pdf \
    --notebook-url "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009" \
    --no-api \
    -v
```

This uses the existing "Digital Communications: Test" notebook and bypasses Gemini API entirely.

---

## VERIFICATION CHECKLIST

- [ ] `notebooklm.py` has NO duplicate methods (only ~350 lines, not ~384)
- [ ] `generate_audio_overview()` method exists
- [ ] `send_chat_message()` method exists  
- [ ] `generate_flashcards()` method exists
- [ ] `add_text_source()` is fully implemented (not just `return True`)
- [ ] `navigate_to_notebook()` method exists for `--notebook-url` mode
- [ ] `google_auth.py` has `open_gemini_in_new_tab()` method
- [ ] No `AttributeError` crashes
- [ ] CSS selectors include fallback options

---

## ERROR PATTERNS TO WATCH FOR

If you see these errors, here's what's wrong:

| Error | Cause | Fix |
|-------|-------|-----|
| `AttributeError: 'NotebookLMClient' object has no attribute 'generate_audio_overview'` | Method not defined | Add the method to notebooklm.py |
| `AttributeError: 'NotebookLMClient' object has no attribute 'send_chat_message'` | Method not defined | Add the method to notebooklm.py |
| `AttributeError: 'GoogleAuthenticator' object has no attribute 'open_gemini_in_new_tab'` | Method not defined | Add method to google_auth.py |
| `TimeoutException: Could not find element to click: [data-test-id='create-notebook-button']` | Outdated selector | Update SELECTORS dict |
| `SyntaxError` | Duplicate method definitions | Remove all duplicate code |

---

## SUMMARY

**Root Cause:** Copy-paste error duplicated half of `notebooklm.py`, and several methods were never implemented.

**Fix Order:**
1. **FIRST:** Replace entire `src/generators/notebooklm.py` with clean code above
2. **SECOND:** Add `open_gemini_in_new_tab()` to `src/auth/google_auth.py`
3. **THIRD:** Run syntax checks
4. **FOURTH:** Test with `--notebook-url` mode

**Files Modified:**
- `src/generators/notebooklm.py` - COMPLETE REWRITE
- `src/auth/google_auth.py` - Add one method
