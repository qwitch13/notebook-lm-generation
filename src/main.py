#!/usr/bin/env python3
"""
NotebookLM Generation Tool - Main Entry Point

Automated generation of learning materials from educational content.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config.settings import get_settings, ProcessingStep
from .auth.google_auth import GoogleAuthenticator
from .processors.content_processor import ContentProcessor
from .processors.topic_splitter import TopicSplitter
from .generators.notebooklm import NotebookLMClient
from .generators.gemini_client import GeminiClient
from .generators.handout import HandoutGenerator
from .generators.cheatsheet import CheatsheetGenerator
from .generators.mindmap import MindmapGenerator
from .generators.audiobook import AudiobookGenerator
from .generators.story import StoryGenerator
from .generators.strategy import StrategyGenerator
from .generators.flashcards import FlashcardGenerator
from .generators.quiz import QuizGenerator
from .generators.discussion import DiscussionGenerator
from .utils.logger import setup_logger, get_logger, LogContext
from .utils.progress_reporter import ProgressReporter
from .utils.downloader import Downloader


class NotebookLMGenerator:
    """
    Main orchestrator for the NotebookLM Generation pipeline.

    Coordinates all processing steps from content input to final output.
    """

    def __init__(
        self,
        input_path: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = False,
        output_dir: Optional[Path] = None,
        gemini_api_key: Optional[str] = None,
        notebook_url: Optional[str] = None,
        no_api: bool = False,
        action: str = "full",
        chat_message: Optional[str] = None
    ):
        self.input_path = Path(input_path) if not input_path.startswith("http") else input_path
        self.email = email
        self.password = password
        self.headless = headless
        self.settings = get_settings()
        self.notebook_url = notebook_url  # Use existing NotebookLM notebook
        self.no_api = no_api  # Don't use Gemini API, only NotebookLM chat
        self.action = action  # Single action mode: audio, chat, flashcards, quiz, summary, full
        self.chat_message = chat_message  # Message for chat action

        # Determine output directory
        if output_dir:
            self.output_dir = output_dir
        elif isinstance(self.input_path, Path):
            self.output_dir = self.input_path.parent / f"{self.input_path.stem}_output"
        else:
            self.output_dir = Path.cwd() / "output"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize logger
        self.logger = setup_logger(
            log_level=self.settings.log_level,
            log_file=self.settings.log_file,
            output_dir=self.output_dir
        )

        # Initialize progress reporter
        self.progress = ProgressReporter(
            update_interval=self.settings.progress_update_interval
        )

        # Initialize downloader
        self.downloader = Downloader(self.output_dir)

        # Initialize components (will be set up in run())
        self.authenticator: Optional[GoogleAuthenticator] = None
        self.notebooklm: Optional[NotebookLMClient] = None
        self.gemini: Optional[GeminiClient] = None
        self.gemini_api_key = gemini_api_key or self.settings.gemini_api_key

    def run(self) -> bool:
        """
        Execute the generation pipeline.

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info("NotebookLM Generation Tool")
        self.logger.info(f"Input: {self.input_path}")
        self.logger.info(f"Output: {self.output_dir}")
        self.logger.info(f"Action: {self.action}")
        self.logger.info("=" * 60)

        self.progress.start()

        try:
            # Step 1: Authentication
            if not self._authenticate():
                return False

            # If single action mode, run only that action
            if self.action != "full":
                return self._run_single_action()

            # Full pipeline mode
            # Step 2: Load and process content
            content = self._load_content()
            if not content:
                return False

            # Step 3: Split into topics
            split_content = self._split_topics(content)
            if not split_content:
                return False

            # Step 4: Generate all materials
            self._generate_all_materials(split_content)

            # Step 5: Open Gemini at the end
            self._open_gemini_final()

            # Step 6: Final summary
            self._finalize()

            return True

        except KeyboardInterrupt:
            self.logger.warning("Process interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return False
        finally:
            self.progress.stop()
            self._cleanup()

    def _run_single_action(self) -> bool:
        """Run a single action on the notebook (audio, chat, flashcards, etc)."""
        print(f"\n{'=' * 50}")
        print(f"🎯 RUNNING SINGLE ACTION: {self.action}")
        print(f"{'=' * 50}\n")
        self.logger.info(f"Running single action: {self.action}")
        
        if not self.notebooklm:
            self.logger.error("NotebookLM client not initialized")
            print("❌ NotebookLM client not initialized!")
            return False
        
        print("✅ NotebookLM client is available")
        
        # Give user time to see the browser
        import time
        print("⏳ Waiting 5 seconds before starting action...")
        time.sleep(5)
        
        try:
            if self.action == "audio":
                print("🎵 Starting audio generation...")
                self.logger.info("Generating audio overview...")
                result = self.notebooklm.generate_audio_overview()
                print(f"   Audio result: {result}")
                if result:
                    self.logger.info("✅ Audio generation started successfully!")
                    print("✅ Audio generation started successfully!")
                else:
                    self.logger.error("❌ Failed to start audio generation")
                    print("❌ Failed to start audio generation")
                return result
            
            elif self.action == "chat":
                print("💬 Starting chat...")
                if not self.chat_message:
                    self.logger.error("No message provided for chat action. Use --chat-message")
                    print("❌ No chat message provided!")
                    return False
                self.logger.info(f"Sending chat message: {self.chat_message[:50]}...")
                print(f"   Sending: {self.chat_message[:50]}...")
                response = self.notebooklm.send_chat_message(self.chat_message)
                print(f"   Response received: {bool(response)}")
                if response:
                    self.logger.info("✅ Got response from NotebookLM:")
                    print("\n" + "=" * 60)
                    print(response)
                    print("=" * 60 + "\n")
                    return True
                else:
                    self.logger.error("❌ Failed to get response")
                    print("❌ Failed to get response")
                    return False
            
            elif self.action == "flashcards":
                self.logger.info("Generating flashcards...")
                result = self.notebooklm.generate_flashcards()
                return bool(result)
            
            elif self.action == "quiz":
                self.logger.info("Generating quiz...")
                result = self.notebooklm.generate_quiz()
                return bool(result)
            
            elif self.action == "upload":
                print("📁 Starting file upload...")
                if not isinstance(self.input_path, Path) or not self.input_path.exists():
                    self.logger.error("No valid file provided for upload action")
                    print(f"❌ No valid file: {self.input_path}")
                    return False
                self.logger.info(f"Uploading file: {self.input_path}")
                result = self.notebooklm.upload_file_source(str(self.input_path))
                if result:
                    self.logger.info("✅ File uploaded successfully!")
                    print("✅ File uploaded successfully!")
                else:
                    self.logger.error("❌ File upload failed")
                    print("❌ File upload failed")
                return result
            
            elif self.action == "summary":
                self.logger.info("Generating summary...")
                result = self.notebooklm.generate_summary()
                if result:
                    self.logger.info("✅ Summary generated:")
                    print("\n" + "=" * 60)
                    print(result)
                    print("=" * 60 + "\n")
                    return True
                return False
            
            else:
                self.logger.error(f"Unknown action: {self.action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Action failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _authenticate(self) -> bool:
        """Authenticate with Google."""
        self.progress.set_step(ProcessingStep.AUTHENTICATION, "Logging into Google...")

        try:
            self.authenticator = GoogleAuthenticator(
                email=self.email,
                password=self.password,
                headless=self.headless
            )

            # Always attempt login - it will use saved session or prompt for manual login
            success = self.authenticator.login_google()
            if not success:
                self.progress.fail_step(ProcessingStep.AUTHENTICATION, "Login failed")
                return False

            # Initialize clients
            self.notebooklm = NotebookLMClient(self.authenticator)

            # Navigate to existing notebook if URL provided
            if self.notebook_url:
                self.logger.info(f"Using existing NotebookLM notebook: {self.notebook_url}")
                # Use the NotebookLMClient's navigate method for proper waiting and setup
                self.notebooklm.navigate_to_notebook(self.notebook_url)

            # Initialize Gemini client (skip if --no-api)
            if self.no_api:
                self.logger.info("Running in NO-API mode - using only NotebookLM chat for generation")
                self.gemini = None
            else:
                self.gemini = GeminiClient(
                    api_key=self.gemini_api_key,
                    authenticator=self.authenticator,
                    use_browser=False  # Use API by default
                )

            self.progress.complete_step(ProcessingStep.AUTHENTICATION)
            return True

        except Exception as e:
            self.progress.fail_step(ProcessingStep.AUTHENTICATION, str(e))
            self.logger.error(f"Authentication failed: {e}")
            return False

    def _load_content(self):
        """Load and process input content."""
        self.progress.set_step(ProcessingStep.CONTENT_LOADING, "Processing input content...")

        try:
            processor = ContentProcessor()
            content = processor.process(self.input_path)

            self.logger.info(f"Loaded content: {content.title}")
            self.logger.info(f"Word count: {content.word_count}")

            self.progress.complete_step(ProcessingStep.CONTENT_LOADING)
            return content

        except Exception as e:
            self.progress.fail_step(ProcessingStep.CONTENT_LOADING, str(e))
            self.logger.error(f"Content loading failed: {e}")
            return None

    def _split_topics(self, content):
        """Split content into topics."""
        self.progress.set_step(ProcessingStep.TOPIC_SPLITTING, "Analyzing content and splitting into topics...")

        try:
            # Use fallback splitting if --no-api mode
            api_key = None if self.no_api else self.gemini_api_key
            splitter = TopicSplitter(api_key=api_key)
            split_content = splitter.split(content)

            self.logger.info(f"Split into {split_content.total_topics} topics")
            for topic in split_content.topics:
                self.logger.info(f"  - {topic.title}")

            self.progress.complete_step(ProcessingStep.TOPIC_SPLITTING)
            return split_content

        except Exception as e:
            self.progress.fail_step(ProcessingStep.TOPIC_SPLITTING, str(e))
            self.logger.error(f"Topic splitting failed: {e}")
            return None

    def _generate_all_materials(self, split_content):
        """Generate all learning materials."""
        import traceback

        self.logger.info("Starting material generation...")
        self.logger.debug(f"NotebookLM client: {self.notebooklm}")
        self.logger.debug(f"Gemini client: {self.gemini}")

        topics = split_content.topics
        self.logger.info(f"Processing {len(topics)} topics")

        # Set up generators with error handling
        try:
            self.logger.debug("Initializing generators...")
            handout_gen = HandoutGenerator(self.notebooklm, self.gemini, self.downloader)
            cheatsheet_gen = CheatsheetGenerator(self.notebooklm, self.gemini, self.downloader)
            mindmap_gen = MindmapGenerator(self.notebooklm, self.gemini, self.downloader)
            audiobook_gen = AudiobookGenerator(self.notebooklm, self.gemini, self.downloader)
        except Exception as e:
            self.logger.error(f"Failed to initialize generators: {e}")
            self.logger.error(traceback.format_exc())
            return
        try:
            story_gen = StoryGenerator(self.gemini, self.downloader)
            strategy_gen = StrategyGenerator(self.gemini, self.downloader)
            flashcard_gen = FlashcardGenerator(self.notebooklm, self.gemini, self.downloader)
            quiz_gen = QuizGenerator(self.gemini, self.notebooklm, self.downloader)
            discussion_gen = DiscussionGenerator(self.gemini, self.notebooklm, self.downloader)
            self.logger.debug("All generators initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize remaining generators: {e}")
            self.logger.error(traceback.format_exc())
            return

        # Generate for each topic
        for topic_idx, topic in enumerate(topics):
            self.logger.info(f"\n--- Processing topic {topic_idx + 1}/{len(topics)} ---")
            self.logger.info(f"\n{'='*40}")
            self.logger.info(f"Processing Topic {topic.id}: {topic.title}")
            self.logger.info(f"{'='*40}")

            # Videos (via NotebookLM)
            self.progress.set_step(
                ProcessingStep.VIDEO_GENERATION,
                f"Generating video for: {topic.title}"
            )
            video_ok = False
            try:
                self.logger.debug(f"NotebookLM client exists: {self.notebooklm is not None}")
                if self.notebooklm:
                    # Skip notebook creation if using existing notebook URL
                    if self.notebook_url:
                        self.logger.info("Using existing notebook - skipping notebook creation")
                        # Just generate audio from existing notebook
                        self.logger.debug("Generating audio overview from existing notebook...")
                        gen_ok = self.notebooklm.generate_audio_overview()
                        video_ok = bool(gen_ok)
                    else:
                        # Create new notebook for each topic (original behavior)
                        self.logger.debug("Creating notebook...")
                        self.notebooklm.create_notebook(topic.title)
                        self.logger.debug("Adding text source...")
                        src_ok = self.notebooklm.add_text_source(topic.content, topic.title)
                        if src_ok:
                            self.logger.debug("Generating audio overview...")
                            gen_ok = self.notebooklm.generate_audio_overview()
                            video_ok = bool(gen_ok)
                            self.logger.debug(f"Audio generation result: {gen_ok}")
                        else:
                            self.logger.warning("Add source step did not complete successfully; skipping audio generation")
                else:
                    self.logger.warning("NotebookLM client is None, skipping video generation")
            except Exception as e:
                self.logger.error(f"Video generation failed for {topic.title}: {e}")
                self.logger.error(traceback.format_exc())
                video_ok = False

            if video_ok:
                self.progress.complete_step(ProcessingStep.VIDEO_GENERATION)
            else:
                self.progress.fail_step(
                    ProcessingStep.VIDEO_GENERATION,
                    "Notebook creation/source addition/audio generation did not complete; manual action may be required"
                )

            # Handouts
            self.progress.set_step(
                ProcessingStep.HANDOUT_GENERATION,
                f"Generating handout for: {topic.title}"
            )
            try:
                handout = handout_gen.generate(topic)
                if handout:
                    handout_gen.save(topic, handout)
            except Exception as e:
                self.logger.warning(f"Handout generation failed: {e}")

            # Cheatsheets
            self.progress.set_step(
                ProcessingStep.CHEATSHEET_GENERATION,
                f"Generating cheatsheet for: {topic.title}"
            )
            try:
                cheatsheet = cheatsheet_gen.generate(topic)
                if cheatsheet:
                    cheatsheet_gen.save(topic, cheatsheet)
            except Exception as e:
                self.logger.warning(f"Cheatsheet generation failed: {e}")

            # Mindmaps
            self.progress.set_step(
                ProcessingStep.MINDMAP_GENERATION,
                f"Generating mindmap for: {topic.title}"
            )
            try:
                mindmap = mindmap_gen.generate(topic)
                if mindmap:
                    mindmap_gen.save(topic, mindmap)
            except Exception as e:
                self.logger.warning(f"Mindmap generation failed: {e}")

            # Audiobook chapters
            self.progress.set_step(
                ProcessingStep.AUDIOBOOK_GENERATION,
                f"Generating audiobook for: {topic.title}"
            )
            try:
                script = audiobook_gen.generate_script(topic)
                if script:
                    audiobook_gen.save_script(topic, script)
            except Exception as e:
                self.logger.warning(f"Audiobook generation failed: {e}")

            # Stories (Fantasy + Sci-Fi)
            self.progress.set_step(
                ProcessingStep.STORY_GENERATION,
                f"Generating stories for: {topic.title}"
            )
            try:
                stories = story_gen.generate(topic)
                story_gen.save(topic, stories)
            except Exception as e:
                self.logger.warning(f"Story generation failed: {e}")

            # Flashcards (NotebookLM + Anki)
            self.progress.set_step(
                ProcessingStep.FLASHCARD_GENERATION,
                f"Generating flashcards for: {topic.title}"
            )
            try:
                deck = flashcard_gen.generate(topic)
                flashcard_gen.save_markdown(deck)
                flashcard_gen.save_anki(deck)  # Also creates Anki deck
            except Exception as e:
                self.logger.warning(f"Flashcard generation failed: {e}")

            # Quiz
            self.progress.set_step(
                ProcessingStep.QUIZ_GENERATION,
                f"Generating quiz for: {topic.title}"
            )
            try:
                quiz = quiz_gen.generate(topic)
                quiz_gen.save(quiz)
                quiz_gen.save_with_answers(quiz)
            except Exception as e:
                self.logger.warning(f"Quiz generation failed: {e}")

            # Podium Discussion
            self.progress.set_step(
                ProcessingStep.DISCUSSION_GENERATION,
                f"Generating discussion for: {topic.title}"
            )
            try:
                discussion = discussion_gen.generate(topic, with_video=False)
                discussion_gen.save(discussion)
            except Exception as e:
                self.logger.warning(f"Discussion generation failed: {e}")

        # Generate overall strategy paper
        self.progress.set_step(
            ProcessingStep.STRATEGY_GENERATION,
            "Generating learning strategy paper..."
        )
        try:
            strategy = strategy_gen.generate(split_content)
            if strategy:
                strategy_gen.save(split_content, strategy)
        except Exception as e:
            self.logger.warning(f"Strategy generation failed: {e}")

        self.progress.complete_step(ProcessingStep.STRATEGY_GENERATION)

    def _open_gemini_final(self):
        """Open Gemini in browser at the end."""
        self.logger.info("Opening Gemini in browser...")
        try:
            if self.authenticator:
                self.authenticator.open_gemini_in_new_tab()
                self.logger.info("Gemini opened in new tab")
        except Exception as e:
            self.logger.warning(f"Could not open Gemini: {e}")

    def _finalize(self):
        """Finalize and show summary."""
        self.progress.set_step(ProcessingStep.DOWNLOADING, "Finalizing outputs...")

        # Get download summary
        summary = self.downloader.get_summary()

        self.logger.info("\n" + "=" * 60)
        self.logger.info("GENERATION COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"\nOutput directory: {self.output_dir}")
        self.logger.info("\nGenerated files:")

        total_files = 0
        for content_type, info in summary.items():
            if info["count"] > 0:
                self.logger.info(f"  {content_type}: {info['count']} files")
                total_files += info["count"]

        self.logger.info(f"\nTotal files generated: {total_files}")
        self.logger.info("=" * 60)

        self.progress.complete_step(ProcessingStep.DOWNLOADING)
        self.progress.set_step(ProcessingStep.COMPLETED, "All done!")

    def _cleanup(self):
        """Clean up resources."""
        if self.authenticator:
            # Don't close browser - leave it open for user
            pass


def get_config_path() -> Path:
    """Get the path to the config file."""
    config_dir = Path.home() / ".config" / "nlmgen"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config"


def load_config() -> dict:
    """Load the config file as a dictionary."""
    config_path = get_config_path()
    config = {}
    if config_path.exists():
        for line in config_path.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def save_config(config: dict) -> None:
    """Save the config dictionary to file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")


def save_api_key(api_key: str) -> None:
    """Save the Gemini API key to the config file."""
    config = load_config()
    config["GEMINI_API_KEY"] = api_key
    save_config(config)


def load_api_key() -> Optional[str]:
    """Load the Gemini API key from the config file."""
    return load_config().get("GEMINI_API_KEY")


def save_user_credentials(email: str, password: str) -> None:
    """Save Google user credentials to the config file."""
    config = load_config()
    config["GOOGLE_EMAIL"] = email
    config["GOOGLE_PASSWORD"] = password
    save_config(config)


def load_user_credentials() -> tuple[Optional[str], Optional[str]]:
    """Load Google user credentials from the config file."""
    config = load_config()
    return config.get("GOOGLE_EMAIL"), config.get("GOOGLE_PASSWORD")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NotebookLM Generation Tool - Generate learning materials from content"
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Input file path (PDF, TXT) or URL"
    )

    parser.add_argument(
        "-e", "--email",
        help="Google account email"
    )

    parser.add_argument(
        "-p", "--password",
        help="Google account password"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output directory (default: same as input)"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )

    parser.add_argument(
        "--api-key",
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )

    parser.add_argument(
        "--notebook-url",
        help="Use existing NotebookLM notebook URL (skip creating new notebooks)"
    )

    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Don't use Gemini API - use only NotebookLM chat for generation (unlimited)"
    )

    parser.add_argument(
        "--action",
        choices=["audio", "chat", "flashcards", "quiz", "summary", "upload", "full", "studio", "download"],
        default="full",
        help="Action: audio, chat, flashcards, quiz, summary, upload (file to notebook), full, studio, download"
    )

    parser.add_argument(
        "--chat-message",
        help="Message to send when using --action chat"
    )

    # Studio/Batch options
    parser.add_argument(
        "--batch",
        metavar="FOLDER",
        help="Batch process all PDFs in folder (creates notebook per file)"
    )

    parser.add_argument(
        "--materials", "-m",
        nargs="+",
        choices=["audio", "video", "mindmap", "quiz", "flashcards", "infographic"],
        help="Materials to generate in studio mode (default: all)"
    )

    parser.add_argument(
        "--auto-name", "-a",
        action="store_true",
        help="Auto-name notebooks from filenames (no prompts)"
    )

    parser.add_argument(
        "--name",
        help="Custom notebook name"
    )

    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List sources in notebook and exit"
    )

    parser.add_argument(
        "--list-materials",
        action="store_true",
        help="List generated materials in notebook"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--add-key",
        metavar="KEY",
        help="Save Gemini API key to config file for future use"
    )

    parser.add_argument(
        "--save-user",
        action="store_true",
        help="Save provided -e/--email and -p/--password to config file for future use"
    )

    args = parser.parse_args()

    # Handle --save-user option
    if args.save_user:
        if not args.email or not args.password:
            parser.error("--save-user requires both -e/--email and -p/--password")
        save_user_credentials(args.email, args.password)
        print(f"Google credentials saved to {get_config_path()}")

    # Handle --add-key option
    if args.add_key:
        save_api_key(args.add_key)
        print(f"Gemini API key saved to {get_config_path()}")

    # Exit early if only saving config (no input provided)
    if args.input is None and not args.batch:
        if args.add_key or args.save_user:
            sys.exit(0)
        if not args.notebook_url:
            parser.error("the following arguments are required: input (or --batch or --notebook-url)")

    # Load saved credentials if not provided via CLI
    saved_email, saved_password = load_user_credentials()
    email = args.email or saved_email
    password = args.password or saved_password

    # Determine API key (priority: --api-key > env var > saved config)
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or load_api_key()

    # Set up environment
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key

    output_dir = Path(args.output) if args.output else None

    # =========================================================================
    # BATCH/STUDIO MODE
    # =========================================================================
    if args.batch or args.action in ["studio", "download"] or args.list_sources or args.list_materials:
        from .generators.studio_automator import StudioAutomator, MaterialType
        from .auth.google_auth import GoogleAuthenticator
        from .generators.notebooklm import NotebookLMClient
        
        # Parse materials
        materials = None
        if args.materials:
            material_map = {
                "audio": MaterialType.AUDIO,
                "video": MaterialType.VIDEO,
                "mindmap": MaterialType.MINDMAP,
                "quiz": MaterialType.QUIZ,
                "flashcards": MaterialType.FLASHCARDS,
                "infographic": MaterialType.INFOGRAPHIC,
            }
            materials = [material_map[m] for m in args.materials]
        
        # Initialize browser
        print("🌐 Initializing browser...")
        auth = GoogleAuthenticator(headless=args.headless)
        driver = auth.get_driver()
        
        if not driver:
            print("❌ Failed to initialize browser")
            sys.exit(1)
        
        try:
            studio = StudioAutomator(driver)
            
            # BATCH MODE
            if args.batch:
                from pathlib import Path as P
                folder = P(args.batch)
                files = sorted(folder.glob("*.pdf"))
                
                if not files:
                    print(f"❌ No PDFs found in {args.batch}")
                    sys.exit(1)
                
                print(f"📁 Found {len(files)} PDFs")
                
                for i, f in enumerate(files, 1):
                    print(f"\n[{i}/{len(files)}] {f.name}")
                    
                    # Get notebook name
                    default_name = f.stem.replace('_', ' ').replace('-', ' ').title()
                    if args.name:
                        nb_name = args.name
                    elif args.auto_name:
                        nb_name = default_name
                    else:
                        print(f"📓 Notebook name (Enter for '{default_name}'): ", end="")
                        user_input = input().strip()
                        nb_name = user_input if user_input else default_name
                    
                    # Create notebook
                    nb_url = studio.create_new_notebook(nb_name)
                    if nb_url:
                        print(f"   ✅ Created: {nb_url}")
                        studio.add_source_file(str(f))
                        import time
                        time.sleep(10)
                        studio.process_all_sources(materials=materials)
                    else:
                        print(f"   ❌ Failed")
                
                print("\n✅ Batch complete!")
                sys.exit(0)
            
            # EXISTING NOTEBOOK MODE
            if args.notebook_url:
                client = NotebookLMClient(auth)
                client.navigate_to_notebook(args.notebook_url)
                import time
                time.sleep(3)
            
            # List sources
            if args.list_sources:
                sources = studio.list_sources()
                print("\n📋 Sources:")
                for s in sources:
                    print(f"  • {s.name}")
                sys.exit(0)
            
            # List materials
            if args.list_materials:
                mats = studio.list_generated_materials()
                print("\n📋 Materials:")
                for m in mats:
                    status = "⏳" if m['status'] == 'generating' else "✅"
                    print(f"  {status} [{m['type']}] {m['name'][:50]}")
                sys.exit(0)
            
            # Download
            if args.action == "download":
                results = studio.download_all_materials()
                print(f"\n📥 Downloaded: {results['downloaded']}, Failed: {results['failed']}")
                sys.exit(0)
            
            # Studio generate
            if args.action == "studio":
                studio.process_all_sources(materials=materials)
                print(studio.get_summary_report())
                sys.exit(0)
                
        except KeyboardInterrupt:
            print("\n⚠️ Cancelled")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    # =========================================================================
    # STANDARD MODE (original behavior)
    # =========================================================================
    # Run generator
    generator = NotebookLMGenerator(
        input_path=args.input,
        email=email,
        password=password,
        headless=args.headless,
        output_dir=output_dir,
        gemini_api_key=api_key if not args.no_api else None,
        notebook_url=args.notebook_url,
        no_api=args.no_api,
        action=args.action,
        chat_message=args.chat_message
    )

    success = generator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
