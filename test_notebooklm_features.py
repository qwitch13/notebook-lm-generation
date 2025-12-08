#!/usr/bin/env python3
"""
Test NotebookLM browser automation for both Chat and Audio generation.

Usage:
    cd ~/IdeaProjects/notebook-lm-generation
    source venv/bin/activate
    python3 test_notebooklm_features.py --test chat
"""

import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Your existing notebook URL
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"


def get_notebooklm_client():
    """Create and return a properly initialized NotebookLMClient."""
    from src.auth.google_auth import GoogleAuthenticator
    from src.generators.notebooklm import NotebookLMClient
    
    print("🔑 Initializing GoogleAuthenticator...")
    auth = GoogleAuthenticator()
    
    print("🌐 Getting browser driver...")
    driver = auth.get_driver()
    
    if not driver:
        print("❌ Failed to get browser driver")
        return None
    
    print("✅ Driver obtained")
    
    print("📓 Creating NotebookLMClient...")
    client = NotebookLMClient(authenticator=auth)
    
    return client


def test_chat():
    """Test the chat functionality."""
    print("\n" + "="*60)
    print("🧪 TEST: NotebookLM Chat")
    print("="*60)
    
    client = get_notebooklm_client()
    if not client:
        return False
    
    try:
        # Navigate to notebook
        print("\n1️⃣ Navigating to notebook...")
        if not client.navigate_to_notebook(NOTEBOOK_URL):
            print("❌ Failed to navigate to notebook")
            return False
        
        print("✅ Navigated to notebook")
        time.sleep(3)
        
        # Send test message
        print("\n2️⃣ Sending test chat message...")
        response = client.send_chat_message("Fasse die wichtigsten Themen in 2-3 Sätzen zusammen.")
        
        if response:
            print(f"\n✅ Got response ({len(response)} chars):")
            print("-" * 40)
            print(response[:500])
            if len(response) > 500:
                print(f"... ({len(response) - 500} more chars)")
            print("-" * 40)
            return True
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\n💡 Browser left open for inspection")


def test_audio():
    """Test the audio generation functionality."""
    print("\n" + "="*60)
    print("🧪 TEST: NotebookLM Audio Generation")
    print("="*60)
    
    client = get_notebooklm_client()
    if not client:
        return False
    
    try:
        # Navigate to notebook
        print("\n1️⃣ Navigating to notebook...")
        if not client.navigate_to_notebook(NOTEBOOK_URL):
            print("❌ Failed to navigate to notebook")
            return False
        
        print("✅ Navigated to notebook")
        time.sleep(3)
        
        # Try to generate audio
        print("\n2️⃣ Attempting to generate audio overview...")
        result = client.generate_audio_overview()
        
        if result:
            print("✅ Audio generation initiated!")
            print("   Note: Full generation takes 2-5 minutes")
            return True
        else:
            print("❌ Audio generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\n💡 Browser left open for inspection")


def test_topic_splitter():
    """Test the topic splitter."""
    print("\n" + "="*60)
    print("🧪 TEST: Topic Splitter")
    print("="*60)
    
    try:
        from src.processors.topic_splitter import TopicSplitter
        from src.processors.content_processor import ProcessedContent
        
        splitter = TopicSplitter()
        
        # Sample content - using correct ProcessedContent fields
        sample = ProcessedContent(
            source="test_input.txt",
            source_type="txt",
            title="Machine Learning Basics",
            raw_text="""
            Chapter 1: Introduction to Machine Learning
            
            Machine learning is a subset of artificial intelligence that enables computers to learn
            from data without being explicitly programmed. There are three main types:
            
            1. Supervised Learning: The algorithm learns from labeled training data.
            2. Unsupervised Learning: The algorithm finds patterns in unlabeled data.
            3. Reinforcement Learning: The algorithm learns through trial and error.
            
            Chapter 2: Neural Networks
            
            Neural networks are computing systems inspired by biological neural networks.
            They consist of layers of interconnected nodes that process information.
            Deep learning uses neural networks with many layers to learn complex patterns.
            """,
            cleaned_text="""
            Chapter 1: Introduction to Machine Learning
            
            Machine learning is a subset of artificial intelligence that enables computers to learn
            from data without being explicitly programmed. There are three main types:
            
            1. Supervised Learning: The algorithm learns from labeled training data.
            2. Unsupervised Learning: The algorithm finds patterns in unlabeled data.
            3. Reinforcement Learning: The algorithm learns through trial and error.
            
            Chapter 2: Neural Networks
            
            Neural networks are computing systems inspired by biological neural networks.
            They consist of layers of interconnected nodes that process information.
            Deep learning uses neural networks with many layers to learn complex patterns.
            """,
            word_count=100,
            metadata={}
        )
        
        print("Splitting sample content...")
        result = splitter.split(sample, max_topics=3)
        
        if result and result.topics:
            print(f"✅ Split into {len(result.topics)} topics:")
            for t in result.topics:
                print(f"   - {t.title}: {t.summary[:50]}...")
            return True
        else:
            print("❌ No topics extracted (may need GEMINI_API_KEY)")
            print("   Set: export GEMINI_API_KEY='your-key'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test NotebookLM features")
    parser.add_argument("--test", choices=["chat", "audio", "splitter", "all"], 
                        default="chat", help="Which test to run")
    args = parser.parse_args()
    
    print("="*60)
    print("NotebookLM Feature Tests")
    print("="*60)
    
    if args.test == "chat" or args.test == "all":
        test_chat()
    
    if args.test == "audio" or args.test == "all":
        test_audio()
    
    if args.test == "splitter" or args.test == "all":
        test_topic_splitter()
    
    print("\n" + "="*60)
    print("Tests complete!")
    print("="*60)


if __name__ == "__main__":
    main()
