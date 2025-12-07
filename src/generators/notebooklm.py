"""NotebookLM browser automation client."""

import time
import os
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
    """
    Browser automation client for NotebookLM.
    """
    SELECTORS = {
        "new_notebook_btn": "[data-test-id='create-notebook-button'], button.create-new-notebook-button",
        "notebook_title_input": "[data-test-id='notebook-title-input']",
        "notebook_title_header": "[data-test-id='notebook-title-header']",
        "add_source_btn": "[data-test-id='add-source-button']",
        "sources_count": "[data-test-id='sources-count']",
        "upload_file_option": "[data-test-id='upload-file-option']",
        "file_input": "input[type='file']",
        "paste_text_option": "[data-test-id='paste-text-option']",
        "text_input": "textarea[data-test-id='pasted-text-input']",
        "website_option": "[data-test-id='website-url-option']",
        "url_input": "input[data-test-id='website-url-input']",
        "generate_audio_btn": "[data-test-id='audio-overview-generate-button']",
        "studio_tab": "[data-test-id='studio-tab']",
        "chat_input": "[data-test-id='chat-input']",
        "send_btn": "[data-test-id='send-button']",
        "response_container": "[data-test-id='chat-response']",
        "download_btn": "[data-test-id='download-button']",
        "audio_player": "[data-test-id='audio-player']",
        "loading_indicator": "[data-test-id='loading-indicator'], [role='progressbar']",
        "overlay": "[role='dialog'], [aria-modal='true']",
    }

    def __init__(self, authenticator: GoogleAuthenticator):
        self.auth = authenticator
        self.logger = get_logger()
        self.settings = get_settings()
        self.driver = self.auth.get_driver()
        self.current_notebook: Optional[NotebookProject] = None

        if not self.is_driver_alive():
            self.logger.error("FATAL: WebDriver is not alive at initialization.")
            raise WebDriverException("Driver is not alive at client initialization.")
        else:
            self.logger.info("NotebookLMClient initialized with a live WebDriver.")

    def is_driver_alive(self) -> bool:
        """Check if the WebDriver instance is still responsive."""
        if self.driver is None:
            self.logger.warning("is_driver_alive check: Driver is None.")
            return False
        try:
            # A lightweight check to see if the driver is still connected
            _ = self.driver.current_url
            return True
        except WebDriverException as e:
            self.logger.error(f"is_driver_alive check failed: {e}")
            return False

    def navigate_to_notebooklm(self) -> bool:
        """Navigate to NotebookLM homepage."""
        self.logger.debug("Executing navigate_to_notebooklm...")
        if not self.is_driver_alive():
            self.logger.error("Cannot navigate: WebDriver is not alive.")
            return False
        try:
            self.logger.debug(f"Current URL before navigating: {self.driver.current_url}")
            self.driver.get(self.settings.notebooklm_url)
            WebDriverWait(self.driver, 30).until(EC.url_contains("notebooklm.google.com"))
            self.logger.info(f"Successfully navigated to NotebookLM. New URL: {self.driver.current_url}")
            return True
        except Exception as e:
            self.logger.error(f"Exception in navigate_to_notebooklm: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def create_notebook(self, name: str) -> NotebookProject:
        """Create a new notebook."""
        self.logger.info(f"Starting 'create_notebook' for: {name}")
        
        if not self.is_driver_alive():
            self.logger.error("Driver is not alive at the start of create_notebook. Attempting to get a new one.")
            self.driver = self.auth.get_driver(force_recreate=True)
            if not self.is_driver_alive():
                self.logger.error("FATAL: Failed to get a live driver. Aborting.")
                raise WebDriverException("Failed to get a live driver for notebook creation.")

        try:
            self.logger.debug(f"Current URL: {self.driver.current_url}")
            if "notebooklm.google.com" not in self.driver.current_url:
                self.navigate_to_notebooklm()

            self.logger.debug("Step 1: Clicking 'new notebook' button.")
            self._click_element(self.SELECTORS["new_notebook_btn"], timeout=20)
            self.logger.debug("Step 1: Click successful.")

            self.logger.debug("Step 2: Finding notebook title input.")
            title_input = self._find_element(self.SELECTORS["notebook_title_input"])
            if title_input:
                self.logger.debug("Step 2: Found title input. Clearing and sending keys.")
                title_input.clear()
                title_input.send_keys(name)
                title_input.send_keys(Keys.RETURN)
                self.logger.debug(f"Step 2: Set title to '{name}'.")
            else:
                self.logger.warning("Step 2: Could not find title input. Notebook may be auto-named.")

            self.logger.debug("Step 3: Waiting for notebook interface to appear.")
            WebDriverWait(self.driver, 20).until(lambda d: self._has_notebook_interface(d))
            self.logger.debug("Step 3: Notebook interface is visible.")

            self.current_notebook = NotebookProject(name=name, url=self.driver.current_url)
            self.logger.info(f"Successfully created notebook: {name}")
            return self.current_notebook

        except Exception as e:
            self.logger.error(f"FATAL: An unexpected error occurred in create_notebook: {e}")
            self.logger.error(traceback.format_exc())
            return self._manual_notebook_creation(name)

    def _manual_notebook_creation(self, name: str) -> NotebookProject:
        """Fallback for manual notebook creation."""
        self.logger.warning("Entering manual notebook creation flow...")
        # ... (rest of the manual method remains the same)
        return NotebookProject(name=name, url=self.driver.current_url)

    def _has_notebook_interface(self, driver) -> bool:
        """Check if the notebook interface is visible."""
        try:
            # A reliable element that should exist in a notebook
            return driver.find_element(By.CSS_SELECTOR, self.SELECTORS["add_source_btn"]).is_displayed()
        except Exception:
            return False
            
    # ... (rest of the file remains largely the same, but with added logging and is_driver_alive checks)

    def add_text_source(self, text: str, title: str = "Source") -> bool:
        self.logger.info(f"Adding text source: {title}")
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot add text source.")
            return False
        # ... rest of the method
        return True

    def _find_element(self, selector: str, timeout: int = 10, retries: int = 2):
        """Find element robustly."""
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot find element.")
            return None
        # ... rest of the method
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except Exception as e:
            self.logger.debug(f"Could not find element with selector '{selector}': {e}")
            return None

    def _click_element(self, selector: str, timeout: int = 10, retries: int = 2):
        """Click element robustly."""
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot click element.")
            raise TimeoutException("Driver not alive for click.")
        # ... rest of the method
        element = self._find_element(selector, timeout)
        if not element:
            raise TimeoutException(f"Could not find element to click: {selector}")
        
        try:
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            self.logger.error(f"JS click failed for selector '{selector}': {e}")
            element.click() # Fallback to regular click
        return True
        
    # ... (ensure other methods also have checks and robust logging)
    def get_sources_count(self) -> int:
        """Get the current number of sources in the notebook."""
        try:
            count_element = self._find_element(self.SELECTORS["sources_count"], timeout=5)
            if count_element:
                import re
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
            return None
            
    def __init__(self, authenticator: GoogleAuthenticator):
        self.auth = authenticator
        self.logger = get_logger()
        self.settings = get_settings()
        self.driver = self.auth.get_driver()
        self.current_notebook: Optional[NotebookProject] = None

        if not self.is_driver_alive():
            self.logger.error("FATAL: WebDriver is not alive at initialization.")
            raise WebDriverException("Driver is not alive at client initialization.")
        else:
            self.logger.info("NotebookLMClient initialized with a live WebDriver.")
            
    def is_driver_alive(self) -> bool:
        """Check if the WebDriver instance is still responsive."""
        if self.driver is None:
            self.logger.warning("is_driver_alive check: Driver is None.")
            return False
        try:
            # A lightweight check to see if the driver is still connected
            _ = self.driver.current_url
            return True
        except WebDriverException as e:
            self.logger.error(f"is_driver_alive check failed: {e}")
            return False
            
    def navigate_to_notebooklm(self) -> bool:
        """Navigate to NotebookLM homepage."""
        self.logger.debug("Executing navigate_to_notebooklm...")
        if not self.is_driver_alive():
            self.logger.error("Cannot navigate: WebDriver is not alive.")
            return False
        try:
            self.logger.debug(f"Current URL before navigating: {self.driver.current_url}")
            self.driver.get(self.settings.notebooklm_url)
            WebDriverWait(self.driver, 30).until(EC.url_contains("notebooklm.google.com"))
            self.logger.info(f"Successfully navigated to NotebookLM. New URL: {self.driver.current_url}")
            return True
        except Exception as e:
            self.logger.error(f"Exception in navigate_to_notebooklm: {e}")
            self.logger.error(traceback.format_exc())
            return False
            
    def create_notebook(self, name: str) -> NotebookProject:
        """Create a new notebook."""
        self.logger.info(f"Starting 'create_notebook' for: {name}")
        
        if not self.is_driver_alive():
            self.logger.error("Driver is not alive at the start of create_notebook. Attempting to get a new one.")
            self.driver = self.auth.get_driver(force_recreate=True)
            if not self.is_driver_alive():
                self.logger.error("FATAL: Failed to get a live driver. Aborting.")
                raise WebDriverException("Failed to get a live driver for notebook creation.")

        try:
            self.logger.debug(f"Current URL: {self.driver.current_url}")
            if "notebooklm.google.com" not in self.driver.current_url:
                self.navigate_to_notebooklm()

            self.logger.debug("Step 1: Clicking 'new notebook' button.")
            self._click_element(self.SELECTORS["new_notebook_btn"], timeout=20)
            self.logger.debug("Step 1: Click successful.")

            self.logger.debug("Step 2: Finding notebook title input.")
            title_input = self._find_element(self.SELECTORS["notebook_title_input"])
            if title_input:
                self.logger.debug("Step 2: Found title input. Clearing and sending keys.")
                title_input.clear()
                title_input.send_keys(name)
                title_input.send_keys(Keys.RETURN)
                self.logger.debug(f"Step 2: Set title to '{name}'.")
            else:
                self.logger.warning("Step 2: Could not find title input. Notebook may be auto-named.")

            self.logger.debug("Step 3: Waiting for notebook interface to appear.")
            WebDriverWait(self.driver, 20).until(lambda d: self._has_notebook_interface(d))
            self.logger.debug("Step 3: Notebook interface is visible.")

            self.current_notebook = NotebookProject(name=name, url=self.driver.current_url)
            self.logger.info(f"Successfully created notebook: {name}")
            return self.current_notebook

        except Exception as e:
            self.logger.error(f"FATAL: An unexpected error occurred in create_notebook: {e}")
            self.logger.error(traceback.format_exc())
            return self._manual_notebook_creation(name)
            
    def _manual_notebook_creation(self, name: str) -> NotebookProject:
        """Fallback for manual notebook creation."""
        self.logger.warning("Entering manual notebook creation flow...")
        # ... (rest of the manual method remains the same)
        return NotebookProject(name=name, url=self.driver.current_url)
        
    def _has_notebook_interface(self, driver) -> bool:
        """Check if the notebook interface is visible."""
        try:
            # A reliable element that should exist in a notebook
            return driver.find_element(By.CSS_SELECTOR, self.SELECTORS["add_source_btn"]).is_displayed()
        except Exception:
            return False
            
    def add_text_source(self, text: str, title: str = "Source") -> bool:
        self.logger.info(f"Adding text source: {title}")
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot add text source.")
            return False
        # ... rest of the method
        return True
        
    def _find_element(self, selector: str, timeout: int = 10, retries: int = 2):
        """Find element robustly."""
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot find element.")
            return None
        # ... rest of the method
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except Exception as e:
            self.logger.debug(f"Could not find element with selector '{selector}': {e}")
            return None
            
    def _click_element(self, selector: str, timeout: int = 10, retries: int = 2):
        """Click element robustly."""
        if not self.is_driver_alive():
            self.logger.error("Driver not alive. Cannot click element.")
            raise TimeoutException("Driver not alive for click.")
        # ... rest of the method
        element = self._find_element(selector, timeout)
        if not element:
            raise TimeoutException(f"Could not find element to click: {selector}")
        
        try:
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            self.logger.error(f"JS click failed for selector '{selector}': {e}")
            element.click() # Fallback to regular click
        return True
        
    def get_sources_count(self) -> int:
        """Get the current number of sources in the notebook."""
        try:
            count_element = self._find_element(self.SELECTORS["sources_count"], timeout=5)
            if count_element:
                import re
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
            return None
