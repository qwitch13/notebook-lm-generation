# NotebookLM Generation Tool
## Complete Technical Documentation

**Version:** 1.0.0  
**Date:** December 2024  
**Author:** Hecate  

---

# Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Installation](#3-installation)
4. [Usage Guide](#4-usage-guide)
5. [Implementation Details](#5-implementation-details)
6. [API Reference](#6-api-reference)
7. [Troubleshooting](#7-troubleshooting)
8. [How to Approach This Coding Project](#8-how-to-approach-this-coding-project)

---

# 1. Project Overview

## 1.1 What is NotebookLM Generation Tool?

The NotebookLM Generation Tool is a Python-based automation framework that interfaces with Google's NotebookLM service to automatically generate educational materials from PDF documents and other content sources.

## 1.2 Key Features

- **Batch Processing**: Process entire folders of PDFs automatically
- **Material Generation**: Create Audio Summaries, Videos, Mindmaps, Quizzes, Flashcards, and Infographics
- **Notebook Management**: Automatically create and name notebooks
- **Download Automation**: Bulk download all generated materials
- **Browser Automation**: Uses Selenium with persistent Chrome profiles
- **Gemini API Integration**: Optional AI-powered content splitting

## 1.3 Why Browser Automation?

Google NotebookLM's API is **Enterprise-only** (paid). The public/consumer version has no API access. Browser automation is the only approach for free accounts.

**Enterprise APIs (Not Used):**
- NotebookLM Enterprise API: Requires GCP project + Enterprise license
- Standalone Podcast API: Requires Discovery Engine API access

---

# 2. Architecture

## 2.1 Project Structure

```
notebook-lm-generation/
├── src/
│   ├── main.py                    # CLI entry point
│   ├── auth/
│   │   └── google_auth.py         # Chrome profile & authentication
│   ├── config/
│   │   └── settings.py            # Configuration management
│   ├── generators/
│   │   ├── notebooklm.py          # Core browser automation (1050 lines)
│   │   ├── studio_automator.py    # Studio panel automation (1546 lines)
│   │   ├── gemini_client.py       # Gemini API client
│   │   ├── audiobook.py           # Audiobook chapter generation
│   │   ├── flashcards.py          # Flashcard generation
│   │   ├── quiz.py                # Quiz generation
│   │   └── ...                    # Other generators
│   ├── processors/
│   │   ├── content_processor.py   # PDF/text processing
│   │   └── topic_splitter.py      # Content splitting with Gemini
│   └── utils/
│       ├── logger.py              # Logging utilities
│       ├── downloader.py          # File download utilities
│       └── progress_reporter.py   # Progress tracking
├── install.sh                     # Installation script
├── uninstall.sh                   # Uninstallation script
├── requirements.txt               # Python dependencies
└── test_studio_full.py            # Standalone test script
```

## 2.2 Core Components

### NotebookLMClient (notebooklm.py)
The main browser automation client. Handles:
- Navigation to NotebookLM
- Notebook creation
- Source management
- Chat interactions
- Basic audio generation

### StudioAutomator (studio_automator.py)
Advanced Studio panel automation. Handles:
- Source selection/deselection
- Material generation (all 6 types)
- Language selection (English for audio/video/infographic)
- Material download
- Complete workflow orchestration

### GoogleAuthenticator (google_auth.py)
Chrome browser management:
- Persistent profile at `~/.nlm_chrome_profile`
- Session persistence (login once, reuse)
- Headless mode support

## 2.3 Data Flow

```
Input (PDF/Text)
       │
       ▼
┌─────────────────┐
│ ContentProcessor │  ← Extracts text from PDF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TopicSplitter  │  ← Splits into chapters (optional)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ NotebookLMClient│  ← Creates notebook, adds sources
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ StudioAutomator │  ← Generates all materials
└────────┬────────┘
         │
         ▼
    Downloads/
    (MP4, MP3, PNG)
```

---

# 3. Installation

## 3.1 Prerequisites

- Python 3.11 or higher
- Google Chrome browser
- Google account (logged into Chrome)

## 3.2 Quick Install

```bash
cd /path/to/notebook-lm-generation
./install.sh
```

The installer:
1. Creates virtual environment
2. Installs Python dependencies
3. Creates `nlmgen` command globally
4. Sets up configuration file

## 3.3 Manual Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main --help
```

## 3.4 Configuration

Edit `.env` file:
```bash
GEMINI_API_KEY=your_key_here
HEADLESS_BROWSER=false
LOG_LEVEL=INFO
```

---

# 4. Usage Guide

## 4.1 Basic Commands

### Single File Processing
```bash
nlmgen "/path/to/document.pdf"
nlmgen "/path/to/document.pdf" --name "My Study Notes"
nlmgen "/path/to/document.pdf" --auto-name
```

### Batch Processing
```bash
nlmgen --batch "/path/to/folder/"
nlmgen --batch "/path/to/folder/" --auto-name
nlmgen --batch "/path/to/folder/" --materials audio video --auto-name
```

### Existing Notebook Operations
```bash
nlmgen --notebook-url "URL" --list-sources
nlmgen --notebook-url "URL" --list-materials
nlmgen --notebook-url "URL" --action download
nlmgen --notebook-url "URL" --action studio
```

## 4.2 Material Types

| Material | Flag | Time | Language | Download |
|----------|------|------|----------|----------|
| Audio Summary | `audio` | 3-10 min | English | .mp3 |
| Video Overview | `video` | 5-15 min | English | .mp4 |
| Mindmap | `mindmap` | 2-5 min | Auto | .png |
| Quiz | `quiz` | 1-3 min | Auto | No |
| Flashcards | `flashcards` | 1-3 min | Auto | No |
| Infographic | `infographic` | 3-8 min | English | No |

---

# 5. Implementation Details

## 5.1 Browser Automation Approach

Multiple fallback strategies for each UI element:
```python
ELEMENT_STRATEGIES = {
    "studio_tab": [
        (By.XPATH, "//*[contains(text(), 'Studio')]"),
        (By.XPATH, "//div[contains(@class, 'mdc-tab')]"),
        (By.CSS_SELECTOR, ".mdc-tab"),
    ],
}
```

### Safe Clicking
```python
def _click_safe(self, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    driver.execute_script("arguments[0].click();", element)
```

### German UI Support
- "Quellen" → Sources
- "Karteikarten" → Flashcards
- "Erstellen" → Create
- "Herunterladen" → Download

## 5.2 Studio Panel Automation Flow

```python
deselect_all_sources()
select_source(source_name)
for material in [AUDIO, VIDEO, MINDMAP, QUIZ, FLASHCARDS, INFOGRAPHIC]:
    generate_material(material)
deselect_source(source_name)
```

## 5.3 Download Implementation

Downloadable: Erklärvideo (.mp4), Audio-Zusammenfassung (.mp3), Mindmap (.png)
Non-Downloadable: Quiz, Flashcards, Infographic

---

# 6. API Reference

## 6.1 StudioAutomator Class

```python
from src.generators.studio_automator import StudioAutomator, MaterialType

studio = StudioAutomator(driver)
sources = studio.list_sources()
studio.process_all_sources(materials=[MaterialType.AUDIO, MaterialType.MINDMAP])
results = studio.download_all_materials()
url = studio.create_new_notebook("My Notebook")
studio.add_source_file("/path/to/file.pdf")
```

## 6.2 CLI Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--batch FOLDER` | | Process all PDFs in folder |
| `--notebook-url URL` | | Use existing notebook |
| `--materials` | `-m` | Materials to generate |
| `--auto-name` | `-a` | Auto-name from filename |
| `--name NAME` | | Custom notebook name |
| `--list-sources` | | List sources |
| `--list-materials` | | List generated materials |
| `--action` | | studio, download, chat |
| `--headless` | | Run browser headless |

---

# 7. Troubleshooting

## 7.1 Common Issues

**"Element not found"**
- Wait longer for page load
- Check if logged into Google
- UI may have changed

**"Download fails"**
- Item may still be generating
- Item type may not support download

## 7.2 Debug Mode

```bash
nlmgen document.pdf -v
ls ~/nlm_error_*.png
```

## 7.3 Reset Chrome Profile

```bash
rm -rf ~/.nlm_chrome_profile
```

---

# 8. How to Approach This Coding Project

## 8.1 Understanding the Challenge

1. **No Official API**: Google only provides APIs for Enterprise customers
2. **Dynamic Web Interface**: JavaScript-heavy UI with changing selectors
3. **Authentication**: Google's login flow has anti-bot measures
4. **Localization**: Interface may be in different languages

## 8.2 Development Phases

### Phase 1: Browser Foundation
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def setup_browser():
    options = Options()
    options.add_argument("--user-data-dir=~/.nlm_chrome_profile")
    driver = webdriver.Chrome(options=options)
    return driver
```

### Phase 2: Robust Element Finding
```python
def find_element_robust(driver, strategies):
    for by, selector in strategies:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((by, selector))
            )
            return element
        except:
            continue
    raise Exception("Element not found")
```

### Phase 3: Build Core Interactions
1. Navigate to NotebookLM homepage
2. Create new notebook
3. Add source file (PDF upload)
4. Navigate Studio panel
5. Click generate buttons

### Phase 4: Material Generation
```python
def generate_material(material_type):
    card = find_material_card(material_type)
    click_safe(card)
    if material_type in [AUDIO, VIDEO, INFOGRAPHIC]:
        select_english_language()
    create_btn = find_create_button()
    click_safe(create_btn)
```

## 8.3 Testing Strategy

1. **Manual First**: Run each function in Python REPL
2. **Visual Debugging**: Keep browser visible
3. **Incremental**: Test each interaction before combining
4. **Error Capture**: Save HTML and screenshots on failure

```python
def capture_error_state(driver, error):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    driver.save_screenshot(f"~/nlm_error_{timestamp}.png")
    with open(f"~/nlm_error_{timestamp}.html", "w") as f:
        f.write(driver.page_source)
```

## 8.4 Common Pitfalls

1. **Clicking too fast**: Always wait after clicks
2. **Stale elements**: Re-find elements after page changes
3. **Overlays**: Dismiss popups before clicking
4. **Scrolling**: Scroll elements into view
5. **Language**: Handle multiple UI languages

---

**End of Documentation**
