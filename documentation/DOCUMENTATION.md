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
# Clone or navigate to project
cd /path/to/notebook-lm-generation

# Run installer
./install.sh
```

The installer:
1. Creates virtual environment
2. Installs Python dependencies
3. Creates `nlmgen` command globally
4. Sets up configuration file

## 3.3 Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python -m src.main --help
```

## 3.4 Configuration

Edit `.env` file:
```bash
# Gemini API Key (optional - for topic splitting)
GEMINI_API_KEY=your_key_here

# Browser settings
HEADLESS_BROWSER=false

# Logging
LOG_LEVEL=INFO
```

---

# 4. Usage Guide

## 4.1 Basic Commands

### Single File Processing
```bash
# Process PDF with name prompt
nlmgen "/path/to/document.pdf"

# Process with custom notebook name
nlmgen "/path/to/document.pdf" --name "My Study Notes"

# Auto-name from filename
nlmgen "/path/to/document.pdf" --auto-name
```

### Batch Processing
```bash
# Process all PDFs in folder (prompts for each name)
nlmgen --batch "/path/to/folder/"

# Auto-name all notebooks
nlmgen --batch "/path/to/folder/" --auto-name

# Generate only specific materials
nlmgen --batch "/path/to/folder/" --materials audio video --auto-name
```

### Existing Notebook Operations
```bash
# List sources in notebook
nlmgen --notebook-url "https://notebooklm.google.com/notebook/..." --list-sources

# List generated materials
nlmgen --notebook-url "https://notebooklm.google.com/notebook/..." --list-materials

# Download all completed materials
nlmgen --notebook-url "https://notebooklm.google.com/notebook/..." --action download

# Generate materials for existing notebook
nlmgen --notebook-url "https://notebooklm.google.com/notebook/..." --action studio
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

## 4.3 Complete Workflow Example

```bash
# Step 1: Process all study PDFs
nlmgen --batch ~/Documents/study/ --materials audio mindmap --auto-name

# Step 2: Wait for generation (5-15 minutes)
# Materials generate in background

# Step 3: Download from each notebook
nlmgen --notebook-url "https://notebooklm.google.com/notebook/abc123" --action download
```

---

# 5. Implementation Details

## 5.1 Browser Automation Approach

The tool uses Selenium WebDriver with these strategies:

### Element Finding
Multiple fallback strategies for each UI element:
```python
ELEMENT_STRATEGIES = {
    "studio_tab": [
        (By.XPATH, "//*[contains(text(), 'Studio')]"),
        (By.XPATH, "//div[contains(@class, 'mdc-tab')]"),
        (By.CSS_SELECTOR, ".mdc-tab"),
    ],
    # ... more strategies
}
```

### Safe Clicking
JavaScript click fallback for reliability:
```python
def _click_safe(self, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        driver.execute_script("arguments[0].click();", element)
    except:
        element.click()
```

### German UI Support
The tool supports German NotebookLM interface:
- "Quellen" → Sources
- "Karteikarten" → Flashcards
- "Erstellen" → Create
- "Herunterladen" → Download

## 5.2 Studio Panel Automation

### Source Selection Flow
```python
# 1. Deselect all sources
deselect_all_sources()

# 2. Select single source
select_source(source_name)

# 3. Generate materials
for material in [AUDIO, VIDEO, MINDMAP, QUIZ, FLASHCARDS, INFOGRAPHIC]:
    generate_material(material)

# 4. Deselect and move to next
deselect_source(source_name)
```

### Language Selection (for Audio/Video/Infographic)
```python
def _select_english_language(self):
    # Click language dropdown (shows "Deutsch")
    dropdown = find_element("language_dropdown")
    click(dropdown)
    
    # Scroll to find English
    scroll_dropdown(3)
    
    # Click English option
    english = find_element("english_option")
    click(english)
```

## 5.3 Download Implementation

### Downloadable Types
- **Erklärvideo** → .mp4
- **Audio-Zusammenfassung** → .mp3
- **Mindmap** → .png

### Non-Downloadable (Share Only)
- Quiz
- Flashcards/Karteikarten
- Infographic
- Text reports

### Download Flow
```python
def download_item(item_name):
    # 1. Find "Mehr" (More) button for item
    mehr_btn = find_mehr_button(item_name)
    
    # 2. Click to open context menu
    click(mehr_btn)
    wait(1)
    
    # 3. Click "Herunterladen" (Download)
    click_menu_option("Herunterladen")
```

## 5.4 Error Handling

### Error Report Generation
On failure, the tool creates:
- Screenshot: `~/nlm_error_TIMESTAMP.png`
- HTML dump: `~/nlm_error_TIMESTAMP.html`
- JSON report: `~/nlm_error_report_TIMESTAMP.json`

### Common Errors Handled
- Element not found → Retry with fallback selectors
- Dialog appears → Close and continue
- Delete confirmation → Click cancel
- Share dialog → Close (no download available)

---

# 6. API Reference

## 6.1 StudioAutomator Class

```python
from src.generators.studio_automator import StudioAutomator, MaterialType

# Initialize
studio = StudioAutomator(driver)

# List sources
sources = studio.list_sources()

# Generate materials
studio.process_all_sources(
    source_patterns=["audiobook"],  # Optional filter
    materials=[MaterialType.AUDIO, MaterialType.MINDMAP]
)

# Download all
results = studio.download_all_materials()

# Create notebook
url = studio.create_new_notebook("My Notebook")

# Add sources
studio.add_source_file("/path/to/file.pdf")
studio.add_source_text("Content here", "Title")
```

## 6.2 MaterialType Enum

```python
class MaterialType(Enum):
    AUDIO = "audio"
    VIDEO = "video"
    MINDMAP = "mindmap"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"
    INFOGRAPHIC = "infographic"
```

## 6.3 CLI Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--batch FOLDER` | `-b` | Process all PDFs in folder |
| `--file FILE` | `-f` | Process single file |
| `--notebook-url URL` | `-n` | Use existing notebook |
| `--materials` | `-m` | Materials to generate |
| `--auto-name` | `-a` | Auto-name from filename |
| `--name NAME` | | Custom notebook name |
| `--list-sources` | `-l` | List sources |
| `--list-materials` | | List generated materials |
| `--download` | `-d` | Download all materials |
| `--action` | | studio, download, chat, etc. |
| `--headless` | | Run browser headless |

---

# 7. Troubleshooting

## 7.1 Common Issues

### "Element not found"
- The UI may have changed
- Wait longer for page load
- Check if logged into Google

### "Click not working"
- Element may be covered by overlay
- Try dismissing any dialogs first
- Check for welcome screens

### "No sources found"
- Navigate to correct notebook first
- Wait for page to fully load
- Check sources panel is visible

### "Download fails"
- Item may still be generating
- Item type may not support download
- Check Downloads folder permissions

## 7.2 Debug Mode

```bash
# Run with verbose logging
nlmgen document.pdf -v

# Check error reports
ls ~/nlm_error_*.png
ls ~/nlm_error_*.html
```

## 7.3 Reset Chrome Profile

```bash
# Remove cached profile
rm -rf ~/.nlm_chrome_profile

# Next run will create fresh profile
```

---

# Appendix A: Complete Example Session

```bash
# 1. Install
cd ~/IdeaProjects/notebook-lm-generation
./install.sh

# 2. First run - Chrome will open, login to Google
nlmgen ~/Documents/study/lecture.pdf --name "Networking Exam Prep"

# 3. Watch it create notebook and generate materials
# Output:
# 🌐 Initializing browser...
# 📓 Creating notebook: Networking Exam Prep
#    ✅ Created: https://notebooklm.google.com/notebook/abc123
# 📁 Adding source file...
#    ✅ Added: lecture.pdf
# 🎬 Generating materials...
#    ✅ Audio started
#    ✅ Video started
#    ✅ Mindmap started
#    ...

# 4. Wait 10-15 minutes, then download
nlmgen --notebook-url "https://notebooklm.google.com/notebook/abc123" --action download

# 5. Check Downloads folder
ls ~/Downloads/*.mp4 ~/Downloads/*.mp3 ~/Downloads/*.png
```

---

# Appendix B: Batch Processing Multiple Courses

```bash
# Organize files
mkdir -p ~/study/{networking,os,teamwork}
mv networking*.pdf ~/study/networking/
mv os*.pdf ~/study/os/
mv team*.pdf ~/study/teamwork/

# Process each course with auto-naming
for course in networking os teamwork; do
    echo "Processing $course..."
    nlmgen --batch ~/study/$course/ --materials audio mindmap --auto-name
done

# Result: One notebook per PDF, each with audio and mindmap
```

---

**End of Documentation**
