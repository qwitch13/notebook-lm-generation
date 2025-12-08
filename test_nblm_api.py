#!/usr/bin/env python3
"""
Test script for NotebookLM API via nblm SDK

PREREQUISITES:
1. Install Google Cloud SDK:
   curl https://sdk.cloud.google.com | bash
   
2. Restart terminal and run:
   gcloud auth login
   gcloud auth application-default login
   
3. Get your project number from GCP Console:
   https://console.cloud.google.com/
   
4. Enable Discovery Engine API:
   gcloud services enable discoveryengine.googleapis.com
   
5. Set environment variables:
   export NBLM_PROJECT_NUMBER="your-project-number"
"""

import os
import sys

def test_nblm():
    try:
        from nblm import NblmClient, GcloudTokenProvider, WebSource
        print("✅ nblm package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import nblm: {e}")
        print("   Run: pip install nblm")
        return False
    
    # Check for project number
    project_number = os.environ.get("NBLM_PROJECT_NUMBER")
    if not project_number:
        print("❌ NBLM_PROJECT_NUMBER environment variable not set")
        print("   Get it from: https://console.cloud.google.com/")
        print("   Then run: export NBLM_PROJECT_NUMBER='your-number'")
        return False
    
    print(f"✅ Project number: {project_number}")
    
    # Try to authenticate
    try:
        token_provider = GcloudTokenProvider()
        print("✅ GcloudTokenProvider initialized")
    except Exception as e:
        print(f"❌ Failed to initialize GcloudTokenProvider: {e}")
        print("   Run: gcloud auth login && gcloud auth application-default login")
        return False
    
    # Try to create client
    try:
        client = NblmClient(
            token_provider=token_provider,
            project_number=project_number
        )
        print("✅ NblmClient created successfully")
    except Exception as e:
        print(f"❌ Failed to create NblmClient: {e}")
        return False
    
    # Try to list notebooks
    try:
        print("\n📒 Listing recent notebooks...")
        notebooks = client.list_recently_viewed()
        print(f"   Found {len(notebooks)} notebooks")
        for nb in notebooks[:5]:  # Show first 5
            print(f"   - {nb.title} (ID: {nb.notebook_id})")
    except Exception as e:
        print(f"❌ Failed to list notebooks: {e}")
        print("   This might mean:")
        print("   - Discovery Engine API not enabled")
        print("   - No NotebookLM Enterprise license")
        print("   - Authentication issues")
        return False
    
    print("\n✅ All tests passed! nblm SDK is working.")
    return True


def test_podcast_api_standalone():
    """
    Test the standalone Podcast API (doesn't require NotebookLM Enterprise)
    """
    import subprocess
    import json
    
    print("\n" + "="*60)
    print("Testing Standalone Podcast API")
    print("="*60)
    
    project_id = os.environ.get("NBLM_PROJECT_NUMBER") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("❌ Set NBLM_PROJECT_NUMBER or GOOGLE_CLOUD_PROJECT")
        return False
    
    # Get access token via gcloud
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, check=True
        )
        token = result.stdout.strip()
        print("✅ Got access token from gcloud")
    except FileNotFoundError:
        print("❌ gcloud CLI not found")
        print("   Install: curl https://sdk.cloud.google.com | bash")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get token: {e.stderr}")
        return False
    
    # Try podcast API
    import urllib.request
    import urllib.error
    
    url = f"https://discoveryengine.googleapis.com/v1/projects/{project_id}/locations/global/podcasts"
    
    data = {
        "podcastConfig": {
            "focus": "Summarize the key points",
            "length": "SHORT",
            "languageCode": "en"
        },
        "contexts": [
            {"text": "This is a test document about artificial intelligence and machine learning."}
        ],
        "title": "Test Podcast",
        "description": "Testing the API"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("✅ Podcast API request successful!")
            print(f"   Response: {json.dumps(result, indent=2)[:500]}...")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Podcast API error ({e.code}): {error_body}")
        if e.code == 403:
            print("   → Enable Discovery Engine API and get Podcast API User role")
        return False


if __name__ == "__main__":
    print("="*60)
    print("NotebookLM API Test Script")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--podcast":
        test_podcast_api_standalone()
    else:
        test_nblm()
        test_podcast_api_standalone()
