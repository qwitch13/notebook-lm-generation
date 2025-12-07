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
