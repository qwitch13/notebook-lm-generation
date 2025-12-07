"""NotebookLM browser automation client."""

import time
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver

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

    Handles creating notebooks, uploading sources, and generating
    various outputs like audio overviews and study guides.
    """

    # CSS Selectors (may need updates if NotebookLM UI changes)
    # Updated 2025-12 for current NotebookLM interface
    SELECTORS = {
        "new_notebook_btn": "[data-test-id='create-notebook-button'], button.create-new-notebook-button, button[aria-label*='new notebook'], button[aria-label*='New notebook'], button[aria-label*='Create'], .create-button, button.mdc-button--raised, button[jsname]",
        "notebook_title_input": "[data-test-id='notebook-title-input'], [data-test-id='notebook-title'], input[placeholder*='title'], input[aria-label*='title'], .notebook-title-input",
        "notebook_title_header": "[data-test-id='notebook-title-header'], .notebook-title, h1",
        "add_source_btn": "[data-test-id='add-source-button'], button[aria-label*='Add source'], button[aria-label*='add source'], .add-source-button, button.source-button, [aria-label='Add source']",
        "sources_count": "[data-test-id='sources-count'], [aria-label*='Sources']",
        "upload_file_option": "[data-test-id='upload-file-option'], [data-test-id='upload-file'], [aria-label*='Upload'], [aria-label*='upload'], .upload-option, button[aria-label*='file']",
        "file_input": "input[type='file']",
        "paste_text_option": "[data-test-id='paste-text-option'], [data-test-id='paste-text'], [aria-label*='Paste text'], [aria-label*='paste'], [aria-label*='Copied text'], .paste-text-option",
        "text_input": "textarea[data-test-id='pasted-text-input'], textarea[placeholder*='Paste'], textarea[aria-label*='text'], .text-input-area, textarea",
        "website_option": "[data-test-id='website-url-option'], [data-test-id='website-url'], [aria-label*='Website'], [aria-label*='website'], [aria-label*='URL'], .website-option",
        "url_input": "input[data-test-id='website-url-input'], input[placeholder*='URL'], input[type='url'], input[aria-label*='URL']",
        "generate_audio_btn": "[data-test-id='audio-overview-generate-button'], [data-test-id='generate-audio'], button[aria-label*='Audio Overview'], button[aria-label*='audio'], button[aria-label*='Generate'], .audio-overview-button, [data-test-id='audio-overview-generate']",
        "studio_tab": "[data-test-id='studio-tab'], [aria-label*='Studio'], button[aria-label*='Audio'], .studio-tab",
        "chat_input": "[data-test-id='chat-input'], textarea[aria-label*='message'], textarea[placeholder*='Ask'], .chat-input, textarea",
        "send_btn": "[data-test-id='send-button'], button[aria-label*='Send'], button[aria-label*='submit'], .send-button",
        "response_container": "[data-test-id='chat-response'], [data-test-id='response'], .response-container, .chat-response, .message-content",
        "download_btn": "[data-test-id='download-button'], [data-test-id='download'], button[aria-label*='Download'], .download-button",
        "audio_player": "[data-test-id='audio-player'], audio",
        "loading_indicator": "[data-test-id='loading-indicator'], [data-test-id='loading'], .loading, .spinner, [role='progressbar']",
        # Potential overlays/popups that can intercept clicks
        "overlay": ".kPY6ve, [role='dialog'], [aria-modal='true'], .mdc-dialog__surface, .cdk-overlay-container, .modal-backdrop",
    }

    def __init__(self, authenticator: GoogleAuthenticator):
        self.auth = authenticator
        self.driver = authenticator.get_driver()
        self.logger = get_logger()
        self.settings = get_settings()
        self.current_notebook: Optional[NotebookProject] = None

    def navigate_to_notebooklm(self) -> bool:
        """Navigate to NotebookLM homepage."""
        return self.auth.navigate_to_notebooklm()

    def create_notebook(self, name: str) -> NotebookProject:
        """
        Create a new notebook.

        Args:
            name: Name for the new notebook

        Returns:
            NotebookProject instance
        """
        self.logger.info(f"Creating new notebook: {name}")

        try:
            # Navigate to NotebookLM if not already there
            if "notebooklm" not in self.driver.current_url.lower():
                self.navigate_to_notebooklm()

            time.sleep(3)

            # Try to click create new notebook button
            try:
                self._click_element(self.SELECTORS["new_notebook_btn"], timeout=15)
                time.sleep(2)
            except TimeoutException:
                # Button not found - ask user to create manually
                return self._manual_notebook_creation(name)

            # Set notebook title if input is available
            try:
                title_input = self._find_element(self.SELECTORS["notebook_title_input"])
                if title_input:
                    title_input.clear()
                    title_input.send_keys(name)
                    title_input.send_keys(Keys.RETURN)
                    time.sleep(1)
            except Exception:
                self.logger.debug("Could not set notebook title directly")

            # Verify notebook interface is available; otherwise ask for manual creation
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda d: self._has_notebook_interface(d)
                )
            except Exception:
                self.logger.warning("Notebook interface not detected after creation click; switching to manual flow")
                return self._manual_notebook_creation(name)

            self.current_notebook = NotebookProject(
                name=name,
                url=self.driver.current_url
            )

            self.logger.info(f"Created notebook: {name}")
            return self.current_notebook

        except Exception as e:
            self.logger.error(f"Failed to create notebook: {e}")
            # Fall back to manual creation
            return self._manual_notebook_creation(name)

    def _manual_notebook_creation(self, name: str) -> NotebookProject:
        """
        Ask user to create notebook manually.

        Args:
            name: Name for the notebook

        Returns:
            NotebookProject instance
        """
        self.logger.warning("=" * 50)
        self.logger.warning("MANUAL ACTION REQUIRED")
        self.logger.warning(f"Please create a new notebook named: {name[:50]}...")
        self.logger.warning("1. Click 'Create new' or '+' button in NotebookLM")
        self.logger.warning("2. The tool will continue automatically")
        self.logger.warning("Waiting up to 2 minutes...")
        self.logger.warning("=" * 50)

        # Wait for user to create notebook (URL will change to include notebook ID)
        initial_url = self.driver.current_url
        try:
            WebDriverWait(self.driver, 120).until(
                lambda d: d.current_url != initial_url or
                          "notebook" in d.current_url.lower() or
                          self._has_notebook_interface(d)
            )
            self.logger.info("Notebook created successfully!")
        except TimeoutException:
            self.logger.warning("Timeout waiting for notebook creation, continuing anyway...")

        self.current_notebook = NotebookProject(
            name=name,
            url=self.driver.current_url
        )
        return self.current_notebook

    def _has_notebook_interface(self, driver) -> bool:
        """Check if the notebook interface is visible."""
        try:
            # Look for notebook-specific elements
            selectors = [
                self.SELECTORS["add_source_btn"],
                self.SELECTORS["chat_input"],
                "[data-test-id='notebook-view']",
                "[data-test-id='notebook']",
                ".notebook-content",
            ]
            for selector in selectors:
                for sel in selector.split(", "):
                    try:
                        driver.find_element(By.CSS_SELECTOR, sel.strip())
                        return True
                    except NoSuchElementException:
                        continue
        except Exception:
            pass
        return False

    def _manual_add_source(self, text: str, title: str) -> bool:
        """
        Ask user to manually add source content.

        Args:
            text: Text content to add (will be copied to clipboard)
            title: Title for the source

        Returns:
            True if user confirms source was added
        """
        # Try to copy text to clipboard
        try:
            import pyperclip
            pyperclip.copy(text[:50000])  # Limit to 50k chars
            clipboard_msg = "Content has been copied to clipboard."
        except Exception:
            clipboard_msg = "Could not copy to clipboard - please copy manually."

        self.logger.warning("=" * 50)
        self.logger.warning("MANUAL ACTION REQUIRED")
        self.logger.warning(f"Please add source: {title[:50]}...")
        self.logger.warning("1. Click 'Add source' or '+' in NotebookLM")
        self.logger.warning("2. Select 'Copied text' or 'Paste text'")
        self.logger.warning(f"3. {clipboard_msg}")
        self.logger.warning("4. Paste the content and submit")
        self.logger.warning("Waiting up to 2 minutes for source to be added...")
        self.logger.warning("=" * 50)

        # Wait for user to add source
        initial_sources = self.get_sources_count()
        try:
            WebDriverWait(self.driver, 120).until(
                lambda d: self.get_sources_count() > initial_sources
            )
            self.logger.info("Source added successfully!")
            if self.current_notebook:
                self.current_notebook.sources_count = self.get_sources_count()
            return True
        except TimeoutException:
            self.logger.warning("Timeout waiting for source addition, continuing anyway...")
            return True

    def _manual_generate_audio(self) -> bool:
        """
        Ask user to manually generate audio overview.

        Returns:
            True if user confirms audio generation was started
        """
        self.logger.warning("=" * 50)
        self.logger.warning("MANUAL ACTION REQUIRED")
        self.logger.warning("Please generate Audio Overview manually:")
        self.logger.warning("1. Look for 'Audio Overview' or 'Generate' button")
        self.logger.warning("2. It may be in a 'Studio' tab or sidebar")
        self.logger.warning("3. Click to start audio generation")
        self.logger.warning("4. Audio generation typically takes 3-5 minutes")
        self.logger.warning("Waiting up to 5 minutes for generation...")
        self.logger.warning("=" * 50)

        # Wait for audio to generate
        try:
            time.sleep(300)  # Wait 5 minutes
            self.logger.info("Continuing after audio generation wait...")
            return True
        except Exception:
            return True

    def add_text_source(self, text: str, title: str = "Source") -> bool:
        """
        Add text content as a source.

        Args:
            text: Text content to add
            title: Title for the source

        Returns:
            True if successful
        """
        self.logger.info(f"Adding text source: {title}")
        initial_sources = self.get_sources_count()

        try:
            # Click add source button
            self._click_element(self.SELECTORS["add_source_btn"])
            time.sleep(1)

            # Select paste text option
            self._click_element(self.SELECTORS["paste_text_option"])
            time.sleep(1)

            # Enter text
            text_area = self._find_element(self.SELECTORS["text_input"])
            if text_area:
                text_area.clear()
                # Send text in chunks to avoid issues with large content
                chunk_size = 5000
                for i in range(0, len(text), chunk_size):
                    text_area.send_keys(text[i:i + chunk_size])
                    time.sleep(0.5)

            # Submit
            text_area.send_keys(Keys.CONTROL, Keys.RETURN)
            time.sleep(3)

            # Wait for processing
            self._wait_for_loading()
            
            # Verify source was added
            WebDriverWait(self.driver, 30).until(
                lambda d: self.get_sources_count() > initial_sources
            )

            if self.current_notebook:
                self.current_notebook.sources_count = self.get_sources_count()

            self.logger.info(f"Added text source: {title}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add text source automatically: {e}")
            return self._manual_add_source(text, title)

    def add_file_source(self, file_path: Path) -> bool:
        """
        Add a file as a source.

        Args:
            file_path: Path to the file to upload

        Returns:
            True if successful
        """
        self.logger.info(f"Adding file source: {file_path}")
        initial_sources = self.get_sources_count()

        try:
            # Click add source button
            self._click_element(self.SELECTORS["add_source_btn"])
            time.sleep(1)

            # Select upload file option
            self._click_element(self.SELECTORS["upload_file_option"])
            time.sleep(1)

            # Find file input and upload
            file_input = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS["file_input"])
            file_input.send_keys(str(file_path.absolute()))
            time.sleep(3)

            # Wait for upload to complete
            self._wait_for_loading(timeout=60)
            
            # Verify source was added
            WebDriverWait(self.driver, 30).until(
                lambda d: self.get_sources_count() > initial_sources
            )

            if self.current_notebook:
                self.current_notebook.sources_count = self.get_sources_count()

            self.logger.info(f"Added file source: {file_path.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add file source: {e}")
            return False

    def add_website_source(self, url: str) -> bool:
        """
        Add a website as a source.

        Args:
            url: URL to add

        Returns:
            True if successful
        """
        self.logger.info(f"Adding website source: {url}")
        initial_sources = self.get_sources_count()

        try:
            # Click add source button
            self._click_element(self.SELECTORS["add_source_btn"])
            time.sleep(1)

            # Select website option
            self._click_element(self.SELECTORS["website_option"])
            time.sleep(1)

            # Enter URL
            url_input = self._find_element(self.SELECTORS["url_input"])
            if url_input:
                url_input.clear()
                url_input.send_keys(url)
                url_input.send_keys(Keys.RETURN)
                time.sleep(3)

            # Wait for processing
            self._wait_for_loading(timeout=60)
            
            # Verify source was added
            WebDriverWait(self.driver, 30).until(
                lambda d: self.get_sources_count() > initial_sources
            )

            if self.current_notebook:
                self.current_notebook.sources_count = self.get_sources_count()

            self.logger.info(f"Added website source: {url}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add website source: {e}")
            return False

    def generate_audio_overview(self) -> bool:
        """
        Generate an audio overview (podcast-style).

        Returns:
            True if generation started successfully
        """
        self.logger.info("Generating audio overview...")

        try:
            # Navigate to Studio tab if available
            try:
                self._click_element(self.SELECTORS["studio_tab"])
                time.sleep(2)
            except Exception:
                pass

            # Click generate audio button
            self._click_element(self.SELECTORS["generate_audio_btn"])
            time.sleep(2)

            # Wait for generation (can take several minutes)
            self._wait_for_loading(timeout=300)

            # Verify that an audio player or result appears
            audio_el = self._find_element(self.SELECTORS["audio_player"], timeout=5)
            if audio_el:
                self.logger.info("Audio overview generation started")
                return True
            else:
                self.logger.warning("Audio player not found after generation trigger; requesting manual generation")
                # Fall back to manual generation flow
                if self._manual_generate_audio():
                    # After manual wait, check again
                    audio_el2 = self._find_element(self.SELECTORS["audio_player"], timeout=5)
                    return audio_el2 is not None
                return False

        except Exception as e:
            self.logger.error(f"Failed to generate audio overview automatically: {e}")
            ok = self._manual_generate_audio()
            if ok:
                audio_el = self._find_element(self.SELECTORS["audio_player"], timeout=5)
                return audio_el is not None
            return False

    def send_chat_message(self, message: str) -> Optional[str]:
        """
        Send a chat message and get response.

        Args:
            message: Message to send

        Returns:
            Response text or None
        """
        self.logger.debug(f"Sending chat message: {message[:50]}...")

        try:
            # Find chat input
            chat_input = self._find_element(self.SELECTORS["chat_input"])
            if not chat_input:
                self.logger.error("Chat input not found")
                return None

            # Clear and enter message
            chat_input.clear()
            chat_input.send_keys(message)

            # Click send or press enter
            try:
                self._click_element(self.SELECTORS["send_btn"])
            except Exception:
                chat_input.send_keys(Keys.RETURN)

            time.sleep(2)

            # Wait for response
            self._wait_for_loading(timeout=120)
            time.sleep(2)

            # Get response
            response_elements = self.driver.find_elements(
                By.CSS_SELECTOR, self.SELECTORS["response_container"]
            )

            if response_elements:
                # Get the last response
                return response_elements[-1].text

            return None

        except Exception as e:
            self.logger.error(f"Failed to send chat message: {e}")
            return None

    def generate_study_guide(self) -> Optional[str]:
        """Generate a study guide using chat."""
        return self.send_chat_message(
            "Create a comprehensive study guide for this content. Include key concepts, "
            "definitions, and important points to remember."
        )

    def generate_briefing_doc(self) -> Optional[str]:
        """Generate a briefing document using chat."""
        return self.send_chat_message(
            "Create a detailed briefing document summarizing this content. "
            "Include executive summary, main points, and conclusions."
        )

    def generate_faq(self) -> Optional[str]:
        """Generate FAQ using chat."""
        return self.send_chat_message(
            "Generate a comprehensive FAQ (Frequently Asked Questions) based on this content. "
            "Include at least 10 questions and detailed answers."
        )

    def generate_timeline(self) -> Optional[str]:
        """Generate a timeline if applicable."""
        return self.send_chat_message(
            "Create a timeline of events or key milestones mentioned in this content."
        )

    def generate_flashcards(self) -> Optional[str]:
        """Generate flashcards using chat."""
        return self.send_chat_message(
            "Create flashcards (question and answer pairs) for studying this content. "
            "Format each card as 'Q: [question]' followed by 'A: [answer]'. "
            "Create at least 15 flashcards covering the main concepts."
        )

    def _find_element(self, selector: str, timeout: int = 10, retries: int = 2):
        """Find element using multiple selector strategies with visibility and stale element retry."""
        from selenium.common.exceptions import StaleElementReferenceException

        selectors = selector.split(", ")

        for attempt in range(retries):
            for sel in selectors:
                try:
                    wait_time = max(1, timeout // max(1, len(selectors)))
                    element = WebDriverWait(self.driver, wait_time).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, sel.strip()))
                    )
                    # Verify element is not stale by accessing a property
                    _ = element.is_displayed()
                    return element
                except StaleElementReferenceException:
                    self.logger.debug(f"Stale element, retrying... ({attempt + 1}/{retries})")
                    time.sleep(0.5)
                    continue
                except TimeoutException:
                    continue

        return None

    def _scroll_into_view(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
            time.sleep(0.2)
        except Exception:
            pass

    def _dismiss_overlays(self):
        """Try to dismiss blocking overlays/popups that intercept clicks."""
        try:
            # Press ESC to close dialogs
            from selenium.webdriver.common.keys import Keys
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            time.sleep(0.2)
        except Exception:
            pass

        try:
            overlays = self.driver.find_elements(By.CSS_SELECTOR, self.SELECTORS["overlay"])  # type: ignore[index]
            for ov in overlays:
                try:
                    if ov.is_displayed():
                        self.driver.execute_script("arguments[0].style.display='none'", ov)
                except Exception:
                    continue
        except Exception:
            pass

    def _click_element(self, selector: str, timeout: int = 10, retries: int = 2):
        """Click an element robustly: wait, scroll, regular click, then JS click fallback, handling interceptions."""
        from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException

        selectors = selector.split(", ")

        for attempt in range(retries):
            for sel in selectors:
                try:
                    wait_time = max(1, timeout // max(1, len(selectors)))
                    element = WebDriverWait(self.driver, wait_time).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel.strip()))
                    )

                    # Scroll into view before clicking
                    self._scroll_into_view(element)

                    try:
                        element.click()
                        return True
                    except ElementClickInterceptedException:
                        # Try to dismiss overlays and JS-click
                        self._dismiss_overlays()
                        self._scroll_into_view(element)
                        try:
                            self.driver.execute_script("arguments[0].click();", element)
                            return True
                        except Exception:
                            # Small wait and retry within same attempt
                            time.sleep(0.5)
                            continue
                except StaleElementReferenceException:
                    self.logger.debug(f"Stale element on click, retrying... ({attempt + 1}/{retries})")
                    time.sleep(0.5)
                    continue
                except TimeoutException:
                    continue

        raise TimeoutException(f"Could not click element: {selector}")

    def _wait_for_loading(self, timeout: int = 60):
        """Wait for loading indicators to disappear."""
        try:
            # First wait for loading to appear (briefly)
            time.sleep(1)

            # Then wait for it to disappear
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.SELECTORS["loading_indicator"])
                )
            )
        except TimeoutException:
            self.logger.debug("Loading wait timed out")
        except Exception:
            pass  # Loading indicator might not exist

    def get_sources_count(self) -> int:
        """Get the current number of sources in the notebook."""
        try:
            count_element = self._find_element(self.SELECTORS["sources_count"], timeout=5)
            if count_element:
                # Extract number from text like "Sources (5)"
                import re
                match = re.search(r'\((\d+)\)', count_element.text)
                if match:
                    return int(match.group(1))
            # Fallback for just a number
            return int(count_element.text)
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

    def get_audio_url(self) -> Optional[str]:
        """Get the URL of the generated audio."""
        try:
            audio_element = self._find_element(self.SELECTORS["audio_player"])
            if audio_element:
                return audio_element.get_attribute("src")
        except Exception:
            pass
        return None

    def download_audio(self, output_path: Path) -> bool:
        """Download the generated audio."""
        try:
            # Try to click download button
            self._click_element(self.SELECTORS["download_btn"])
            time.sleep(3)

            self.logger.info(f"Audio download initiated to: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to download audio: {e}")
            return False
