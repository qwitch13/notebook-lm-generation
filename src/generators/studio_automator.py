"""
NotebookLM Studio Automation - Full Material Generation
Based on Perplexity Comet analysis of DOM structure

Generates all 6 material types per source:
- Audio Summary (requires English language setting)
- Video Overview (requires English language setting)
- Mindmap (no language setting, immediate generation)
- Quiz (no language setting, immediate generation)
- Flashcards/Karteikarten (no language setting, immediate generation)
- Infographic (requires English language setting)
"""

import time
import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils.logger import get_logger


class MaterialType(Enum):
    """Types of materials that can be generated in NotebookLM Studio."""
    AUDIO = "audio"
    VIDEO = "video"
    MINDMAP = "mindmap"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"
    INFOGRAPHIC = "infographic"


@dataclass
class MaterialStatus:
    """Status of a generated material."""
    material_type: MaterialType
    source_name: str
    started: bool = False
    completed: bool = False
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SourceInfo:
    """Information about a notebook source."""
    name: str
    truncated_name: str  # What appears in UI (usually truncated)
    index: int
    checkbox_element: any = None


class StudioAutomator:
    """
    Automates NotebookLM Studio material generation.
    
    Workflow per source:
    1. Deselect all sources
    2. Select single source
    3. Generate all 6 materials
    4. Move to next source
    """
    
    # Materials that require English language setting
    LANGUAGE_REQUIRED = {MaterialType.AUDIO, MaterialType.VIDEO, MaterialType.INFOGRAPHIC}
    
    # Materials that generate immediately (no dialog)
    IMMEDIATE_GENERATION = {MaterialType.MINDMAP, MaterialType.QUIZ, MaterialType.FLASHCARDS}
    
    # Button labels (German UI)
    BUTTON_LABELS = {
        MaterialType.AUDIO: "Audio-Zusammenfassung anpassen",
        MaterialType.VIDEO: "Video-Zusammenfassung anpassen",
        MaterialType.MINDMAP: "Mindmap",
        MaterialType.QUIZ: "Quiz",
        MaterialType.FLASHCARDS: "Karteikarten",
        MaterialType.INFOGRAPHIC: "Infografik anpassen",
    }
    
    # Alternative button labels (partial matches)
    BUTTON_ALTERNATIVES = {
        MaterialType.AUDIO: ["Audio", "audio_magic_eraser"],
        MaterialType.VIDEO: ["Video"],
        MaterialType.MINDMAP: ["Mindmap", "mind_map"],
        MaterialType.QUIZ: ["Quiz"],
        MaterialType.FLASHCARDS: ["Karteikarten", "Flashcard", "cards"],
        MaterialType.INFOGRAPHIC: ["Infografik", "Infographic"],
    }
    
    def __init__(self, driver, logger=None):
        """Initialize the Studio automator."""
        self.driver = driver
        self.logger = logger or get_logger()
        self.generation_status: List[MaterialStatus] = []
        
    def _wait(self, seconds: float):
        """Wait with logging."""
        self.logger.debug(f"Waiting {seconds}s...")
        time.sleep(seconds)
        
    def _scroll_element(self, element, scroll_amount: int = 200):
        """Scroll within an element (for dropdowns)."""
        try:
            self.driver.execute_script(
                "arguments[0].scrollTop += arguments[1];",
                element, scroll_amount
            )
        except Exception as e:
            self.logger.debug(f"Scroll failed: {e}")
            # Fallback: use mouse wheel
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.scroll_by_amount(0, scroll_amount)
                actions.perform()
            except:
                pass

    def _click_safe(self, element) -> bool:
        """Safely click an element with JS fallback."""
        if not element:
            return False
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            self._wait(0.3)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            try:
                element.click()
                return True
            except Exception as e2:
                self.logger.error(f"Click failed: {e2}")
                return False

    def _find_by_aria_label(self, label: str, partial: bool = True) -> Optional[any]:
        """Find element by aria-label."""
        try:
            if partial:
                xpath = f"//*[contains(@aria-label, '{label}')]"
            else:
                xpath = f"//*[@aria-label='{label}']"
            elements = self.driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except Exception as e:
            self.logger.debug(f"aria-label search failed: {e}")
        return None

    def _find_by_text(self, text: str, tag: str = "*") -> Optional[any]:
        """Find element containing text."""
        try:
            xpath = f"//{tag}[contains(text(), '{text}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except Exception as e:
            self.logger.debug(f"Text search failed: {e}")
        return None

    def _find_button(self, label: str, alternatives: List[str] = None) -> Optional[any]:
        """Find a button by label or alternative texts."""
        # Try aria-label first
        btn = self._find_by_aria_label(label)
        if btn:
            return btn
            
        # Try button text
        btn = self._find_by_text(label, "button")
        if btn:
            return btn
            
        # Try alternatives
        if alternatives:
            for alt in alternatives:
                btn = self._find_by_aria_label(alt)
                if btn:
                    return btn
                btn = self._find_by_text(alt, "button")
                if btn:
                    return btn
                    
        # Try finding by class patterns
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for b in buttons:
                if b.is_displayed():
                    aria = b.get_attribute("aria-label") or ""
                    text = b.text or ""
                    if label.lower() in aria.lower() or label.lower() in text.lower():
                        return b
        except:
            pass
            
        return None

    # =========================================================================
    # SOURCE SELECTION
    # =========================================================================
    
    def get_sources_count_display(self) -> str:
        """Get the sources count displayed in chat area (e.g., '1 Quelle' or '0 Quellen')."""
        try:
            # Look for text like "X Quelle(n)" in chat area
            patterns = [
                r"(\d+)\s*Quelle",
                r"(\d+)\s*source",
            ]
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group(0)
        except:
            pass
        return "unknown"

    def list_sources(self) -> List[SourceInfo]:
        """List all available sources in the notebook."""
        sources = []
        try:
            # Click on Quellen/Sources panel first
            sources_header = self._find_by_text("Quellen")
            if not sources_header:
                sources_header = self._find_by_text("Sources")
            if sources_header:
                self._click_safe(sources_header)
                self._wait(1)
            
            # Find all source checkboxes
            checkboxes = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "input[type='checkbox'][aria-label]"
            )
            
            for i, cb in enumerate(checkboxes):
                aria = cb.get_attribute("aria-label") or ""
                # Skip "Alle Quellen" (select all) checkbox
                if "alle" in aria.lower() or "all" in aria.lower():
                    continue
                if cb.is_displayed():
                    sources.append(SourceInfo(
                        name=aria,
                        truncated_name=aria[:30] + "..." if len(aria) > 30 else aria,
                        index=i,
                        checkbox_element=cb
                    ))
                    
            self.logger.info(f"Found {len(sources)} sources")
            
        except Exception as e:
            self.logger.error(f"Failed to list sources: {e}")
            
        return sources

    def deselect_all_sources(self) -> bool:
        """Deselect all sources using 'Alle Quellen auswählen' checkbox."""
        self.logger.info("Deselecting all sources...")
        try:
            # Find "Alle Quellen auswählen" checkbox
            all_cb = self._find_by_aria_label("Alle Quellen")
            if not all_cb:
                # Alternative: find by text nearby
                all_text = self._find_by_text("Alle Quellen")
                if all_text:
                    # Find checkbox near this text
                    parent = all_text.find_element(By.XPATH, "./..")
                    checkboxes = parent.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    if checkboxes:
                        all_cb = checkboxes[0]
            
            if all_cb:
                # Check if it's currently checked
                is_checked = all_cb.get_attribute("checked") or all_cb.is_selected()
                if is_checked:
                    self._click_safe(all_cb)
                    self._wait(1)
                    self.logger.info("Deselected all sources")
                else:
                    # If not checked, we need to check then uncheck to deselect all
                    self._click_safe(all_cb)
                    self._wait(0.5)
                    self._click_safe(all_cb)
                    self._wait(1)
                return True
            else:
                self.logger.warning("Could not find 'Alle Quellen' checkbox")
                
        except Exception as e:
            self.logger.error(f"Failed to deselect sources: {e}")
            
        return False

    def select_source(self, source: SourceInfo) -> bool:
        """Select a single source by its info."""
        self.logger.info(f"Selecting source: {source.truncated_name}")
        try:
            if source.checkbox_element:
                self._click_safe(source.checkbox_element)
                self._wait(1)
                # Verify selection
                count = self.get_sources_count_display()
                self.logger.info(f"Sources selected: {count}")
                return "1" in count
            else:
                # Find by aria-label
                cb = self._find_by_aria_label(source.name[:20])
                if cb:
                    self._click_safe(cb)
                    self._wait(1)
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to select source: {e}")
            
        return False

    def select_source_by_name(self, name_pattern: str) -> bool:
        """Select a source by partial name match."""
        sources = self.list_sources()
        for source in sources:
            if name_pattern.lower() in source.name.lower():
                return self.select_source(source)
        self.logger.warning(f"No source matching: {name_pattern}")
        return False

    # =========================================================================
    # LANGUAGE SELECTION (for Audio, Video, Infographic)
    # =========================================================================
    
    def _select_english_language(self) -> bool:
        """Select English language in a customization dialog dropdown."""
        try:
            self._wait(1)
            
            # Find the language dropdown (combobox)
            dropdown = None
            # Method 1: By role
            dropdowns = self.driver.find_elements(By.CSS_SELECTOR, "[role='combobox']")
            for dd in dropdowns:
                if dd.is_displayed():
                    text = dd.text or ""
                    if "Deutsch" in text or "German" in text or "sprache" in dd.get_attribute("aria-label").lower() if dd.get_attribute("aria-label") else False:
                        dropdown = dd
                        break
            
            # Method 2: By finding dropdown near "Sprache" label
            if not dropdown:
                lang_label = self._find_by_text("Sprache")
                if lang_label:
                    parent = lang_label.find_element(By.XPATH, "./..")
                    dropdowns = parent.find_elements(By.CSS_SELECTOR, "[role='combobox']")
                    if dropdowns:
                        dropdown = dropdowns[0]
            
            if not dropdown:
                self.logger.warning("Could not find language dropdown")
                return False
                
            # Click dropdown to open
            self.logger.debug("Clicking language dropdown...")
            self._click_safe(dropdown)
            self._wait(1)
            
            # Scroll down to find English
            self._scroll_element(dropdown, 200)
            self._wait(0.5)
            self._scroll_element(dropdown, 200)
            self._wait(0.5)
            
            # Find English option
            english_option = None
            options = self.driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            for opt in options:
                if opt.is_displayed() and "english" in opt.text.lower():
                    english_option = opt
                    break
            
            if not english_option:
                # Alternative: find by text
                english_option = self._find_by_text("English")
            
            if english_option:
                self.logger.debug("Selecting English...")
                self._click_safe(english_option)
                self._wait(1)
                self.logger.info("Selected English language")
                return True
            else:
                self.logger.warning("Could not find English option")
                
        except Exception as e:
            self.logger.error(f"Language selection failed: {e}")
            
        return False

    def _click_create_button(self) -> bool:
        """Click the 'Erstellen' (Create) button in a dialog."""
        try:
            # Find create button
            create_btn = self._find_by_text("Erstellen", "button")
            if not create_btn:
                create_btn = self._find_by_text("Create", "button")
            if not create_btn:
                create_btn = self._find_by_text("Generate", "button")
                
            if create_btn:
                self._click_safe(create_btn)
                self._wait(2)
                self.logger.info("Clicked Create button")
                return True
            else:
                self.logger.warning("Could not find Create button")
                
        except Exception as e:
            self.logger.error(f"Create button click failed: {e}")
            
        return False

    # =========================================================================
    # MATERIAL GENERATION
    # =========================================================================
    
    def _open_studio_panel(self) -> bool:
        """Ensure Studio panel is open/visible."""
        try:
            # Look for Studio tab
            studio_tab = self._find_by_text("Studio")
            if studio_tab:
                self._click_safe(studio_tab)
                self._wait(2)
                self.logger.info("Opened Studio panel")
                return True
        except Exception as e:
            self.logger.error(f"Failed to open Studio: {e}")
        return False

    def generate_audio(self, source_name: str = "") -> MaterialStatus:
        """Generate Audio Summary with English language."""
        status = MaterialStatus(MaterialType.AUDIO, source_name)
        self.logger.info("Generating Audio Summary...")
        
        try:
            # Find and click Audio customize button
            btn = self._find_button(
                self.BUTTON_LABELS[MaterialType.AUDIO],
                self.BUTTON_ALTERNATIVES[MaterialType.AUDIO]
            )
            if not btn:
                # Alternative: find edit icon near Audio text
                audio_text = self._find_by_text("Audio")
                if audio_text:
                    parent = audio_text.find_element(By.XPATH, "./../..")
                    edit_icons = parent.find_elements(By.XPATH, ".//mat-icon[contains(text(), 'edit')]")
                    if edit_icons:
                        btn = edit_icons[0]
            
            if not btn:
                status.error = "Could not find Audio button"
                self.logger.error(status.error)
                return status
                
            self._click_safe(btn)
            self._wait(2)
            
            # Select English language
            if not self._select_english_language():
                self.logger.warning("Could not change language, proceeding anyway")
            
            # Click Create
            if self._click_create_button():
                status.started = True
                self.logger.info("Audio generation started")
            else:
                status.error = "Could not click Create button"
                
        except Exception as e:
            status.error = str(e)
            self.logger.error(f"Audio generation failed: {e}")
            
        self.generation_status.append(status)
        return status

    def generate_video(self, source_name: str = "") -> MaterialStatus:
        """Generate Video Overview with English language."""
        status = MaterialStatus(MaterialType.VIDEO, source_name)
        self.logger.info("Generating Video Overview...")
        
        try:
            btn = self._find_button(
                self.BUTTON_LABELS[MaterialType.VIDEO],
                self.BUTTON_ALTERNATIVES[MaterialType.VIDEO]
            )
            if not btn:
                status.error = "Could not find Video button"
                self.logger.error(status.error)
                return status
                
            self._click_safe(btn)
            self._wait(2)
            
            # Select English
            if not self._select_english_language():
                self.logger.warning("Could not change language, proceeding anyway")
            
            # Click Create
            if self._click_create_button():
                status.started = True
                self.logger.info("Video generation started")
            else:
                status.error = "Could not click Create button"
                
        except Exception as e:
            status.error = str(e)
            self.logger.error(f"Video generation failed: {e}")
            
        self.generation_status.append(status)
        return status

    def generate_mindmap(self, source_name: str = "") -> MaterialStatus:
        """Generate Mindmap (immediate, no dialog)."""
        status = MaterialStatus(MaterialType.MINDMAP, source_name)
        self.logger.info("Generating Mindmap...")
        
        try:
            btn = self._find_button(
                self.BUTTON_LABELS[MaterialType.MINDMAP],
                self.BUTTON_ALTERNATIVES[MaterialType.MINDMAP]
            )
            if not btn:
                status.error = "Could not find Mindmap button"
                self.logger.error(status.error)
                return status
                
            self._click_safe(btn)
            self._wait(2)
            status.started = True
            self.logger.info("Mindmap generation started")
                
        except Exception as e:
            status.error = str(e)
            self.logger.error(f"Mindmap generation failed: {e}")
            
        self.generation_status.append(status)
        return status

    def generate_quiz(self, source_name: str = "") -> MaterialStatus:
        """Generate Quiz (immediate, no dialog)."""
        status = MaterialStatus(MaterialType.QUIZ, source_name)
        self.logger.info("Generating Quiz...")
        
        try:
            btn = self._find_button(
                self.BUTTON_LABELS[MaterialType.QUIZ],
                self.BUTTON_ALTERNATIVES[MaterialType.QUIZ]
            )
            if not btn:
                status.error = "Could not find Quiz button"
                self.logger.error(status.error)
                return status
                
            self._click_safe(btn)
            self._wait(2)
            status.started = True
            self.logger.info("Quiz generation started")
                
        except Exception as e:
            status.error = str(e)
            self.logger.error(f"Quiz generation failed: {e}")
            
        self.generation_status.append(status)
        return status

    def generate_flashcards(self, source_name: str = "") -> MaterialStatus:
        """Generate Flashcards/Karteikarten (immediate, no dialog)."""
        status = MaterialStatus(MaterialType.FLASHCARDS, source_name)
        self.logger.info("Generating Flashcards...")
        
        try:
            btn = self._find_button(
                self.BUTTON_LABELS[MaterialType.FLASHCARDS],
                self.BUTTON_ALTERNATIVES[MaterialType.FLASHCARDS]
            )
            if not btn:
                status.error = "Could not find Flashcards button"
                self.logger.error(status.error)
                return status
                
            self._click_safe(btn)
            self._wait(2)
            status.started = True
            self.logger.info("Flashcards generation started")
                
        except Exception as e:
            status.error = str(e)
            self.logger.error(f"Flashcards generation failed: {e}")
            
        self.generation_status.append(status)
        return status

    def generate_infographic(self, source_name: str = "") -> MaterialStatus:
        """Generate Infographic with English language."""
        status = MaterialStatus(MaterialType.INFOGRAPHIC, source_name)
        self.logger.info("Generating Infographic...")
        
        try:
            btn = self._find_button(
                self.BUTTON_LABELS[MaterialType.INFOGRAPHIC],
                self.BUTTON_ALTERNATIVES[MaterialType.INFOGRAPHIC]
            )
            if not btn:
                status.error = "Could not find Infographic button"
                self.logger.error(status.error)
                return status
                
            self._click_safe(btn)
            self._wait(2)
            
            # Select English
            if not self._select_english_language():
                self.logger.warning("Could not change language, proceeding anyway")
            
            # Click Create
            if self._click_create_button():
                status.started = True
                self.logger.info("Infographic generation started")
            else:
                status.error = "Could not click Create button"
                
        except Exception as e:
            status.error = str(e)
            self.logger.error(f"Infographic generation failed: {e}")
            
        self.generation_status.append(status)
        return status

    # =========================================================================
    # FULL AUTOMATION
    # =========================================================================
    
    def generate_all_materials_for_source(
        self, 
        source: SourceInfo,
        materials: List[MaterialType] = None
    ) -> List[MaterialStatus]:
        """Generate all (or specified) materials for a single source."""
        
        if materials is None:
            materials = list(MaterialType)
            
        results = []
        source_name = source.truncated_name
        
        self.logger.info(f"=" * 60)
        self.logger.info(f"Processing source: {source_name}")
        self.logger.info(f"=" * 60)
        
        # Open Studio panel
        self._open_studio_panel()
        self._wait(1)
        
        # Generate each material type
        for mat_type in materials:
            self.logger.info(f"--- Generating {mat_type.value} ---")
            
            if mat_type == MaterialType.AUDIO:
                status = self.generate_audio(source_name)
            elif mat_type == MaterialType.VIDEO:
                status = self.generate_video(source_name)
            elif mat_type == MaterialType.MINDMAP:
                status = self.generate_mindmap(source_name)
            elif mat_type == MaterialType.QUIZ:
                status = self.generate_quiz(source_name)
            elif mat_type == MaterialType.FLASHCARDS:
                status = self.generate_flashcards(source_name)
            elif mat_type == MaterialType.INFOGRAPHIC:
                status = self.generate_infographic(source_name)
            else:
                continue
                
            results.append(status)
            self._wait(2)  # Wait between materials
            
        return results

    def process_all_sources(
        self, 
        source_patterns: List[str] = None,
        materials: List[MaterialType] = None
    ) -> Dict[str, List[MaterialStatus]]:
        """
        Process all sources (or matching patterns) and generate materials.
        
        Args:
            source_patterns: Optional list of patterns to match source names
            materials: Optional list of material types to generate (default: all)
            
        Returns:
            Dict mapping source names to their generation statuses
        """
        all_results = {}
        
        # Get all sources
        sources = self.list_sources()
        
        if not sources:
            self.logger.error("No sources found!")
            return all_results
            
        self.logger.info(f"Found {len(sources)} sources to process")
        
        # Filter by patterns if provided
        if source_patterns:
            filtered = []
            for source in sources:
                for pattern in source_patterns:
                    if pattern.lower() in source.name.lower():
                        filtered.append(source)
                        break
            sources = filtered
            self.logger.info(f"Filtered to {len(sources)} matching sources")
        
        # Process each source
        for i, source in enumerate(sources):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"[{i+1}/{len(sources)}] {source.truncated_name}")
            self.logger.info(f"{'='*60}")
            
            # Step 1: Deselect all
            self.deselect_all_sources()
            self._wait(1)
            
            # Step 2: Select this source
            if not self.select_source(source):
                self.logger.error(f"Failed to select source: {source.truncated_name}")
                continue
            
            # Step 3: Generate all materials
            results = self.generate_all_materials_for_source(source, materials)
            all_results[source.name] = results
            
            # Step 4: Deselect (cleanup)
            self.deselect_all_sources()
            self._wait(2)
            
            # Progress report
            success = sum(1 for r in results if r.started)
            self.logger.info(f"Completed {source.truncated_name}: {success}/{len(results)} materials started")
            
        return all_results

    def get_summary_report(self) -> str:
        """Get a summary report of all generation attempts."""
        lines = [
            "=" * 60,
            "STUDIO AUTOMATION SUMMARY REPORT",
            "=" * 60,
            f"Total operations: {len(self.generation_status)}",
            "",
        ]
        
        # Group by source
        by_source = {}
        for status in self.generation_status:
            if status.source_name not in by_source:
                by_source[status.source_name] = []
            by_source[status.source_name].append(status)
            
        for source, statuses in by_source.items():
            lines.append(f"\n📄 Source: {source or 'Unknown'}")
            for s in statuses:
                icon = "✅" if s.started and not s.error else "❌"
                error_msg = f" - {s.error}" if s.error else ""
                lines.append(f"  {icon} {s.material_type.value}{error_msg}")
                
        # Summary stats
        started = sum(1 for s in self.generation_status if s.started)
        failed = sum(1 for s in self.generation_status if s.error)
        lines.extend([
            "",
            "-" * 40,
            f"Started: {started}",
            f"Failed: {failed}",
            f"Total: {len(self.generation_status)}",
        ])
        
        return "\n".join(lines)


    # =========================================================================
    # DOWNLOAD FUNCTIONALITY
    # Based on Comet analysis - downloads completed materials
    # =========================================================================
    
    # Downloadable content types
    DOWNLOADABLE_TYPES = {
        "erklärvideo": "video",      # .mp4
        "video": "video",
        "audio-zusammenfassung": "audio",  # .mp3
        "zusammenfassung": "audio",
        "audio": "audio",
        "mindmap": "mindmap",        # .png
    }
    
    # Non-downloadable types (share/copy only)
    NON_DOWNLOADABLE = ["quiz", "karteikarten", "flashcards", "lernkarten", 
                        "detaillierte analyse", "bericht", "präsentation"]

    def _find_mehr_button_for_item(self, item_name: str) -> Optional[any]:
        """Find the 'Mehr' (More) button for a specific item."""
        try:
            # Strategy 1: Find by aria-label pattern
            xpaths = [
                f"//*[contains(text(), '{item_name[:20]}')]/ancestor::*[contains(@class, 'item') or contains(@class, 'card')]//button[contains(@aria-label, 'Mehr') or contains(@aria-label, 'More')]",
                f"//*[contains(text(), '{item_name[:20]}')]/following::button[contains(text(), 'more_vert') or @aria-label='Mehr'][1]",
                f"//*[contains(text(), '{item_name[:20]}')]/parent::*//button[last()]",
                # Material icon more_vert
                f"//*[contains(text(), '{item_name[:20]}')]/ancestor::*[1]//mat-icon[text()='more_vert']/parent::button",
            ]
            
            for xpath in xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            return elem
                except:
                    continue
            
            # Strategy 2: Find all Mehr buttons and match by proximity
            mehr_buttons = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(@aria-label, 'Mehr') or .//mat-icon[text()='more_vert']]"
            )
            
            # Find the item text element
            item_elem = self._find_by_text(item_name[:20])
            if item_elem and mehr_buttons:
                # Get item position
                item_rect = item_elem.rect
                item_center_y = item_rect['y'] + item_rect['height'] / 2
                
                # Find closest Mehr button
                best_btn = None
                min_distance = float('inf')
                
                for btn in mehr_buttons:
                    if btn.is_displayed():
                        btn_rect = btn.rect
                        btn_center_y = btn_rect['y'] + btn_rect['height'] / 2
                        
                        # Check if on same "row" (within 50px vertically)
                        if abs(btn_center_y - item_center_y) < 50:
                            distance = abs(btn_center_y - item_center_y)
                            if distance < min_distance:
                                min_distance = distance
                                best_btn = btn
                
                if best_btn:
                    return best_btn
                    
        except Exception as e:
            self.logger.debug(f"Mehr button search failed: {e}")
            
        return None

    def _click_menu_option(self, option_text: str, timeout: float = 3.0) -> bool:
        """Click an option in an open menu."""
        try:
            xpaths = [
                f"//button[contains(text(), '{option_text}')]",
                f"//div[@role='menuitem'][contains(text(), '{option_text}')]",
                f"//*[@role='menuitem'][contains(., '{option_text}')]",
                f"//mat-menu-item[contains(., '{option_text}')]",
                f"//*[contains(@class, 'menu')]//button[contains(., '{option_text}')]",
            ]
            
            for xpath in xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            self._click_safe(elem)
                            return True
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Menu option click failed: {e}")
            
        return False

    def _close_dialog(self) -> bool:
        """Close any open dialog."""
        try:
            # Find close button (X)
            close_xpaths = [
                "//button[contains(@aria-label, 'Close') or contains(@aria-label, 'Schließen')]",
                "//button[.//mat-icon[text()='close']]",
                "//dialog//button[contains(@class, 'close')]",
                "//div[@role='dialog']//button[1]",  # Usually first button is close
            ]
            
            for xpath in close_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            self._click_safe(elem)
                            self._wait(0.5)
                            return True
                except:
                    continue
            
            # Fallback: Press Escape
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self._wait(0.5)
            return True
            
        except Exception as e:
            self.logger.debug(f"Dialog close failed: {e}")
            
        return False

    def _cancel_delete_dialog(self) -> bool:
        """Cancel a delete confirmation dialog if one appears."""
        try:
            # Look for "Abbrechen" (Cancel) button in delete confirmation
            cancel_btn = self._find_by_text("Abbrechen", "button")
            if not cancel_btn:
                cancel_btn = self._find_by_text("Cancel", "button")
            
            if cancel_btn and cancel_btn.is_displayed():
                self._click_safe(cancel_btn)
                self._wait(0.5)
                return True
                
        except:
            pass
        return False

    def download_item(self, item_name: str, item_type: str = "unknown") -> dict:
        """
        Download a single item from Studio.
        
        Args:
            item_name: Name/title of the item to download
            item_type: Type hint (video, audio, mindmap)
            
        Returns:
            dict with 'success', 'filename', 'error' keys
        """
        result = {
            'success': False,
            'item_name': item_name,
            'item_type': item_type,
            'filename': None,
            'error': None
        }
        
        self.logger.info(f"📥 Downloading: {item_name[:40]}...")
        
        try:
            # Step 1: Find the Mehr (More) button for this item
            mehr_btn = self._find_mehr_button_for_item(item_name)
            
            if not mehr_btn:
                result['error'] = "Could not find Mehr button"
                self.logger.warning(result['error'])
                return result
            
            # Step 2: Click to open context menu
            self._click_safe(mehr_btn)
            self._wait(1)  # Allow menu to render
            
            # Step 3: Check for and click "Herunterladen" (Download)
            if self._click_menu_option("Herunterladen"):
                result['success'] = True
                result['filename'] = f"{item_name}.{'mp4' if item_type == 'video' else 'mp3' if item_type == 'audio' else 'png'}"
                self.logger.info(f"   ✅ Download initiated: {result['filename']}")
                self._wait(1)
                return result
            
            # Step 4: Check if share dialog opened instead
            # (Some items don't have download option)
            dialog_detected = self.driver.find_elements(By.XPATH, "//div[@role='dialog']")
            if dialog_detected:
                self.logger.info("   Share dialog detected (no download available)")
                self._close_dialog()
                result['error'] = "No download option (share only)"
                return result
            
            # Step 5: Check for delete confirmation (clicked wrong option)
            if self._cancel_delete_dialog():
                result['error'] = "Accidentally triggered delete dialog"
                return result
            
            result['error'] = "Download option not found in menu"
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Download failed: {e}")
            
        return result


    def list_generated_materials(self) -> List[dict]:
        """
        List all generated materials in the Studio panel.
        
        Returns:
            List of dicts with 'name', 'type', 'status', 'downloadable' keys
        """
        materials = []
        
        try:
            self._open_studio_panel()
            self._wait(2)
            
            # Find all items in Studio panel
            # Items typically have structure: title, metadata, action buttons
            item_xpaths = [
                "//div[contains(@class, 'studio')]//div[contains(@class, 'item')]",
                "//div[contains(@class, 'generated')]//div[contains(@class, 'card')]",
                "//*[contains(@class, 'material-list')]//*[contains(@class, 'item')]",
            ]
            
            # Get page text to parse items
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Parse for known material types
            lines = page_text.split('\n')
            current_item = None
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Detect item type
                item_type = None
                for type_key, type_val in self.DOWNLOADABLE_TYPES.items():
                    if type_key in line_lower:
                        item_type = type_val
                        break
                
                # Check if non-downloadable
                is_non_downloadable = any(nd in line_lower for nd in self.NON_DOWNLOADABLE)
                
                # Check if still generating
                is_generating = "wird erstellt" in line_lower or "kommen sie in" in line_lower
                
                if item_type and not is_non_downloadable:
                    # Look for item name (usually previous non-empty line)
                    item_name = lines[i-1].strip() if i > 0 and lines[i-1].strip() else line
                    
                    materials.append({
                        'name': item_name,
                        'type': item_type,
                        'type_label': line.strip(),
                        'status': 'generating' if is_generating else 'ready',
                        'downloadable': not is_generating,
                    })
            
            self.logger.info(f"Found {len(materials)} downloadable materials")
            
        except Exception as e:
            self.logger.error(f"Failed to list materials: {e}")
            
        return materials

    def download_all_materials(self, download_dir: str = None) -> dict:
        """
        Download all completed materials from Studio.
        
        Args:
            download_dir: Optional directory (uses browser default if None)
            
        Returns:
            dict with statistics and results
        """
        results = {
            'total': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'items': []
        }
        
        self.logger.info("=" * 60)
        self.logger.info("DOWNLOADING ALL MATERIALS")
        self.logger.info("=" * 60)
        
        # Get list of materials
        materials = self.list_generated_materials()
        results['total'] = len(materials)
        
        if not materials:
            self.logger.warning("No materials found to download")
            return results
        
        self.logger.info(f"Found {len(materials)} materials")
        
        # Download each material
        for i, material in enumerate(materials):
            self.logger.info(f"\n[{i+1}/{len(materials)}] {material['name'][:40]}...")
            
            # Skip if still generating
            if material['status'] == 'generating':
                self.logger.info("   ⏳ Still generating, skipping")
                results['skipped'] += 1
                results['items'].append({
                    **material,
                    'result': 'skipped',
                    'reason': 'still generating'
                })
                continue
            
            # Download
            dl_result = self.download_item(material['name'], material['type'])
            
            if dl_result['success']:
                results['downloaded'] += 1
                results['items'].append({
                    **material,
                    'result': 'success',
                    'filename': dl_result.get('filename')
                })
            else:
                results['failed'] += 1
                results['items'].append({
                    **material,
                    'result': 'failed',
                    'error': dl_result.get('error')
                })
            
            # Small wait between downloads
            self._wait(1)
        
        # Summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("DOWNLOAD SUMMARY")
        self.logger.info(f"  Total: {results['total']}")
        self.logger.info(f"  Downloaded: {results['downloaded']}")
        self.logger.info(f"  Skipped: {results['skipped']}")
        self.logger.info(f"  Failed: {results['failed']}")
        self.logger.info("=" * 60)
        
        return results

    # =========================================================================
    # NOTEBOOK CREATION
    # =========================================================================
    
    def create_new_notebook(self, name: str = None) -> Optional[str]:
        """
        Create a new NotebookLM notebook.
        
        Args:
            name: Optional name for the notebook
            
        Returns:
            URL of the new notebook, or None if failed
        """
        self.logger.info(f"Creating new notebook: {name or '(unnamed)'}")
        
        try:
            # Navigate to NotebookLM home
            self.driver.get("https://notebooklm.google.com/")
            self._wait(3)
            
            # Find and click "New notebook" / "Notebook erstellen" button
            create_btn = self._find_button("Notebook erstellen", ["New notebook", "Create", "erstellen"])
            
            if not create_btn:
                # Try finding by icon
                create_btn = self.driver.find_element(
                    By.XPATH,
                    "//button[.//mat-icon[text()='add'] or contains(@class, 'create')]"
                )
            
            if create_btn:
                self._click_safe(create_btn)
                self._wait(3)
                
                # Wait for notebook to be created
                WebDriverWait(self.driver, 10).until(
                    EC.url_contains("/notebook/")
                )
                
                notebook_url = self.driver.current_url
                self.logger.info(f"Created notebook: {notebook_url}")
                
                # Set name if provided
                if name:
                    self._set_notebook_name(name)
                
                return notebook_url
            else:
                self.logger.error("Could not find create notebook button")
                
        except Exception as e:
            self.logger.error(f"Notebook creation failed: {e}")
            
        return None

    def _set_notebook_name(self, name: str) -> bool:
        """Set the notebook name/title."""
        try:
            # Find title input (usually editable heading)
            title_xpaths = [
                "//input[contains(@placeholder, 'Titel') or contains(@placeholder, 'Title')]",
                "//h1[contains(@contenteditable, 'true')]",
                "//*[contains(@class, 'title')]//input",
                "//div[contains(@class, 'notebook-title')]",
            ]
            
            for xpath in title_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            elem.clear()
                            elem.send_keys(name)
                            elem.send_keys(Keys.RETURN)
                            self._wait(1)
                            return True
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Title set failed: {e}")
            
        return False


    def add_source_text(self, text: str, title: str = "Source") -> bool:
        """
        Add text content as a source to the current notebook.
        
        Args:
            text: Text content to add
            title: Optional title for the source
            
        Returns:
            True if successful
        """
        self.logger.info(f"Adding text source: {title[:30]}...")
        
        try:
            # Click "Quelle hinzufügen" / "Add source" button
            add_btn = self._find_button("Quelle hinzufügen", ["Add source", "hinzufügen", "Add"])
            
            if not add_btn:
                # Try to find in sources panel
                sources_header = self._find_by_text("Quellen")
                if sources_header:
                    self._click_safe(sources_header)
                    self._wait(1)
                add_btn = self._find_button("hinzufügen", ["Add"])
            
            if not add_btn:
                self.logger.error("Could not find Add source button")
                return False
            
            self._click_safe(add_btn)
            self._wait(2)
            
            # Look for "Text einfügen" / "Paste text" option
            paste_btn = self._find_by_text("Text einfügen")
            if not paste_btn:
                paste_btn = self._find_by_text("Paste text")
            if not paste_btn:
                paste_btn = self._find_by_text("Text")
            
            if paste_btn:
                self._click_safe(paste_btn)
                self._wait(1)
            
            # Find text input area
            text_input = None
            input_xpaths = [
                "//textarea",
                "//div[@contenteditable='true']",
                "//input[@type='text']",
            ]
            
            for xpath in input_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            text_input = elem
                            break
                except:
                    continue
                if text_input:
                    break
            
            if not text_input:
                self.logger.error("Could not find text input")
                return False
            
            # Enter text (in chunks for large content)
            text_input.clear()
            chunk_size = 5000
            for i in range(0, len(text), chunk_size):
                text_input.send_keys(text[i:i+chunk_size])
                self._wait(0.1)
            
            self._wait(1)
            
            # Submit (Ctrl+Enter or find submit button)
            submit_btn = self._find_button("Hinzufügen", ["Add", "Insert", "Einfügen"])
            if submit_btn:
                self._click_safe(submit_btn)
            else:
                text_input.send_keys(Keys.CONTROL + Keys.RETURN)
            
            self._wait(3)
            self.logger.info("Text source added successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Add text source failed: {e}")
            
        return False

    def add_source_file(self, file_path: str) -> bool:
        """
        Add a file as a source to the current notebook.
        
        Args:
            file_path: Path to the file (PDF, TXT, etc.)
            
        Returns:
            True if successful
        """
        self.logger.info(f"Adding file source: {file_path}")
        
        try:
            # Click "Quelle hinzufügen" / "Add source" button
            add_btn = self._find_button("Quelle hinzufügen", ["Add source", "hinzufügen"])
            
            if not add_btn:
                sources_header = self._find_by_text("Quellen")
                if sources_header:
                    self._click_safe(sources_header)
                    self._wait(1)
                add_btn = self._find_button("hinzufügen", ["Add"])
            
            if not add_btn:
                self.logger.error("Could not find Add source button")
                return False
            
            self._click_safe(add_btn)
            self._wait(2)
            
            # Find file input element
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            if file_inputs:
                # Send file path to the hidden file input
                file_inputs[0].send_keys(file_path)
                self._wait(5)  # Wait for upload
                self.logger.info("File source added successfully")
                return True
            else:
                # Try clicking upload button first
                upload_btn = self._find_by_text("Hochladen")
                if not upload_btn:
                    upload_btn = self._find_by_text("Upload")
                
                if upload_btn:
                    self._click_safe(upload_btn)
                    self._wait(1)
                    
                    # Try again to find file input
                    file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    if file_inputs:
                        file_inputs[0].send_keys(file_path)
                        self._wait(5)
                        self.logger.info("File source added successfully")
                        return True
            
            self.logger.error("Could not find file input element")
            return False
            
        except Exception as e:
            self.logger.error(f"Add file source failed: {e}")
            
        return False

    # =========================================================================
    # COMPLETE WORKFLOW
    # =========================================================================

    def run_complete_workflow(
        self,
        notebook_name: str = None,
        sources: List[str] = None,
        source_files: List[str] = None,
        materials: List[MaterialType] = None,
        download_when_ready: bool = False
    ) -> dict:
        """
        Run a complete workflow: create notebook, add sources, generate materials, optionally download.
        
        Args:
            notebook_name: Name for new notebook (or use existing if None)
            sources: List of text content to add as sources
            source_files: List of file paths to add as sources
            materials: List of material types to generate (default: all)
            download_when_ready: Whether to download materials after generation
            
        Returns:
            dict with workflow results
        """
        results = {
            'notebook_url': None,
            'sources_added': 0,
            'generation_results': {},
            'download_results': None,
            'errors': []
        }
        
        self.logger.info("=" * 70)
        self.logger.info("RUNNING COMPLETE NOTEBOOKLM WORKFLOW")
        self.logger.info("=" * 70)
        
        try:
            # Step 1: Create notebook if name provided
            if notebook_name:
                self.logger.info(f"\n📓 Step 1: Creating notebook '{notebook_name}'")
                results['notebook_url'] = self.create_new_notebook(notebook_name)
                if not results['notebook_url']:
                    results['errors'].append("Failed to create notebook")
                    return results
            
            # Step 2: Add sources
            if sources or source_files:
                self.logger.info(f"\n📁 Step 2: Adding sources")
                
                # Add text sources
                if sources:
                    for i, text in enumerate(sources):
                        title = f"Source_{i+1}"
                        if self.add_source_text(text, title):
                            results['sources_added'] += 1
                        else:
                            results['errors'].append(f"Failed to add text source {i+1}")
                
                # Add file sources
                if source_files:
                    for file_path in source_files:
                        if self.add_source_file(file_path):
                            results['sources_added'] += 1
                        else:
                            results['errors'].append(f"Failed to add file: {file_path}")
            
            # Step 3: Generate materials
            self.logger.info(f"\n🎬 Step 3: Generating materials")
            
            # List sources and process each
            source_list = self.list_sources()
            if source_list:
                results['generation_results'] = self.process_all_sources(materials=materials)
            else:
                self.logger.warning("No sources found to process")
            
            # Step 4: Download if requested
            if download_when_ready:
                self.logger.info(f"\n📥 Step 4: Downloading materials")
                self.logger.info("   Note: Materials may still be generating. Check back in a few minutes.")
                self._wait(10)  # Give some time for fast materials
                results['download_results'] = self.download_all_materials()
            
            self.logger.info("\n" + "=" * 70)
            self.logger.info("WORKFLOW COMPLETE")
            self.logger.info(f"  Notebook: {results.get('notebook_url', 'existing')}")
            self.logger.info(f"  Sources added: {results['sources_added']}")
            self.logger.info(f"  Errors: {len(results['errors'])}")
            self.logger.info("=" * 70)
            
        except Exception as e:
            results['errors'].append(str(e))
            self.logger.error(f"Workflow error: {e}")
            
        return results


# =========================================================================
# UTILITY FUNCTIONS
# =========================================================================

def quick_download_all(driver, notebook_url: str = None) -> dict:
    """
    Quick function to download all materials from a notebook.
    
    Args:
        driver: Selenium WebDriver
        notebook_url: Optional notebook URL to navigate to first
        
    Returns:
        Download results dict
    """
    automator = StudioAutomator(driver)
    
    if notebook_url:
        driver.get(notebook_url)
        time.sleep(5)
    
    return automator.download_all_materials()


def quick_generate_all(driver, notebook_url: str = None, materials: List[MaterialType] = None) -> dict:
    """
    Quick function to generate all materials for all sources.
    
    Args:
        driver: Selenium WebDriver
        notebook_url: Optional notebook URL to navigate to first
        materials: Optional list of specific materials to generate
        
    Returns:
        Generation results dict
    """
    automator = StudioAutomator(driver)
    
    if notebook_url:
        driver.get(notebook_url)
        time.sleep(5)
    
    return automator.process_all_sources(materials=materials)
