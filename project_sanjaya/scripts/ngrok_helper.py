import os
import sys
import time
import traceback
from dotenv import load_dotenv
from pyngrok import ngrok, conf


def setup_ngrok_tunnel(port=8000, max_retries=2):
    """
    Loads .env, configures ngrok, starts a tunnel, and returns the public URL.
    Provides detailed logs for debugging and reliability.
    """
    print("--- ngrok_helper.py starting ---")

    try:
        # Locate project root and .env
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dotenv_path = os.path.join(project_root, ".env")
        print(f"Searching for .env file at: {dotenv_path}")

        if not os.path.exists(dotenv_path):
            print("ERROR: .env file not found at the expected path.")
            return None

        load_dotenv(dotenv_path=dotenv_path)
        print(".env file loaded successfully.")

        authtoken = os.getenv("NGROK_AUTHTOKEN")
        if not authtoken:
            print("ERROR: NGROK_AUTHTOKEN not found in the loaded .env file.")
            print("Please ensure it is set correctly.")
            return None

        print("NGROK_AUTHTOKEN found. Configuring pyngrok...")

        # Configure pyngrok
        conf.get_default().auth_token = authtoken

        # Attempt to start the tunnel
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to ngrok (Attempt {attempt + 1}/{max_retries})...")
                tunnel = ngrok.connect(port, "http")
                public_url = tunnel.public_url  # Extract the actual public URL
                print(f"SUCCESS: ngrok tunnel available at {public_url}")
                return public_url
            except Exception as e:
                print(f"ngrok connection error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    print("ERROR: Could not establish ngrok tunnel after multiple attempts.")
                    return None

    except Exception as e:
        print(f"CRITICAL ERROR in ngrok_helper: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    url = setup_ngrok_tunnel()

    if url:
        print("\nTunnel is active.")
        print(f"Public URL: {url}")
        print("This process will remain active to maintain the tunnel.")
        print("Press Ctrl+C to stop it.\n")
        try:
            ngrok_process = ngrok.get_ngrok_process()
            ngrok_process.proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down ngrok tunnel...")
        finally:
            ngrok.disconnect(url)
            ngrok.kill()
            print("ngrok tunnel shut down cleanly.")
    else:
        print("\nngrok_helper.py failed to start a tunnel.")
        sys.exit(1)
