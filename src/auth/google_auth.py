"""Google authentication for NotebookLM and Gemini."""

import time
import pickle
import traceback
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

try:
    import undetected_chromedriver as uc
    HAS_UNDETECTED = True
except ImportError:
    HAS_UNDETECTED = False

from webdriver_manager.chrome import ChromeDriverManager

from ..utils.logger import get_logger
from ..config.settings import get_settings


class GoogleAuthenticator:
    """
    Handles Google account authentication for NotebookLM and Gemini.

    Uses Selenium for browser automation to log into Google services.
    Supports both regular Chrome and undetected-chromedriver to bypass
    bot detection.
    """

    COOKIES_FILE = "google_cookies.pkl"

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = False,
        cookies_dir: Optional[Path] = None
    ):
        self.email = email
        self.password = password
        self.headless = headless
        self.cookies_dir = cookies_dir or Path.home() / ".notebook_lm_gen"
        self.cookies_dir.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger()
        self.settings = get_settings()
        self.driver: Optional[webdriver.Chrome] = None
        
        # Persistent profile directory to keep login saved
        self.profile_dir = Path.home() / ".nlm_chrome_profile"
        self.profile_dir.mkdir(exist_ok=True)

    def _create_driver(self) -> Optional[webdriver.Chrome]:
        """Create and configure the Chrome WebDriver."""
        self.logger.info("Creating new WebDriver instance...")
        try:
            # Use standard Selenium with persistent profile (more stable than undetected-chromedriver)
            # The persistent profile keeps Google login saved between sessions
            self.logger.info("Using standard Selenium with persistent Chrome profile.")
            self.logger.info(f"Profile directory: {self.profile_dir}")
            
            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(f"--window-size={self.settings.window_size}")
            
            # Use persistent profile to keep login saved
            options.add_argument(f"--user-data-dir={self.profile_dir}")
            
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                self.logger.error(f"Failed to install/use ChromeDriverManager: {e}")
                self.logger.error("Please ensure Chrome is installed.")
                return None

            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            driver.set_page_load_timeout(self.settings.page_load_timeout)
            self.logger.info("WebDriver instance created successfully.")
            return driver
        except Exception as e:
            self.logger.error(f"FATAL: Failed to create WebDriver: {e}")
            self.logger.error(traceback.format_exc())
            return None

    def get_driver(self, force_recreate: bool = False) -> Optional[webdriver.Chrome]:
        """Get the WebDriver instance, creating it if necessary."""
        if self.driver and not force_recreate:
            # Check if driver is still alive
            try:
                _ = self.driver.window_handles
                self.logger.debug("Returning existing WebDriver instance.")
                return self.driver
            except WebDriverException:
                self.logger.warning("WebDriver is not responding. Creating a new one.")
                self.driver = None

        if self.driver and force_recreate:
            self.logger.info("Forcing re-creation of WebDriver instance.")
            self.close()

        self.driver = self._create_driver()
        return self.driver

    def _save_cookies(self):
        """Save cookies to file for session persistence."""
        if not self.driver:
            return
        cookies_path = self.cookies_dir / self.COOKIES_FILE
        try:
            with open(cookies_path, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            self.logger.debug(f"Saved cookies to {cookies_path}")
        except Exception as e:
            self.logger.error(f"Failed to save cookies: {e}")

    def _load_cookies(self) -> bool:
        """Load cookies from file if available."""
        cookies_path = self.cookies_dir / self.COOKIES_FILE
        if not cookies_path.exists():
            self.logger.debug("Cookies file not found.")
            return False

        if not self.driver:
            self.logger.error("Cannot load cookies, driver is not initialized.")
            return False

        try:
            with open(cookies_path, "rb") as f:
                cookies = pickle.load(f)

            self.logger.debug("Navigating to google.com to set cookies.")
            self.driver.get("https://www.google.com")
            time.sleep(1)

            for cookie in cookies:
                self.driver.add_cookie(cookie)

            self.logger.info("Loaded cookies from file.")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to load cookies: {e}")
            return False

    def login_google(self) -> bool:
        """
        Log into Google account, handling manual login if necessary.
        """
        self.logger.info("Starting Google authentication process...")
        try:
            driver = self.get_driver()
            if not driver:
                self.logger.error("Failed to get WebDriver instance. Aborting login.")
                return False

            if self._load_cookies():
                self.logger.debug("Checking login status with loaded cookies...")
                driver.get("https://myaccount.google.com/u/0/")
                time.sleep(2)
                if "signin" not in driver.current_url:
                    self.logger.info("Successfully logged in using saved session.")
                    return True
                self.logger.info("Cookie session is invalid or expired. Proceeding with manual login.")

            self.logger.warning("=" * 50)
            self.logger.warning("MANUAL LOGIN REQUIRED")
            self.logger.warning("Please log into your Google account in the browser window.")
            self.logger.warning("If you see a 'Welcome' screen, please dismiss it.")
            self.logger.warning("Waiting up to 3 minutes for login...")
            self.logger.warning("=" * 50)

            driver.get("https://accounts.google.com/signin")

            try:
                WebDriverWait(driver, 180).until(
                    lambda d: "myaccount.google.com" in d.current_url or "notebooklm.google.com" in d.current_url
                )
            except TimeoutException:
                self.logger.error("Login timed out after 3 minutes. Please check the browser window.")
                return False

            self.logger.info("Login appears successful. Verifying session...")
            time.sleep(2)

            if self._is_logged_in():
                self._save_cookies()
                self.logger.info("Successfully verified Google login.")
                return True
            else:
                self.logger.error("Login failed. Could not verify logged-in state after manual login.")
                return False

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during Google login: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def _is_logged_in(self) -> bool:
        """Check if currently logged into Google."""
        if not self.driver:
            return False
        try:
            self.logger.debug("Navigating to myaccount.google.com to verify login status.")
            self.driver.get("https://myaccount.google.com/u/0/")
            time.sleep(2)
            
            # If we are redirected to signin, we are not logged in.
            if "signin" in self.driver.current_url.lower():
                self.logger.debug("Redirected to signin page. Not logged in.")
                return False

            # Check for a known element that only appears when logged in.
            try:
                avatar = self.driver.find_element(By.CSS_SELECTOR, "a[href^='https://accounts.google.com/SignOutOptions']")
                if avatar.is_displayed():
                    self.logger.debug("Found sign-out link, assuming logged in.")
                    return True
            except NoSuchElementException:
                self.logger.debug("Could not find sign-out link.")

            self.logger.warning("Could not definitively verify login status, but not on signin page.")
            return True # Assume logged in if not on a signin page
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            return False

    def navigate_to_notebooklm(self) -> bool:
        """Navigate to NotebookLM."""
        self.logger.debug("Navigating to NotebookLM...")
        try:
            driver = self.get_driver()
            if not driver:
                return False
            driver.get(self.settings.notebooklm_url)
            WebDriverWait(driver, 30).until(EC.url_contains("notebooklm.google.com"))
            self.logger.info("Successfully navigated to NotebookLM.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to NotebookLM: {e}")
            self.logger.error(traceback.format_exc())
            return False

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

    def close(self):
        """Close the browser and cleanup."""
        if self.driver:
            self.logger.debug("Closing WebDriver instance.")
            try:
                self._save_cookies()
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
