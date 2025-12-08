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
