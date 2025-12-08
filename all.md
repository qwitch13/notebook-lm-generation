# Multi-Agent Collaboration Protocol

This document describes how multiple AI coding assistants (Junie, Claude Code, Gemini) collaborate on the NotebookLM Generation Tool project.

## Agent Roles

### 🤖 Junie (JetBrains AI Assistant)

**Expertise:**
- Selenium browser automation
- CSS selector debugging and optimization
- UI element detection and interaction
- Click interception and overlay handling
- WebDriver configurations

**Preferred Files:**
- `src/generators/notebooklm.py` - NotebookLM browser automation
- `src/auth/google_auth.py` - Google login automation
- `src/utils/downloader.py` - Download handling

**When to Use Junie:**
- CSS selectors not finding elements
- Click interception errors
- Stale element exceptions
- Browser timing issues
- Popup/overlay handling

### 🧠 Claude Code (Anthropic CLI)

**Expertise:**
- Architecture and design patterns
- Complex refactoring across files
- Error handling strategies
- Documentation and README updates
- Code review and quality
- Git operations and commits

**Preferred Files:**
- `src/main.py` - Main entry point
- `src/orchestrator/` - This orchestration system
- `README.md`, `CLAUDE.md`, `JOURNAL.md`
- Any `__init__.py` files

**When to Use Claude Code:**
- Multi-file refactoring needed
- Architecture decisions
- Documentation updates
- Code review requests
- Git commit/push operations

### ✨ Gemini (Google AI in IDE)

**Expertise:**
- Google API integration
- Gemini API prompts and responses
- JSON parsing and handling
- Content generation prompt engineering
- Google authentication patterns

**Preferred Files:**
- `src/generators/gemini_client.py` - Gemini API client
- `src/processors/topic_splitter.py` - Topic extraction
- `src/generators/*.py` - Content generators
- `src/config/settings.py` - Configuration

**When to Use Gemini:**
- Gemini API errors or rate limits
- JSON parsing issues
- Prompt engineering
- Google service integration

## Collaboration Workflow

### 1. Check Shared State

Before starting work, check `.agent_state.json` for:
- Pending tasks that match your expertise
- Messages from other agents
- Currently assigned work

```bash
# View orchestrator status
python -m src.orchestrator.agent_orchestrator status
```

### 2. Claim a Task

When you find a suitable task:
1. Update the task status to "assigned" in `.agent_state.json`
2. Set yourself as the assigned agent
3. This prevents other agents from working on the same task

### 3. Implement Changes

- Work on files matching your expertise
- Follow existing code patterns
- Add appropriate error handling
- Run syntax checks before finishing

### 4. Notify Other Agents

After completing work:
1. Add a message to `.agent_state.json`
2. Describe what you changed
3. Tag specific agents if review needed
4. Update task status to "review" or "completed"

### 5. Review & Merge

- Claude Code typically handles final review
- Check for conflicts with other agents' changes
- Run tests if applicable
- Commit and push when ready

## Task Priority

| Priority | Description |
|----------|-------------|
| 10 | Critical - blocking other work |
| 8 | High - important bug fix |
| 5 | Medium - feature or enhancement |
| 3 | Low - documentation or cleanup |
| 1 | Optional - nice to have |

## Communication Protocol

### Message Format

```json
{
  "from": "junie",
  "to": "claude_code",
  "message": "Updated NotebookLM selectors, please review",
  "timestamp": 1733587200,
  "read_by": []
}
```

### Common Messages

- **Request Review:** "Completed [task], please review [files]"
- **Handoff:** "Fixed [issue], passing to [agent] for [next step]"
- **Blocked:** "Blocked on [issue], need help from [agent]"
- **Question:** "Should we [approach A] or [approach B]?"

## File Ownership Matrix

| File Pattern | Primary | Secondary |
|--------------|---------|-----------|
| `**/notebooklm.py` | Junie | Claude |
| `**/google_auth.py` | Junie | Gemini |
| `**/gemini_client.py` | Gemini | Claude |
| `**/topic_splitter.py` | Gemini | Claude |
| `**/main.py` | Claude | Any |
| `**/orchestrator/**` | Claude | Any |
| `**/*.md` | Claude | Any |
| `**/generators/*.py` | Gemini | Junie |

## CLI Commands

```bash
# Print collaboration guide
python -m src.orchestrator.agent_orchestrator guide

# View current status
python -m src.orchestrator.agent_orchestrator status

# View pending tasks
python -m src.orchestrator.agent_orchestrator tasks

# Get instructions for specific agent
python -m src.orchestrator.agent_orchestrator instructions junie
python -m src.orchestrator.agent_orchestrator instructions claude
python -m src.orchestrator.agent_orchestrator instructions gemini

# Create tasks from issue description
python -m src.orchestrator.agent_orchestrator create "JSON parsing fails with newlines"
```

## Example Collaboration Session

### Scenario: Fix Browser Automation Issue

1. **Claude Code** analyzes the issue and creates tasks:
   ```
   Task 1: Analyze issue → Claude Code
   Task 2: Fix selectors → Junie
   Task 3: Review changes → Claude Code
   ```

2. **Junie** claims Task 2 and works on `notebooklm.py`:
   - Updates CSS selectors
   - Adds scroll-into-view
   - Adds overlay dismissal

3. **Junie** posts message:
   ```
   "Updated selectors in notebooklm.py with JS click fallback,
   overlay dismissal, and scroll-into-view. Ready for review."
   ```

4. **Claude Code** reviews, commits, and pushes.

## Best Practices

1. **Don't overlap** - Check what others are working on
2. **Communicate early** - Post messages before making big changes
3. **Test locally** - Run syntax checks at minimum
4. **Small commits** - Easier to review and revert if needed
5. **Document changes** - Update JOURNAL.md with significant work
6. **Respect expertise** - Let the expert agent handle their domain
# CLAUDE.md - Project Guidelines

## Project Overview
NotebookLM Generation Tool - A comprehensive automation tool that processes educational content and generates various learning materials using Google's Gemini AI and NotebookLM.

## Tech Stack
- **Language**: Python 3.11+
- **Authentication**: Google OAuth 2.0
- **AI Services**: Google Gemini API, NotebookLM (via Selenium automation)
- **Content Processing**: PyPDF2, BeautifulSoup, requests
- **Automation**: Selenium WebDriver
- **Progress Tracking**: Threading with periodic updates

## Project Structure
```
notebook-lm-generation/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── auth/
│   │   ├── __init__.py
│   │   └── google_auth.py      # Google/Gemini authentication
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── content_processor.py # PDF/TXT/Website processing
│   │   └── topic_splitter.py    # Split content by topics
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── notebooklm.py       # NotebookLM automation
│   │   ├── gemini_client.py    # Gemini API client
│   │   ├── handout.py          # Handout generation
│   │   ├── cheatsheet.py       # Cheatsheet generation
│   │   ├── mindmap.py          # Mindmap generation
│   │   ├── audiobook.py        # Audiobook chapters
│   │   ├── story.py            # Fantasy/Sci-Fi stories
│   │   ├── strategy.py         # Learning strategy papers
│   │   ├── flashcards.py       # Karteikarten generation
│   │   ├── quiz.py             # Quiz generation
│   │   └── discussion.py       # Podium discussion videos
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── progress_reporter.py # Progress tracking
│   │   ├── logger.py           # Logging utilities
│   │   └── downloader.py       # Download/export utilities
│   └── config/
│       ├── __init__.py
│       └── settings.py         # Configuration settings
├── tests/
│   └── ...
├── requirements.txt
├── install.sh
├── README.md
├── JOURNAL.md
└── CLAUDE.md
```

## Key Commands
- `python -m src.main <input_file>` - Run the generation pipeline
- `pip install -r requirements.txt` - Install dependencies
- `./install.sh` - Full installation script

## Coding Standards
- Use type hints for all functions
- Docstrings for all public functions
- Error handling with proper logging
- Progress updates every 15 seconds
- All output files saved to input file's directory

## Important Notes
- NotebookLM requires browser automation (no official API)
- Gemini API key required for story generation
- Google OAuth for account authentication
- All operations should be idempotent where possible
- Failed operations should be logged and retried where appropriate

## Environment Variables
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth client secret
- `GEMINI_API_KEY` - Gemini API key

## Testing
- Run tests with: `pytest tests/`
- Integration tests require valid credentials
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
# NotebookLM Tool - Status Report

**Date:** 2024-12-07  
**Project:** `/Users/qwitch13/IdeaProjects/notebook-lm-generation`
**Status:** ✅ READY FOR TESTING

## Summary

The NotebookLM automation tool is now fully functional and ready for testing.

## What's Working ✅

1. **All selectors verified working:**
   - ✅ Studio tab
   - ✅ Chat tab  
   - ✅ Audio-Zusammenfassung
   - ✅ 6 edit icons found
   - ✅ 2 textareas found
   - ✅ All Studio items (Audio, Video, Mindmap, Karteikarten, Quiz, Infografik, Präsentation)

2. **Chrome profile persistence:**
   - Uses `~/.nlm_chrome_profile` to keep login saved
   - No need to log in every time after first use

3. **CLI with action support:**
   - `--action audio` - Generate audio overview
   - `--action chat --chat-message "..."` - Send chat message
   - `--action flashcards` - Generate flashcards
   - `--action quiz` - Generate quiz
   - `--action summary` - Generate summary
   - `--action full` - Full pipeline (default)

4. **Error reporting:**
   - On failure, saves screenshot to `~/nlm_error_*.png`
   - On failure, saves page HTML to `~/nlm_error_*.html`
   - On failure, saves JSON report to `~/nlm_error_report_*.json`

## Quick Start Commands

```bash
# Navigate to project
cd /Users/qwitch13/IdeaProjects/notebook-lm-generation
source venv/bin/activate

# Test audio generation on existing notebook
python3 -m src.main dummy.txt \
  --notebook-url "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009" \
  --action audio

# Test chat on existing notebook
python3 -m src.main dummy.txt \
  --notebook-url "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009" \
  --action chat \
  --chat-message "Summarize the main topics in this notebook"

# Test flashcard generation
python3 -m src.main dummy.txt \
  --notebook-url "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009" \
  --action flashcards
```

## First Time Setup

1. Run the tool once - Chrome will open
2. Log into your Google account manually
3. Your login will be saved for future runs

## UI Elements (German)

The tool supports the German NotebookLM UI:
- Tabs: `Quellen`, `Chat`, `Studio`
- Items: `Audio-Zusammenfassung`, `Videoübersicht`, `Mindmap`, `Karteikarten`, `Quiz`, `Infografik`, `Präsentation`
- Actions: `Notiz hinzufügen`, `Quellen hinzufügen`

## Files Modified

| File | Status |
|------|--------|
| `src/generators/notebooklm.py` | ✅ Complete rewrite with German UI support |
| `src/auth/google_auth.py` | ✅ Persistent Chrome profile |
| `src/main.py` | ✅ Added --action and --chat-message args |
| `test_selectors_simple.py` | ✅ Working test script |

## Troubleshooting

### "Browser not secure" message
- Your login is saved in `~/.nlm_chrome_profile`
- After first login, this shouldn't appear again

### Elements not found
- Check `~/nlm_error_report_*.json` for details
- Check `~/nlm_error_*.png` for screenshot
- The UI may have changed - run `test_selectors_simple.py` to debug

### Chrome crashes
- Close all Chrome windows and try again
- Delete `~/.nlm_chrome_profile` to start fresh
# Development Journal - NotebookLM Generation Tool

## 2025-12-07 - Project Initialization

### Session Start
- Created project structure and CLAUDE.md guidelines
- Planning comprehensive NotebookLM automation tool

### Goals for Today
1. Set up complete project structure
2. Implement all core modules
3. Create documentation and install script
4. Push to GitHub

### Progress Log

#### Phase 1: Project Setup
- [x] Created CLAUDE.md with project guidelines
- [x] Created JOURNAL.md
- [x] Set up directory structure
- [x] Create requirements.txt

#### Phase 2: Core Implementation
- [x] Google authentication module (google_auth.py)
- [x] Content processor (PDF/TXT/Website) (content_processor.py)
- [x] Topic splitter using Gemini (topic_splitter.py)
- [x] NotebookLM browser automation (notebooklm.py)

#### Phase 3: Generation Modules
- [x] Handout generation (handout.py)
- [x] Cheatsheet generation (cheatsheet.py)
- [x] Mindmap generation (mindmap.py)
- [x] Audiobook chapters (audiobook.py)
- [x] Fantasy/Sci-Fi stories (story.py)
- [x] Learning strategy papers (strategy.py)
- [x] Flashcards/Karteikarten + Anki (flashcards.py)
- [x] Quiz generation (quiz.py)
- [x] Podium discussion videos (discussion.py)

#### Phase 4: Utilities
- [x] Progress reporter (15-second updates) (progress_reporter.py)
- [x] Logging system (logger.py)
- [x] Download/export functionality (downloader.py)

#### Phase 5: Finalization
- [x] README.md documentation
- [x] Error testing and fixes (syntax checks passed)
- [x] Code optimization
- [x] Install script (install.sh)
- [x] GitHub push - pushed to qwitch13 and nebulai13

#### Phase 6: Enhancements (2025-12-07)
- [x] Fixed echo color codes in install.sh (echo -e)
- [x] Improved passkey/2FA/fingerprint verification handling
- [x] Added system-wide `nlmgen` command installation
- [x] Created man page (nlmgen.1)
- [x] Created uninstall.sh script
- [x] Updated README.md with comprehensive documentation
- [x] Added password quoting advice (single quotes for special chars)

#### Phase 7: Configuration Management (2025-12-07)
- [x] Added `--add-key KEY` option to save Gemini API key to config file
- [x] Added `--save-user` option to save Google credentials (email/password)
- [x] Config file stored at `~/.config/nlmgen/config`
- [x] Credentials are loaded automatically on future runs
- [x] Priority: CLI args > env vars > saved config

#### Phase 8: Gemini Model Update (2025-12-07)
- [x] Fixed 404 error: `gemini-1.5-pro` model no longer available in v1beta API
- [x] Updated to `gemini-2.0-flash` model in gemini_client.py and topic_splitter.py
- [x] Verified model works (rate limit error confirms model exists)

#### Phase 9: Bug Fixes and Manual Login (2025-12-07)
- [x] Fixed topic splitter JSON parsing - added `_extract_json()` to handle markdown code blocks
- [x] Updated NotebookLM CSS selectors for current UI (2025-12)
- [x] Added rate limit retry logic (3 retries with auto-wait based on API response)
- [x] Changed to manual login mode - browser opens, user logs in themselves
- [x] Login uses saved session cookies when available
- [x] 3-minute timeout for manual login completion

#### Phase 10: Enhanced Error Handling (2025-12-07)
- [x] Improved JSON extraction with balanced brace repair
- [x] Added manual notebook creation fallback when button not found
- [x] Enhanced rate limit detection for daily quota vs per-minute limits
- [x] Clear messaging when daily API quota is exceeded
- [x] 2-minute timeout for manual notebook creation

#### Phase 11: Stability Improvements (2025-12-07)
- [x] Fixed JSON parsing - added more aggressive whitespace stripping
- [x] Added debug logging for raw Gemini responses to diagnose parsing issues
- [x] Fixed stale element handling with retry logic in `_find_element()` and `_click_element()`
- [x] Added `_manual_add_source()` fallback when automatic source addition fails
- [x] Added `_manual_generate_audio()` fallback when audio button not found
- [x] Clipboard integration (pyperclip) to copy source text for manual paste
- [x] All NotebookLM automation now falls back to manual user actions when selectors fail

#### Phase 12: Multi-Agent Orchestrator (2025-12-07)
- [x] Implemented agent orchestrator protocol from coding-agent project
- [x] Created `src/orchestrator/` module with full collaboration system
- [x] Defined agent capabilities for Junie, Claude Code, and Gemini
- [x] Agent roles: ANALYZER, IMPLEMENTER, FIXER, TESTER, OPTIMIZER, REVIEWER, etc.
- [x] TaskQueue with priority and dependency management
- [x] CollaborationProtocol for agent communication via `.agent_state.json`
- [x] File ownership matrix - each agent has preferred files
- [x] CLI interface: status, guide, tasks, instructions, create
- [x] Created AGENTS.md with comprehensive collaboration documentation

#### Phase 13: Debug Logging and Error Handling (2025-12-07)
- [x] Added verbose debug logging throughout `main.py`
- [x] Log traceback for all exceptions in video/content generation
- [x] Added INFO-level logging of raw Gemini response in topic_splitter
- [x] Log JSON parsing attempts with position info on failure
- [x] Fixed error handling in `_generate_all_materials()` with proper try/except
- [x] Added per-topic progress logging with topic index
- [x] Created `current-instr.txt` for multi-agent collaboration instructions

#### Phase 14: NotebookLM-Only Mode (2025-12-07)
- [x] Added `--notebook-url` option to use existing NotebookLM notebook
- [x] Added `--no-api` option to disable Gemini API entirely
- [x] When using existing notebook, skip creating new notebooks for each topic
- [x] Topic splitting uses fallback (local) method when `--no-api` is set
- [x] All content generation uses NotebookLM chat (unlimited) instead of Gemini API
- [x] This avoids API rate limits - NotebookLM generation is unlimited!

### Notes
- NotebookLM doesn't have an official API, so we'll use Selenium for browser automation
- Gemini API will be used for content generation tasks
- Progress reporter will run in a separate thread
- Added Anki flashcard support (.apkg format)
- Tool opens Gemini at the end for additional interaction
- System-wide command: `nlmgen` installed to /usr/local/bin
- Man page available via `man nlmgen`

### Features Implemented
- 10+ content generation types
- Support for PDF, TXT, and website inputs
- Automatic topic splitting using AI
- Progress reporting every 15 seconds
- Detailed logging with timestamps
- Both NotebookLM and Anki flashcard formats
- Fantasy AND Sci-Fi story generation
- Complete podium discussion scripts
- System-wide CLI command (`nlmgen`)
- Comprehensive man page
- Uninstall script with cleanup options
- Passkey/Touch ID/Face ID/2FA support with 2-minute wait
- Persistent config storage for API keys and credentials
- Multi-agent orchestrator for Junie/Claude Code/Gemini collaboration

### Issues Encountered
- Initial echo color codes not displaying (fixed with echo -e)
- Passkey verification timing out (fixed with improved detection and longer wait)

---

## Template for Future Entries

### YYYY-MM-DD - Session Title

#### Completed
- Item 1
- Item 2

#### In Progress
- Item 1

#### Blocked/Issues
- Issue 1

#### Next Steps
- Step 1
# NEXT STEPS TO FIX SELECTORS

## Problem
The CSS/XPath selectors don't match NotebookLM's current UI.
The tool can't find: Studio tab, Generate button, Chat input

## Step 1: Run Debug Script

```bash
cd /Users/qwitch13/IdeaProjects/notebook-lm-generation
source venv/bin/activate
python3 debug_selectors.py
```

This will:
1. Open Chrome and navigate to your notebook
2. Wait for you to login if needed
3. Dump ALL buttons, textareas, and interactive elements
4. Save screenshot to ~/notebooklm_debug_screenshot.png
5. Save page HTML to ~/notebooklm_debug_page.html

## Step 2: Share the Output

After running, share:
1. The terminal output (copy/paste)
2. The screenshot file
3. Key findings about which elements exist

## Step 3: What I Need to Know

From the debug output, I need to find:

1. **Chat Input**: Look for textarea with placeholder containing "Ask" or "Type"
2. **Audio Overview Tab**: Look for button containing "Audio Overview" or "Studio"  
3. **Generate Button**: Look for button containing "Generate" in the Audio panel

## Alternative: Manual Inspection

If the debug script doesn't work, you can manually inspect:

1. Open Chrome DevTools (Cmd+Option+I)
2. Right-click on the chat input → Inspect
3. Note the element's attributes (class, aria-label, placeholder, data-*)
4. Do the same for the Audio Overview tab and Generate button
5. Share those findings with me

## What I've Already Fixed

- ✅ Removed duplicate methods in notebooklm.py
- ✅ Added missing methods (generate_audio_overview, send_chat_message, etc.)
- ✅ Added open_gemini_in_new_tab to google_auth.py
- ✅ Added XPath-based element finding with fallbacks
- ✅ Added debug page dump when elements aren't found
- ✅ Fixed main.py to use proper navigate_to_notebook method
- ✅ Added overlay dismissal logic
- ✅ Increased wait times for page load

## Current Status

The code structure is fixed. The remaining issue is that the element selectors need to be updated to match NotebookLM's current UI, which changes periodically.

---

After you share the debug output, I can update the selectors in:
`/Users/qwitch13/IdeaProjects/notebook-lm-generation/src/generators/notebooklm.py`

In the `ELEMENT_STRATEGIES` dictionary around line 35.
# NotebookLM Generation Tool

Automated learning material generation from educational content using Google's Gemini AI and NotebookLM.

## Features

This tool takes educational content (PDF, TXT, or website) and automatically generates:

- **Video summaries** via NotebookLM Audio Overview
- **Handouts** with keypoint summaries
- **Cheatsheets** for quick reference
- **Mindmaps** (Mermaid format) for each topic
- **Audiobook chapters** with narration scripts
- **Fantasy & Sci-Fi stories** that teach the concepts
- **Learning strategy papers** for exam preparation
- **Flashcards** (Karteikarten) - both markdown and Anki format
- **Quizzes** with answer keys
- **Podium discussions** with 3 participants

### Additional Features

- **Progress reporter** with updates every 15 seconds
- **Detailed logging** of all operations
- **Automatic topic splitting** using AI
- **Anki deck generation** (.apkg format)
- **Opens Gemini** at the end for additional interaction
- **System-wide `nlmgen` command** - run from anywhere
- **Man page** - comprehensive documentation via `man nlmgen`

## Installation

### Prerequisites

- Python 3.11 or higher
- Google Chrome browser
- Google account
- Gemini API key (optional but recommended)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/qwitch13/notebook-lm-generation.git
cd notebook-lm-generation

# Run the install script (installs nlmgen command system-wide)
./install.sh
```

The install script will:
1. Create a Python virtual environment
2. Install all dependencies
3. Create the `.env` configuration file
4. Install the `nlmgen` command to `/usr/local/bin`
5. Install the man page

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Uninstallation

```bash
# Run the uninstall script
./uninstall.sh
```

This will remove the `nlmgen` command and man page. You can optionally remove the virtual environment, configuration, and saved cookies.

## Configuration

### Environment Variables

The install script creates a `.env` file. Edit it to add your API key:

```bash
nano .env
```

```env
# Required for full functionality
GEMINI_API_KEY=your_gemini_api_key

# Optional
HEADLESS_BROWSER=false
LOG_LEVEL=INFO
```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file or pass via command line

## Usage

### Basic Usage

After installation, the `nlmgen` command is available system-wide:

```bash
# Process a PDF file
nlmgen document.pdf

# Process a text file
nlmgen notes.txt

# Process a website
nlmgen https://example.com/article
```

### With Authentication

```bash
# With Google account credentials (use single quotes for passwords with special characters!)
nlmgen document.pdf -e your.email@gmail.com -p 'your_password!'

# With Gemini API key
nlmgen document.pdf --api-key YOUR_API_KEY
```

### Full Example

```bash
nlmgen document.pdf \
    -e email@gmail.com \
    -p 'my!complex_password' \
    -o ./output_folder \
    --api-key YOUR_API_KEY \
    -v  # verbose mode
```

### Using an Existing NotebookLM Notebook (Recommended)

If you've already created a NotebookLM notebook with your content uploaded, you can use it directly to avoid API rate limits:

```bash
# Use existing notebook - bypasses Gemini API rate limits!
nlmgen document.pdf --notebook-url "https://notebooklm.google.com/notebook/your-notebook-id"

# No API mode - uses only NotebookLM for all generation (unlimited!)
nlmgen document.pdf --notebook-url "https://notebooklm.google.com/notebook/your-notebook-id" --no-api
```

This is especially useful when:
- You've hit Gemini API rate limits
- You want to use NotebookLM's unlimited generation capabilities
- You have a pre-existing notebook with sources already added

### Saving Credentials

You can save your API key and credentials for future use:

```bash
# Save Gemini API key
nlmgen --add-key 'YOUR_API_KEY'

# Save Google credentials
nlmgen --save-user -e 'email@gmail.com' -p 'password'

# Future runs use saved credentials automatically
nlmgen document.pdf
```

Credentials are stored in `~/.config/nlmgen/config`.

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `input` | Input file path (PDF, TXT) or URL |
| `-e, --email` | Google account email |
| `-p, --password` | Google account password (use single quotes for special chars) |
| `-o, --output` | Output directory |
| `--headless` | Run browser in headless mode |
| `--api-key` | Gemini API key |
| `--add-key KEY` | Save Gemini API key for future use |
| `--save-user` | Save email/password for future use |
| `--notebook-url` | URL of existing NotebookLM notebook to use |
| `--no-api` | Disable Gemini API, use only NotebookLM chat (unlimited) |
| `-v, --verbose` | Enable verbose output |
| `-h, --help` | Show help message |

### Getting Help

```bash
# Command line help
nlmgen --help

# Man page (detailed documentation)
man nlmgen
```

## Authentication

The tool uses manual login mode for maximum reliability:

1. A browser window will open to Google Sign In
2. **Log in manually** with your Google account
3. Complete any 2FA/passkey verification as needed
4. The tool detects successful login and continues automatically

The tool waits up to 3 minutes for login completion. After first login, cookies are saved so future runs may not require re-authentication.

### Manual Actions

Some actions may require manual intervention:

- **Notebook Creation**: If automatic creation fails, you'll be prompted to create a notebook manually in NotebookLM
- **Rate Limits**: If API rate limits are hit, the tool waits and retries automatically

## Output Structure

All generated files are saved to the same folder as the input file:

```
input_file_output/
├── videos/           # NotebookLM generated videos
├── handouts/         # Summary handouts
├── cheatsheets/      # Quick reference sheets
├── mindmaps/         # Mermaid diagram mindmaps
├── audiobooks/       # Narration scripts
├── stories/          # Fantasy & Sci-Fi stories
├── strategies/       # Learning strategy papers
├── flashcards/       # Markdown flashcards
├── anki/             # Anki deck files (.apkg, .txt)
├── quizzes/          # Quiz files with answer keys
├── discussions/      # Podium discussion scripts
└── notebook_lm_generation.log  # Process log
```

## Progress Tracking

The tool displays progress updates every 15 seconds showing:

- Current processing step
- Completed vs total steps
- Elapsed time
- Status of each generation task

## Troubleshooting

### Common Issues

**Browser automation fails:**
- Make sure Chrome is installed
- Try running without `--headless` first
- Check if Chrome is up to date

**Login fails / 2FA timeout:**
- Use single quotes around passwords with special characters: `-p 'pass!word'`
- Complete 2FA verification within 2 minutes
- Don't use `--headless` when 2FA is required
- Check the browser window for verification prompts

**API errors / Rate limits:**
- Verify your Gemini API key is valid
- Check API quota limits
- **Recommended**: Use `--notebook-url` with an existing NotebookLM notebook to bypass API limits
- Use `--no-api` flag to disable API entirely and use only NotebookLM's unlimited chat
- The tool will fall back to browser automation if API fails

**NotebookLM issues:**
- NotebookLM UI may change - selectors might need updating
- Some features require manual interaction
- Audio generation can take several minutes

**Command not found after install:**
- Make sure `/usr/local/bin` is in your PATH
- Try: `export PATH="/usr/local/bin:$PATH"`

### Logs

Check the log file for detailed error information:

```bash
cat output_folder/notebook_lm_generation.log
```

## Development

### Project Structure

```
notebook-lm-generation/
├── src/
│   ├── main.py              # Entry point
│   ├── auth/                # Authentication
│   ├── processors/          # Content processing
│   ├── generators/          # Material generation
│   ├── utils/               # Utilities
│   └── config/              # Configuration
├── tests/                   # Test files
├── nlmgen.1                 # Man page source
├── install.sh               # Installation script
├── uninstall.sh             # Uninstallation script
├── requirements.txt
└── README.md
```

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Security Notes

- Never commit credentials to version control
- Use environment variables for sensitive data
- The tool stores cookies locally (`~/.notebook_lm_gen/`) for session persistence
- Consider using a separate Google account for automation

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Google Gemini AI for content generation
- Google NotebookLM for audio/video features
- Selenium for browser automation
- All open source dependencies

## Support

For issues and feature requests, please use the GitHub issue tracker:
- https://github.com/qwitch13/notebook-lm-generation/issues
