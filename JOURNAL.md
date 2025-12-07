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
