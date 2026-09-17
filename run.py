"""Launcher script for OpenJournalMetaAnalyzer."""
import sys
import os
import argparse
import threading
import time
import webbrowser
import uvicorn

def open_browser(url: str, delay: float = 1.2):
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="OpenJournalMetaAnalyzer Launcher")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--test-mode", action="store_true", help="Test mode: import and verify app without blocking")
    
    args = parser.parse_args()

    # Ensure project root is in sys.path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    if args.test_mode:
        print("[Test Mode] Importing FastAPI app and verifying components...")
        from app.main import app
        print(f"[Test Mode] Successfully loaded {app.title} v{app.version}.")
        sys.exit(0)

    url = f"http://{args.host}:{args.port}"
    print("=" * 65)
    print("  🚀 OpenJournalMetaAnalyzer - PRISMA 2020 Meta-Analysis Platform")
    print(f"  🌐 Running at: {url}")
    print("  📚 Powered by OpenAlex API & Europe PMC API (Open Access)")
    print("=" * 65)

    if not args.no_browser:
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
