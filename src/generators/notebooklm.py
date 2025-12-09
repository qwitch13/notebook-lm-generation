"""NotebookLM browser automation client."""

import time
import re
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
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


@dataclass  
class ErrorReport:
    """Detailed error report for debugging failures."""
    timestamp: str
    error_type: str
    error_message: str
    action_attempted: str
    page_url: str
    page_title: str
    buttons_found: List[dict]
    textareas_found: List[dict]
    editables_found: List[dict]
    screenshot_path: Optional[str]
    html_path: Optional[str]
    traceback_str: str


class NotebookLMClient:
    """Browser automation client for NotebookLM with robust element finding."""
    
    # Element search strategies: (By type, selector/xpath)
    # Using multiple strategies for resilience against UI changes
    # Includes both English AND German text patterns for internationalized UI
    ELEMENT_STRATEGIES = {
        "studio_tab": [
            # German UI: "Studio" tab
            (By.XPATH, "//*[contains(text(), 'Studio')]"),
            (By.XPATH, "//div[contains(@class, 'mdc-tab')][contains(., 'Studio')]"),
            (By.XPATH, "//div[contains(@class, 'mat-mdc-tab')][contains(., 'Studio')]"),
            # English fallbacks
            (By.XPATH, "//*[contains(text(), 'Audio Overview')]"),
            (By.XPATH, "//div[contains(@class, 'mdc-tab')][contains(., 'Audio Overview')]"),
            (By.CSS_SELECTOR, ".mdc-tab"),  # Find any tab
        ],
        "audio_summary_item": [
            # German: "Audio-Zusammenfassung"
            (By.XPATH, "//*[contains(text(), 'Audio-Zusammenfassung')]"),
            (By.XPATH, "//div[contains(., 'Audio-Zusammenfassung')]"),
            # English: "Audio Overview" or "Audio Summary"
            (By.XPATH, "//*[contains(text(), 'Audio Overview')]"),
            (By.XPATH, "//*[contains(text(), 'Audio Summary')]"),
            # Material icon based search
            (By.XPATH, "//*[contains(text(), 'audio_magic_eraser')]/following-sibling::*"),
        ],
        "generate_audio_btn": [
            # Look for Generate/Erstellen buttons
            (By.XPATH, "//button[contains(., 'Generate')]"),
            (By.XPATH, "//button[contains(., 'Erstellen')]"),  # German
            (By.XPATH, "//button[contains(., 'Create')]"),
            (By.XPATH, "//mat-icon[contains(text(), 'edit')]/parent::button"),
            (By.XPATH, "//button[contains(@class, 'mat-mdc-button')]"),
            (By.CSS_SELECTOR, "button.mat-mdc-button"),
        ],
        "chat_tab": [
            # Click on Chat tab first
            (By.XPATH, "//*[contains(text(), 'Chat')]"),
            (By.XPATH, "//div[contains(@class, 'mdc-tab')][contains(., 'Chat')]"),
            (By.XPATH, "//div[contains(@class, 'mat-mdc-tab')][contains(., 'Chat')]"),
        ],
        "chat_input": [
            # SPECIFIC patterns first - avoid research/deep research textboxes
            # German placeholder patterns for chat
            (By.XPATH, "//textarea[contains(@placeholder, 'Frage') and not(contains(@placeholder, 'Research'))]"),
            (By.XPATH, "//textarea[contains(@placeholder, 'Eingabe') and not(contains(@placeholder, 'Research'))]"),
            # English placeholder patterns for chat
            (By.XPATH, "//textarea[contains(@placeholder, 'Ask') and not(contains(@placeholder, 'research'))]"),
            (By.XPATH, "//textarea[contains(@placeholder, 'Type') and not(contains(@placeholder, 'research'))]"),
            # Chat-specific containers
            (By.XPATH, "//div[contains(@class, 'chat')]//textarea"),
            (By.XPATH, "//*[contains(@class, 'chat-input')]//textarea"),
            # Form inputs in chat area
            (By.CSS_SELECTOR, ".chat-container textarea"),
            (By.CSS_SELECTOR, "[data-testid='chat-input']"),
            # GENERIC fallback LAST (may hit research box)
            (By.CSS_SELECTOR, "textarea:not([placeholder*='Research']):not([placeholder*='research'])"),
            (By.CSS_SELECTOR, "textarea"),
        ],
        "send_btn": [
            (By.XPATH, "//button[contains(@aria-label, 'Send')]"),
            (By.XPATH, "//button[contains(@aria-label, 'Senden')]"),  # German
            (By.XPATH, "//button[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "form button"),
        ],
        "response_container": [
            (By.XPATH, "//div[contains(@class, 'response')]"),
            (By.XPATH, "//div[contains(@class, 'message')]"),
            (By.XPATH, "//div[contains(@class, 'answer')]"),
            (By.CSS_SELECTOR, ".response"),
            (By.CSS_SELECTOR, ".message-content"),
        ],
        "sources_tab": [
            # German: "Quellen"
            (By.XPATH, "//*[contains(text(), 'Quellen')]"),
            (By.XPATH, "//div[contains(@class, 'mdc-tab')][contains(., 'Quellen')]"),
            # English
            (By.XPATH, "//*[contains(text(), 'Sources')]"),
        ],
        "add_source_btn": [
            # German: "Quelle hinzufügen"
            (By.XPATH, "//button[contains(., 'hinzufügen')]"),
            (By.XPATH, "//*[contains(text(), 'Quelle hinzufügen')]"),
            # English
            (By.XPATH, "//button[contains(., 'Add source')]"),
            (By.XPATH, "//button[contains(., 'Add')]"),
        ],
        "flashcards_item": [
            # German: "Karteikarten"
            (By.XPATH, "//*[contains(text(), 'Karteikarten')]"),
            # English
            (By.XPATH, "//*[contains(text(), 'Flashcards')]"),
        ],
        "quiz_item": [
            (By.XPATH, "//*[contains(text(), 'Quiz')]"),
        ],
        "add_note_btn": [
            # German: "Notiz hinzufügen"  
            (By.XPATH, "//*[contains(text(), 'Notiz hinzufügen')]"),
            # English
            (By.XPATH, "//*[contains(text(), 'Add note')]"),
        ],
        "new_notebook_btn": [
            # German: "Notebook erstellen"
            (By.XPATH, "//button[contains(., 'erstellen')]"),
            (By.XPATH, "//*[contains(text(), 'Notebook erstellen')]"),
            # English
            (By.XPATH, "//button[contains(., 'Create')]"),
            (By.XPATH, "//button[contains(., 'New notebook')]"),
        ],
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
            return False
        try:
            _ = self.driver.current_url
            return True
        except WebDriverException:
            return False

    def _generate_error_report(self, action: str, error: Exception = None) -> ErrorReport:
        """Generate a detailed error report for debugging."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Collect page info
        page_url = ""
        page_title = ""
        buttons_info = []
        textareas_info = []
        editables_info = []
        screenshot_path = None
        html_path = None
        
        try:
            if self.is_driver_alive():
                page_url = self.driver.current_url
                page_title = self.driver.title
                
                # Collect buttons
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for i, btn in enumerate(buttons[:20]):
                    try:
                        buttons_info.append({
                            "index": i,
                            "text": btn.text[:50].replace('\n', ' ') if btn.text else "",
                            "aria": btn.get_attribute("aria-label") or "",
                            "visible": btn.is_displayed()
                        })
                    except:
                        pass
                
                # Collect textareas
                textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                for i, ta in enumerate(textareas[:10]):
                    try:
                        textareas_info.append({
                            "index": i,
                            "placeholder": ta.get_attribute("placeholder") or "",
                            "aria": ta.get_attribute("aria-label") or "",
                            "visible": ta.is_displayed()
                        })
                    except:
                        pass
                
                # Collect editables
                editables = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
                for i, ed in enumerate(editables[:10]):
                    try:
                        editables_info.append({
                            "index": i,
                            "tag": ed.tag_name,
                            "role": ed.get_attribute("role") or "",
                            "visible": ed.is_displayed()
                        })
                    except:
                        pass
                
                # Save screenshot
                try:
                    screenshot_path = str(Path.home() / f"nlm_error_{timestamp}.png")
                    self.driver.save_screenshot(screenshot_path)
                except:
                    pass
                
                # Save HTML
                try:
                    html_path = str(Path.home() / f"nlm_error_{timestamp}.html")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                except:
                    pass
        except:
            pass
        
        report = ErrorReport(
            timestamp=timestamp,
            error_type=type(error).__name__ if error else "Unknown",
            error_message=str(error) if error else "Element not found",
            action_attempted=action,
            page_url=page_url,
            page_title=page_title,
            buttons_found=buttons_info,
            textareas_found=textareas_info,
            editables_found=editables_info,
            screenshot_path=screenshot_path,
            html_path=html_path,
            traceback_str=traceback.format_exc() if error else ""
        )
        
        # Save report to file
        try:
            report_path = Path.home() / f"nlm_error_report_{timestamp}.json"
            with open(report_path, "w") as f:
                json.dump({
                    "timestamp": report.timestamp,
                    "error_type": report.error_type,
                    "error_message": report.error_message,
                    "action_attempted": report.action_attempted,
                    "page_url": report.page_url,
                    "page_title": report.page_title,
                    "buttons_found": report.buttons_found,
                    "textareas_found": report.textareas_found,
                    "editables_found": report.editables_found,
                    "screenshot_path": report.screenshot_path,
                    "html_path": report.html_path,
                }, f, indent=2)
            self.logger.error(f"📋 Error report saved: {report_path}")
            if screenshot_path:
                self.logger.error(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            self.logger.error(f"Failed to save error report: {e}")
        
        return report

    def _find_element_multi_strategy(self, element_key: str, timeout: int = 10) -> Optional[any]:
        """Find element using multiple strategies (XPath + CSS fallbacks)."""
        if not self.is_driver_alive():
            self.logger.error("Driver not alive.")
            return None
        
        strategies = self.ELEMENT_STRATEGIES.get(element_key, [])
        if not strategies:
            self.logger.error(f"No strategies defined for: {element_key}")
            return None
        
        time_per_strategy = max(1, timeout // len(strategies))
        
        for by_type, selector in strategies:
            try:
                element = WebDriverWait(self.driver, time_per_strategy).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                if element and element.is_displayed():
                    self.logger.debug(f"Found '{element_key}' with: {by_type}='{selector}'")
                    return element
            except (TimeoutException, NoSuchElementException):
                continue
            except Exception as e:
                self.logger.debug(f"Strategy failed for {element_key}: {e}")
                continue
        
        self.logger.warning(f"Could not find element: {element_key}")
        self._debug_dump_page_info()
        return None

    def _find_clickable_by_text(self, text: str, timeout: int = 10) -> Optional[any]:
        """Find a clickable element containing specific text."""
        if not self.is_driver_alive():
            return None
        
        # More comprehensive XPath patterns for Angular Material UI
        xpaths = [
            # Angular Material tabs
            f"//div[contains(@class, 'mdc-tab')][contains(., '{text}')]",
            f"//div[contains(@class, 'mat-mdc-tab')][contains(., '{text}')]",
            # Standard buttons
            f"//button[contains(., '{text}')]",
            # Material buttons
            f"//button[contains(@class, 'mat-mdc-button')][contains(., '{text}')]",
            # Links
            f"//a[contains(., '{text}')]",
            # Div role=button
            f"//div[@role='button'][contains(., '{text}')]",
            f"//div[@role='tab'][contains(., '{text}')]",
            # Span inside clickable parent
            f"//span[contains(text(), '{text}')]/ancestor::button",
            f"//span[contains(text(), '{text}')]/ancestor::div[@role='button']",
            f"//span[contains(text(), '{text}')]/ancestor::div[contains(@class, 'mdc-tab')]",
            # Generic text match
            f"//*[contains(text(), '{text}')]",
            # Case-insensitive search (for text inside elements)
            f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
        ]
        
        time_per_xpath = max(1, timeout // len(xpaths))
        
        for xpath in xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
                        self.logger.debug(f"Found clickable with text '{text}' using: {xpath[:50]}...")
                        return element
            except Exception as e:
                self.logger.debug(f"XPath failed for '{text}': {e}")
                continue
        
        self.logger.debug(f"Could not find clickable element with text: {text}")
        return None

    def _find_input_field(self, timeout: int = 10) -> Optional[any]:
        """Find any input field (textarea or contenteditable)."""
        if not self.is_driver_alive():
            return None
        
        strategies = [
            (By.CSS_SELECTOR, "textarea:not([disabled])"),
            (By.CSS_SELECTOR, "[contenteditable='true']"),
            (By.CSS_SELECTOR, "input[type='text']:not([disabled])"),
            (By.XPATH, "//textarea"),
            (By.XPATH, "//div[@contenteditable='true']"),
        ]
        
        for by_type, selector in strategies:
            try:
                elements = self.driver.find_elements(by_type, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        self.logger.debug(f"Found input field: {selector}")
                        return elem
            except:
                continue
        return None

    def _find_edit_button_near_text(self, text: str, timeout: int = 10) -> Optional[any]:
        """Find an edit button near an element containing specific text.
        
        In NotebookLM, items like 'Audio-Zusammenfassung' have an edit icon (mat-icon) next to them.
        """
        if not self.is_driver_alive():
            return None
        
        # Strategies to find edit buttons near text
        xpaths = [
            # mat-icon with 'edit' text near the target text
            f"//*[contains(text(), '{text}')]/following-sibling::*[contains(text(), 'edit')]",
            f"//*[contains(text(), '{text}')]/following::mat-icon[contains(text(), 'edit')]",
            f"//*[contains(text(), '{text}')]/parent::*//*[contains(text(), 'edit')]",
            f"//*[contains(text(), '{text}')]/ancestor::*[contains(@class, 'item') or contains(@class, 'row')]//mat-icon[contains(text(), 'edit')]",
            # Button containing edit icon near text
            f"//*[contains(text(), '{text}')]/following::button[.//mat-icon[contains(text(), 'edit')]]",
            f"//*[contains(text(), '{text}')]/parent::*//button",
            # The item itself might be clickable
            f"//*[contains(text(), '{text}')]/parent::*[@role='button']",
            f"//*[contains(text(), '{text}')]/ancestor::*[@role='button']",
        ]
        
        for xpath in xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
                        self.logger.debug(f"Found edit button near '{text}' using: {xpath[:50]}...")
                        return element
            except Exception as e:
                self.logger.debug(f"XPath failed: {e}")
                continue
        
        self.logger.debug(f"Could not find edit button near: {text}")
        return None

    def _debug_dump_page_info(self):
        """Dump page info for debugging when elements can't be found."""
        try:
            self.logger.debug(f"Current URL: {self.driver.current_url}")
            self.logger.debug(f"Page title: {self.driver.title}")
            
            # Check for iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.logger.debug(f"Found {len(iframes)} iframes on page")
            
            # List all buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.logger.debug(f"Found {len(buttons)} buttons on page")
            for i, btn in enumerate(buttons[:15]):  # First 15 only
                try:
                    text = btn.text[:50].replace('\n', ' ') if btn.text else "(no text)"
                    aria = btn.get_attribute("aria-label") or "(no aria)"
                    visible = "visible" if btn.is_displayed() else "hidden"
                    self.logger.debug(f"  Button {i}: [{visible}] text='{text}' aria='{aria}'")
                except:
                    pass
            
            # List all textareas
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            self.logger.debug(f"Found {len(textareas)} textareas on page")
            for i, ta in enumerate(textareas[:5]):
                try:
                    placeholder = ta.get_attribute("placeholder") or "(no placeholder)"
                    visible = "visible" if ta.is_displayed() else "hidden"
                    self.logger.debug(f"  Textarea {i}: [{visible}] placeholder='{placeholder}'")
                except:
                    pass
                    
            # List all contenteditable
            editables = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
            self.logger.debug(f"Found {len(editables)} contenteditable elements")
            
            # Save page source for debugging
            try:
                debug_path = Path.home() / "notebooklm_debug_page.html"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                self.logger.debug(f"Page source saved to: {debug_path}")
            except:
                pass
                
        except Exception as e:
            self.logger.debug(f"Debug dump failed: {e}")

    def _click_element_safe(self, element) -> bool:
        """Safely click an element with JS fallback."""
        if not element:
            return False
        try:
            # Scroll into view first
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            # Try JS click (more reliable)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            try:
                element.click()
                return True
            except Exception as e2:
                self.logger.error(f"Click failed: {e2}")
                return False

    def navigate_to_notebooklm(self) -> bool:
        """Navigate to NotebookLM homepage and ensure logged in."""
        if not self.is_driver_alive():
            return False
        try:
            self.driver.get(self.settings.notebooklm_url)
            time.sleep(3)  # Initial page load
            
            # Check if we're redirected to login
            max_wait = 120  # 2 minutes max wait for login
            waited = 0
            login_warning_shown = False
            
            while waited < max_wait:
                current_url = self.driver.current_url.lower()
                
                # Check if we're on login/accounts page
                if "accounts.google.com" in current_url or "signin" in current_url:
                    if not login_warning_shown:
                        self.logger.warning("=" * 50)
                        self.logger.warning("LOGIN REQUIRED")
                        self.logger.warning("Please log into your Google account in the browser window.")
                        self.logger.warning(f"Waiting up to {max_wait} seconds...")
                        self.logger.warning("=" * 50)
                        login_warning_shown = True
                    time.sleep(3)
                    waited += 3
                    continue
                
                # Check if we're on NotebookLM homepage (not just any notebooklm page)
                if "notebooklm.google.com" in current_url:
                    # Wait for page to fully load
                    time.sleep(3)
                    
                    # Verify we can find some expected element (the page loaded properly)
                    try:
                        WebDriverWait(self.driver, 10).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                    except:
                        pass
                    
                    # Look for any sign we're on a proper NotebookLM page
                    # Either the create button or existing notebooks
                    try:
                        # Check for create button or any notebook-related content
                        page_source = self.driver.page_source.lower()
                        if "notebook" in page_source or "create" in page_source or "erstellen" in page_source:
                            self.logger.info(f"Successfully navigated to NotebookLM: {self.driver.current_url}")
                            self._dismiss_overlays()
                            return True
                    except:
                        pass
                    
                    time.sleep(2)
                    waited += 2
                    continue
                
                # Unknown state, wait a bit
                time.sleep(2)
                waited += 2
            
            self.logger.error(f"Failed to reach NotebookLM after {max_wait}s. Current URL: {self.driver.current_url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    def navigate_to_notebook(self, notebook_url: str) -> bool:
        """Navigate directly to an existing notebook by URL."""
        self.logger.info(f"Navigating to notebook: {notebook_url}")
        if not self.is_driver_alive():
            return False
        try:
            self.driver.get(notebook_url)
            
            # Wait for page to fully load
            self.logger.debug("Waiting for page to load completely...")
            time.sleep(5)  # Initial wait
            
            # Wait for document ready state
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content (NotebookLM uses a lot of JS)
            time.sleep(5)
            
            # Verify we're on NotebookLM
            if "notebooklm.google.com" in self.driver.current_url:
                self.logger.info("Successfully navigated to notebook")
                self.current_notebook = NotebookProject(name="Existing Notebook", url=notebook_url)
                
                # Dismiss any welcome overlays/modals
                self._dismiss_overlays()
                
                # Debug: dump page info
                self._debug_dump_page_info()
                
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to navigate: {e}")
            return False

    def _dismiss_overlays(self):
        """Try to dismiss any modal overlays or welcome screens."""
        try:
            # Look for common dismiss buttons
            dismiss_texts = ["Got it", "Dismiss", "Close", "Skip", "OK", "Continue"]
            for text in dismiss_texts:
                try:
                    btn = self.driver.find_element(By.XPATH, f"//button[contains(., '{text}')]")
                    if btn and btn.is_displayed():
                        self._click_element_safe(btn)
                        self.logger.debug(f"Dismissed overlay with '{text}' button")
                        time.sleep(1)
                        break
                except:
                    continue
                    
            # Try pressing Escape
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.5)
            except:
                pass
        except:
            pass

    def create_notebook(self, name: str) -> NotebookProject:
        """Create a new notebook."""
        self.logger.info(f"Creating new notebook: {name}")
        
        if not self.is_driver_alive():
            self.driver = self.auth.get_driver(force_recreate=True)
        
        try:
            # Always navigate to NotebookLM first (this now handles login check)
            if not self.navigate_to_notebooklm():
                raise Exception("Failed to navigate to NotebookLM - login may be required")
            
            time.sleep(3)  # Extra wait for page to stabilize
            
            # Dismiss any overlays first
            self._dismiss_overlays()
            time.sleep(1)
            
            # Find and click create button - try multiple approaches
            create_btn = None
            
            # Try finding by + icon (most reliable for German UI)
            try:
                create_btn = self.driver.find_element(
                    By.XPATH, 
                    "//button[.//mat-icon[text()='add'] or contains(@class, 'create')]"
                )
            except:
                pass
            
            if not create_btn:
                create_btn = self._find_element_multi_strategy("new_notebook_btn", timeout=15)
            
            if not create_btn:
                # Try finding any FAB (floating action button) with + icon
                try:
                    create_btn = self.driver.find_element(
                        By.XPATH, 
                        "//button[contains(@class, 'fab') or contains(@class, 'mdc-fab')]"
                    )
                except:
                    pass
            
            if not create_btn:
                # Debug: list all buttons to help diagnose
                self.logger.warning("Could not find create button. Dumping page info...")
                self._debug_dump_page_info()
                raise Exception("Create notebook button not found - check if logged in properly")
            
            self._click_element_safe(create_btn)
            time.sleep(3)
            
            # Wait for new notebook page to load
            WebDriverWait(self.driver, 15).until(
                lambda d: "notebook" in d.current_url.lower()
            )
            
            self.current_notebook = NotebookProject(name=name, url=self.driver.current_url)
            self.logger.info(f"Created notebook: {self.driver.current_url}")
            return self.current_notebook
            
        except Exception as e:
            self.logger.error(f"Notebook creation failed: {e}")
            raise

    def generate_audio_overview(self) -> bool:
        """Generate audio overview using NotebookLM's Audio Overview feature."""
        self.logger.info("Generating audio overview...")
        print("🎵 generate_audio_overview called")
        
        if not self.is_driver_alive():
            print("❌ Driver not alive!")
            self._generate_error_report("generate_audio_overview - driver not alive")
            return False
        
        try:
            time.sleep(2)
            
            # Step 1: Click on Studio tab (right sidebar)
            self.logger.info("Looking for Studio tab...")
            print("1️⃣ Looking for Studio tab...")
            studio_tab = self._find_clickable_by_text("Studio", timeout=8)
            if not studio_tab:
                studio_tab = self._find_element_multi_strategy("studio_tab", timeout=5)
            
            if studio_tab:
                self._click_element_safe(studio_tab)
                time.sleep(2)
                self.logger.info("Clicked Studio tab")
                print("   ✅ Clicked Studio tab")
            else:
                self.logger.warning("Could not find Studio tab - it may already be active")
                print("   ⚠️ Could not find Studio tab")
            
            # Step 2: Find and click Audio-Zusammenfassung (German) or Audio Overview (English)
            self.logger.info("Looking for Audio Summary item...")
            print("2️⃣ Looking for Audio Summary (Audio-Zusammenfassung)...")
            time.sleep(1)
            
            # First try to find the edit button directly near the audio item
            edit_btn = self._find_edit_button_near_text("Audio-Zusammenfassung", timeout=5)
            if not edit_btn:
                edit_btn = self._find_edit_button_near_text("Audio Overview", timeout=3)
            if not edit_btn:
                edit_btn = self._find_edit_button_near_text("Audio Summary", timeout=3)
            
            if edit_btn:
                print("   ✅ Found edit button for Audio")
                self._click_element_safe(edit_btn)
                self.logger.info("Clicked edit button for Audio Summary")
                time.sleep(3)
                return True
            else:
                print("   No edit button found, trying to click audio item directly...")
            
            # Fallback: Click on the audio item itself
            audio_item = self._find_clickable_by_text("Audio-Zusammenfassung", timeout=5)
            if not audio_item:
                audio_item = self._find_clickable_by_text("Audio Overview", timeout=3)
            if not audio_item:
                audio_item = self._find_clickable_by_text("Audio Summary", timeout=3)
            if not audio_item:
                audio_item = self._find_element_multi_strategy("audio_summary_item", timeout=5)
            
            if audio_item:
                print(f"   Found audio item: {audio_item.text[:30] if audio_item.text else 'no text'}")
                self._click_element_safe(audio_item)
                time.sleep(2)
                self.logger.info("Clicked Audio Summary item")
                
                # Now look for Generate button in any dialog that opened
                time.sleep(1)
                generate_btn = self._find_clickable_by_text("Generate", timeout=5)
                if not generate_btn:
                    generate_btn = self._find_clickable_by_text("Erstellen", timeout=3)  # German
                if not generate_btn:
                    generate_btn = self._find_clickable_by_text("Create", timeout=3)
                if not generate_btn:
                    generate_btn = self._find_element_multi_strategy("generate_audio_btn", timeout=5)
                
                if generate_btn:
                    self._click_element_safe(generate_btn)
                    self.logger.info("Audio generation started! This may take several minutes...")
                    time.sleep(5)
                    return True
            
            self.logger.error("Could not find Audio Summary item or Generate button")
            self._generate_error_report("generate_audio_overview - Audio/Generate not found")
            return False
                
        except Exception as e:
            self.logger.error(f"Audio generation failed: {e}")
            self._generate_error_report("generate_audio_overview", e)
            return False

    def send_chat_message(self, message: str, timeout: int = 60) -> Optional[str]:
        """Send a message to NotebookLM chat and get response."""
        self.logger.info(f"Sending chat message: {message[:50]}...")
        print(f"💬 send_chat_message called with: {message[:50]}...")
        
        if not self.is_driver_alive():
            print("❌ Driver not alive!")
            return None
        
        try:
            time.sleep(1)
            
            # Step 1: Click on Chat tab first
            self.logger.info("Looking for Chat tab...")
            print("1️⃣ Looking for Chat tab...")
            chat_tab = self._find_clickable_by_text("Chat", timeout=5)
            if not chat_tab:
                chat_tab = self._find_element_multi_strategy("chat_tab", timeout=5)
            
            if chat_tab:
                self._click_element_safe(chat_tab)
                time.sleep(3)  # Wait longer for tab to switch and content to load
                self.logger.info("Clicked Chat tab")
                print("   ✅ Clicked Chat tab")
            else:
                self.logger.warning("Could not find Chat tab - may already be active")
                print("   ⚠️ Could not find Chat tab")
            
            # Step 2: Find chat input - be careful to find the RIGHT one
            # After clicking Chat tab, the chat panel should be visible
            self.logger.info("Looking for chat input...")
            print("2️⃣ Looking for chat input...")
            
            # Debug: show all textareas
            all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            print(f"   Found {len(all_textareas)} textareas total")
            for i, ta in enumerate(all_textareas):
                if ta.is_displayed():
                    ph = ta.get_attribute("placeholder") or "no placeholder"
                    print(f"   Textarea {i}: '{ph[:40]}'")
            
            chat_input = None
            
            # EXCLUDE these words in placeholders (they indicate non-chat inputs)
            exclude_words = ["research", "deep", "web", "quellen", "suchen", "search", "source"]
            
            # PREFER these words in placeholders (they indicate chat input)
            prefer_words = ["text eingeben", "eingeben", "frage", "ask", "type", "message", "nachricht"]
            
            # First pass: look for textareas with preferred words
            for ta in all_textareas:
                if ta.is_displayed():
                    ph = (ta.get_attribute("placeholder") or "").lower()
                    # Check if it has any preferred word and no excluded word
                    has_preferred = any(word in ph for word in prefer_words)
                    has_excluded = any(word in ph for word in exclude_words)
                    if has_preferred and not has_excluded:
                        chat_input = ta
                        print(f"   ✅ Found preferred chat input: '{ph[:40]}'")
                        break
            
            # Second pass: look for textareas without excluded words
            if not chat_input:
                for ta in all_textareas:
                    if ta.is_displayed():
                        ph = (ta.get_attribute("placeholder") or "").lower()
                        has_excluded = any(word in ph for word in exclude_words)
                        if not has_excluded and ph:  # Has placeholder but no excluded words
                            chat_input = ta
                            print(f"   Using fallback textarea: '{ph[:40]}'")
                            break
            
            if not chat_input:
                self.logger.error("Could not find chat input field")
                print("   ❌ Could not find any suitable chat input!")
                self._generate_error_report("send_chat_message - chat input not found")
                return None
            
            # Clear and enter message
            print(f"3️⃣ Typing message: {message[:30]}...")
            try:
                chat_input.clear()
            except:
                pass
            
            # Type message
            chat_input.send_keys(message)
            print("   ✅ Message typed")
            time.sleep(0.5)
            
            # Find and click send button
            print("4️⃣ Looking for send button...")
            send_btn = self._find_element_multi_strategy("send_btn", timeout=5)
            if send_btn:
                print("   Found send button, clicking...")
                self._click_element_safe(send_btn)
                print("   ✅ Clicked send button")
            else:
                # Fallback: press Enter
                print("   No send button found, pressing Enter...")
                self.logger.debug("Send button not found, pressing Enter")
                chat_input.send_keys(Keys.RETURN)
                print("   ✅ Pressed Enter")
            
            self.logger.info("Message sent, waiting for response...")
            print("5️⃣ Waiting for AI response...")
            
            # IMPORTANT: Wait for AI to actually generate a response
            # This takes at least 5-15 seconds typically
            print("   Waiting 20 seconds for AI to generate response...")
            time.sleep(20)
            
            # Get response
            print("6️⃣ Looking for response...")
            
            # The AI response should be DIFFERENT from what we sent
            user_message_lower = message.strip().lower()[:50]
            
            # Minimum length for a real response (filters out UI elements)
            MIN_RESPONSE_LENGTH = 50
            
            # IMPORTANT: Search ONLY within chat-panel to avoid sidebar content
            # NotebookLM structure: section > chat-panel > messages
            try:
                # First, find the chat-panel container
                chat_panel = None
                chat_panel_selectors = [
                    "chat-panel",  # Tag name
                    "section.chat-panel",
                    "[class*='chat-panel']",
                ]
                for sel in chat_panel_selectors:
                    try:
                        panels = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        for p in panels:
                            if p.is_displayed():
                                chat_panel = p
                                print(f"   Found chat-panel via: {sel}")
                                break
                        if chat_panel:
                            break
                    except:
                        continue
                
                if not chat_panel:
                    # Fallback: find by tag name
                    try:
                        chat_panel = self.driver.find_element(By.TAG_NAME, "chat-panel")
                        print("   Found chat-panel by tag name")
                    except:
                        print("   ⚠️ Could not find chat-panel element")
                
                # Search within chat-panel for response content
                search_context = chat_panel if chat_panel else self.driver
                context_name = "chat-panel" if chat_panel else "full page"
                
                # Selectors for AI response content (within chat-panel)
                response_selectors = [
                    # NotebookLM specific - look for response bubbles/messages
                    ".//div[contains(@class, 'response')]",
                    ".//div[contains(@class, 'answer')]",
                    ".//div[contains(@class, 'message-content')]",
                    ".//div[contains(@class, 'bot')]",
                    ".//div[contains(@class, 'assistant')]",
                    # Markdown rendered content
                    ".//div[contains(@class, 'markdown')]",
                    ".//div[contains(@class, 'prose')]",
                    ".//div[contains(@class, 'rendered')]",
                    # Generic content containers (but within chat-panel)
                    ".//div[contains(@class, 'content')]",
                    ".//div[contains(@class, 'text')]",
                ]
                
                for sel in response_selectors:
                    try:
                        elements = search_context.find_elements(By.XPATH, sel)
                        visible = [e for e in elements if e.is_displayed()]
                        if visible:
                            print(f"   Found {len(visible)} elements in {context_name} with: {sel}")
                            # Get the LAST visible element (most recent response)
                            for elem in reversed(visible):
                                text = elem.text.strip()
                                text_len = len(text)
                                if text_len >= MIN_RESPONSE_LENGTH and text_len < 10000:
                                    # Skip if it's just our own message
                                    if text.lower()[:50] != user_message_lower:
                                        # Skip obvious UI elements
                                        skip_words = ["quellen", "source", "subscriptions", "erklärvideo", 
                                                      "play_arrow", "more_vert", "sticky_note", "notiz"]
                                        if not any(w in text.lower()[:100] for w in skip_words):
                                            print(f"   ✅ Found AI response ({text_len} chars): {text[:80]}...")
                                            return text
                                        else:
                                            print(f"   (Skipped - UI element: {text[:40]})")
                                    else:
                                        print(f"   (Skipped - our message)")
                                else:
                                    print(f"   (Skipped - length {text_len})")
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"   Selector error: {e}")
            
            # Last resort: find divs within chat-panel only
            print("   Trying last resort: finding divs in chat-panel...")
            try:
                # Re-find chat-panel if needed
                if not chat_panel:
                    try:
                        chat_panel = self.driver.find_element(By.TAG_NAME, "chat-panel")
                    except:
                        chat_panel = self.driver  # Fall back to full page
                
                all_divs = chat_panel.find_elements(By.TAG_NAME, "div")
                print(f"   Checking {len(all_divs)} divs in chat-panel...")
                
                for div in reversed(all_divs):
                    try:
                        if div.is_displayed():
                            text = div.text.strip()
                            text_len = len(text)
                            if text_len >= MIN_RESPONSE_LENGTH and text_len < 8000:
                                if text.lower()[:50] != user_message_lower:
                                    # Exclude obvious UI/sidebar elements
                                    skip_words = ["quellen", "source", "arrow", "menu", "settings", 
                                                  "subscriptions", "erklärvideo", "play_arrow", 
                                                  "more_vert", "sticky_note", "notiz hinzufügen",
                                                  "im web nach", "text eingeben"]
                                    if not any(x in text.lower()[:100] for x in skip_words):
                                        print(f"   ✅ Found text via last resort ({text_len} chars): {text[:80]}...")
                                        return text
                    except:
                        pass
            except Exception as e:
                print(f"   Last resort error: {e}")
            
            self.logger.warning("Could not extract response text")
            print("   ❌ Could not find any AI response text (only found short UI elements)")
            return None
            
        except Exception as e:
            self.logger.error(f"Chat message failed: {e}")
            traceback.print_exc()
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

    def upload_file_source(self, file_path: str, timeout: int = 60) -> bool:
        """Upload a file as a source to the current notebook.
        
        This method bypasses the native file dialog by sending the file path
        directly to the hidden <input type='file'> element.
        
        Args:
            file_path: Absolute path to the file to upload
            timeout: Maximum seconds to wait for upload completion
            
        Returns:
            True if upload succeeded, False otherwise
        """
        from pathlib import Path
        import os
        
        self.logger.info(f"Uploading file: {file_path}")
        print(f"📁 upload_file_source called with: {file_path}")
        
        if not self.is_driver_alive():
            print("❌ Driver not alive!")
            return False
        
        # Validate file exists and get absolute path
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            print(f"❌ File not found: {file_path}")
            return False
        
        print(f"   ✅ File exists: {file_path}")
        
        try:
            # Step 1: Click "Add source" button to open the source dialog
            print("1️⃣ Looking for Add Source button...")
            add_btn = self._find_element_multi_strategy("add_source_btn", timeout=10)
            if not add_btn:
                add_btn = self._find_clickable_by_text("Quelle hinzufügen", timeout=5)
            if not add_btn:
                add_btn = self._find_clickable_by_text("Add source", timeout=5)
            
            if add_btn:
                self._click_element_safe(add_btn)
                print("   ✅ Clicked Add Source button")
                time.sleep(2)
            else:
                self.logger.error("Could not find Add Source button")
                print("   ❌ Could not find Add Source button")
                return False
            
            # Step 2: Click "Upload from computer" option
            print("2️⃣ Looking for Upload button...")
            upload_btn = None
            
            # Try German UI first
            upload_btn = self._find_clickable_by_text("Computer hochladen", timeout=3)
            if not upload_btn:
                upload_btn = self._find_clickable_by_text("von meinem Computer", timeout=3)
            if not upload_btn:
                # Try by aria-label
                try:
                    upload_btn = self.driver.find_element(
                        By.XPATH, 
                        "//button[contains(@aria-label, 'Computer') or contains(@aria-label, 'hochladen')]"
                    )
                except:
                    pass
            if not upload_btn:
                # English fallback
                upload_btn = self._find_clickable_by_text("Upload", timeout=3)
            if not upload_btn:
                upload_btn = self._find_clickable_by_text("from computer", timeout=3)
            
            if upload_btn:
                self._click_element_safe(upload_btn)
                print("   ✅ Clicked Upload button")
                time.sleep(2)
            else:
                print("   ⚠️ Upload button not found, looking for file input directly...")
            
            # Step 3: Find the hidden file input element - THIS IS THE KEY!
            # We send the file path directly to the <input type="file"> element
            # instead of clicking the button that opens the native dialog
            print("3️⃣ Looking for file input element...")
            file_input = None
            
            # Strategies to find the file input
            file_input_selectors = [
                "input[type='file']",
                "input[accept*='pdf']",
                "input[accept*='document']",
                ".dropzone input[type='file']",
                "[class*='upload'] input[type='file']",
                "[class*='file-input']",
            ]
            
            for selector in file_input_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        # File inputs are often hidden, but we can still send_keys to them
                        if inp.get_attribute("type") == "file":
                            file_input = inp
                            print(f"   ✅ Found file input with: {selector}")
                            break
                    if file_input:
                        break
                except Exception as e:
                    continue
            
            # XPath fallback
            if not file_input:
                try:
                    file_input = self.driver.find_element(
                        By.XPATH, "//input[@type='file']"
                    )
                    print("   ✅ Found file input via XPath")
                except:
                    pass
            
            if not file_input:
                self.logger.error("Could not find file input element")
                print("   ❌ Could not find file input element!")
                print("   ℹ️ Attempting manual upload fallback...")
                return self._manual_upload_fallback(file_path, timeout)
            
            # Step 4: Make the input visible if needed (some inputs are display:none)
            try:
                self.driver.execute_script(
                    "arguments[0].style.display = 'block'; "
                    "arguments[0].style.visibility = 'visible'; "
                    "arguments[0].style.opacity = '1';",
                    file_input
                )
                print("   Made file input visible")
            except:
                pass
            
            # Step 5: Send the file path directly to the input
            print(f"4️⃣ Sending file path to input: {file_path}")
            try:
                file_input.send_keys(file_path)
                print("   ✅ File path sent to input element")
            except Exception as e:
                self.logger.error(f"Failed to send file path: {e}")
                print(f"   ❌ Failed to send file path: {e}")
                return self._manual_upload_fallback(file_path, timeout)
            
            # Step 6: Wait for upload to complete
            print("5️⃣ Waiting for upload to complete...")
            time.sleep(3)  # Initial wait for upload to start
            
            # Look for success indicators
            upload_complete = False
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check for success indicators
                try:
                    # Look for the source appearing in the list
                    sources = self.get_sources_count()
                    if sources > 0:
                        upload_complete = True
                        print(f"   ✅ Upload complete! Found {sources} source(s)")
                        break
                    
                    # Look for loading/progress indicators disappearing
                    loading = self.driver.find_elements(
                        By.XPATH, 
                        "//*[contains(@class, 'loading') or contains(@class, 'progress') or contains(@class, 'spinner')]"
                    )
                    visible_loading = [l for l in loading if l.is_displayed()]
                    
                    if not visible_loading:
                        # No loading indicators, check if source appeared
                        time.sleep(2)
                        sources = self.get_sources_count()
                        if sources > 0:
                            upload_complete = True
                            print(f"   ✅ Upload complete! Found {sources} source(s)")
                            break
                except:
                    pass
                
                time.sleep(2)
                elapsed = int(time.time() - start_time)
                print(f"   ⏳ Waiting... ({elapsed}s / {timeout}s)")
            
            if upload_complete:
                self.logger.info("File uploaded successfully")
                # Dismiss any dialogs
                self._dismiss_overlays()
                return True
            else:
                self.logger.warning("Upload may not have completed - checking sources")
                sources = self.get_sources_count()
                if sources > 0:
                    print(f"   ✅ Found {sources} source(s) - upload likely succeeded")
                    return True
                print("   ❌ Upload timeout - no sources found")
                return False
            
        except Exception as e:
            self.logger.error(f"File upload failed: {e}")
            print(f"   ❌ Exception during upload: {e}")
            traceback.print_exc()
            return self._manual_upload_fallback(file_path, timeout)

    def _manual_upload_fallback(self, file_path: str, timeout: int = 120) -> bool:
        """Fallback: prompt user to manually upload the file.
        
        Used when automated upload fails due to UI changes or restrictions.
        """
        self.logger.warning("Automated upload failed - requesting manual upload")
        print("\n" + "=" * 60)
        print("⚠️  MANUAL UPLOAD REQUIRED")
        print("=" * 60)
        print(f"\nPlease manually upload the following file:")
        print(f"📄 {file_path}")
        print(f"\nSteps:")
        print("1. Click 'Add source' in the NotebookLM window")
        print("2. Select 'Upload from computer'")
        print("3. Navigate to and select the file")
        print("4. Wait for upload to complete")
        print(f"\nWaiting up to {timeout} seconds for upload...")
        print("=" * 60 + "\n")
        
        # Wait and check for sources periodically
        start_time = time.time()
        initial_sources = self.get_sources_count()
        
        while time.time() - start_time < timeout:
            current_sources = self.get_sources_count()
            if current_sources > initial_sources:
                print(f"\n✅ Source detected! ({current_sources} sources now)")
                self.logger.info("Manual upload detected - source count increased")
                return True
            
            time.sleep(5)
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            print(f"   Checking for new sources... ({remaining}s remaining)")
        
        print("\n❌ Manual upload timeout - no new sources detected")
        return False

    def add_text_source(self, text: str, title: str = "Source") -> bool:
        """Add text content as a source to the current notebook."""
        self.logger.info(f"Adding text source: {title}")
        if not self.is_driver_alive():
            return False
        
        try:
            # Find add source button
            add_btn = self._find_element_multi_strategy("add_source_btn", timeout=10)
            if not add_btn:
                add_btn = self._find_clickable_by_text("Add source", timeout=8)
            
            if add_btn:
                self._click_element_safe(add_btn)
                time.sleep(2)
            else:
                self.logger.warning("Could not find Add source button")
                return False
            
            # Look for paste text option
            paste_btn = self._find_clickable_by_text("Paste text", timeout=8)
            if not paste_btn:
                paste_btn = self._find_clickable_by_text("Text", timeout=5)
            
            if paste_btn:
                self._click_element_safe(paste_btn)
                time.sleep(1)
            
            # Find text input
            text_input = self._find_input_field(timeout=10)
            if text_input:
                text_input.clear()
                # Enter text in chunks
                chunk_size = 5000
                for i in range(0, len(text), chunk_size):
                    text_input.send_keys(text[i:i+chunk_size])
                    time.sleep(0.1)
                
                time.sleep(1)
                text_input.send_keys(Keys.CONTROL + Keys.RETURN)
                time.sleep(3)
                self.logger.info("Successfully added text source")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to add text source: {e}")
            return False

    def get_sources_count(self) -> int:
        """Get the current number of sources in the notebook."""
        try:
            # Method 1: Look for source count text in UI (English and German)
            patterns = [
                r'(\d+)\s*source',      # English: "3 sources"
                r'(\d+)\s*Quelle',       # German: "3 Quellen"
                r'Quelle.*?(\d+)',       # German: "Quellen (3)"
            ]
            
            for pattern in patterns:
                elements = self.driver.find_elements(
                    By.XPATH, 
                    "//*[contains(text(), 'source') or contains(text(), 'Source') or "
                    "contains(text(), 'Quelle') or contains(text(), 'quelle')]"
                )
                for elem in elements:
                    text = elem.text
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
            
            # Method 2: Count actual source items in the sources panel
            # These are typically list items or cards in the sources section
            source_selectors = [
                "source-item",           # Custom element
                "[class*='source-item']",
                "[class*='source-card']",
                ".sources-panel [class*='item']",
                ".source-list > *",
            ]
            
            for selector in source_selectors:
                try:
                    items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    visible_items = [i for i in items if i.is_displayed()]
                    if visible_items:
                        return len(visible_items)
                except:
                    continue
            
            # Method 3: Check for checkboxes in sources panel (each source has one)
            try:
                checkboxes = self.driver.find_elements(
                    By.XPATH,
                    "//mat-checkbox[ancestor::*[contains(@class, 'source')]]"
                )
                visible = [c for c in checkboxes if c.is_displayed()]
                if visible:
                    return len(visible)
            except:
                pass
            
            return 0
        except Exception as e:
            self.logger.debug(f"get_sources_count error: {e}")
            return 0

    def get_notebook_title(self) -> Optional[str]:
        """Get the title of the current notebook."""
        try:
            # Try to find title in h1 or header elements
            for tag in ["h1", "h2", "[class*='title']"]:
                elements = self.driver.find_elements(By.CSS_SELECTOR, tag)
                for elem in elements:
                    text = elem.text.strip()
                    if text and len(text) > 2:
                        return text
        except:
            pass
        return None

    def close(self):
        """Clean up resources."""
        self.logger.debug("NotebookLMClient closing...")
        self.current_notebook = None
