import os
import sys
import time
from dotenv import load_dotenv
from pyngrok import ngrok, conf

def setup_ngrok_tunnel(port=8000, max_retries=2):
    """
    Loads .env, configures ngrok, starts a tunnel, and provides detailed logging.
    """
    print("--- ngrok_helper.py starting ---")

    # Explicitly find the project root and .env file
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dotenv_path = os.path.join(project_root, '.env')
        print(f"Searching for .env file at: {dotenv_path}")

        if not os.path.exists(dotenv_path):
            print(f"Error: .env file not found at the expected path.")
            return None

        load_dotenv(dotenv_path=dotenv_path)
        print(".env file loaded.")

        authtoken = os.getenv("NGROK_AUTHTOKEN")
        if not authtoken:
            print("Error: NGROK_AUTHTOKEN not found in the loaded .env file.")
            print("Please ensure it is set correctly.")
            return None

        print("NGROK_AUTHTOKEN found.")

        # Configure ngrok with the authtoken
        conf.get_default().auth_token = authtoken
        print("pyngrok configured with authtoken.")

        # Retry loop for starting the tunnel
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to ngrok (Attempt {attempt + 1}/{max_retries})...")
                public_url = ngrok.connect(port, "http")
                print(f"SUCCESS: ngrok tunnel available at {public_url}")
                return public_url
            except Exception as e:
                print(f"!!! ngrok connection error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    print("Could not establish ngrok tunnel after multiple attempts.")
                    return None
    except Exception as e:
        print(f"!!! A critical error occurred in ngrok_helper: {e}")
        # Print traceback for detailed debugging
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    url = setup_ngrok_tunnel()

    if url:
        print("\nTunnel is active. This script will now block to maintain it.")
        print("Press Ctrl+C in the main terminal to stop all services.")
        try:
            ngrok_process = ngrok.get_ngrok_process()
            ngrok_process.proc.wait()
        except KeyboardInterrupt:
            print("\nngrok_helper received shutdown signal.")
        finally:
            ngrok.disconnect(url)
            ngrok.kill()
            print("ngrok tunnel shut down.")
    else:
        print("\n--- ngrok_helper.py failed to start a tunnel. ---")
        # Exit with a non-zero code to indicate failure
        sys.exit(1)
