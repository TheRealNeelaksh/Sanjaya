from pyngrok import ngrok, conf
import os
from dotenv import load_dotenv
import time

def setup_ngrok_tunnel(port=8000, max_retries=3):
    """
    Loads .env, configures ngrok with the authtoken, and starts a tunnel.
    Retries on connection failure.
    """
    # Load .env file from the project root (one level up from 'scripts')
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    authtoken = os.getenv("NGROK_AUTHTOKEN")
    if not authtoken:
        print("Error: NGROK_AUTHTOKEN not found in .env file.")
        print("Please get a token from https://dashboard.ngrok.com and add it to your .env file.")
        return None

    # Explicitly configure ngrok with the authtoken
    conf.get_default().auth_token = authtoken

    # Retry loop in case ngrok fails to start on the first try
    for attempt in range(max_retries):
        try:
            public_url = ngrok.connect(port, "http")
            print(f" * ngrok tunnel available at {public_url}")
            return public_url
        except Exception as e:
            print(f"Error starting ngrok on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5) # Wait before retrying
            else:
                print("Could not establish ngrok tunnel after multiple attempts.")
                return None

if __name__ == "__main__":
    print("Attempting to start ngrok tunnel for port 8000...")
    public_url = setup_ngrok_tunnel()

    if public_url:
        print("\nTunnel is active. Keep this script running to maintain it.")
        print("Press Ctrl+C to stop.")
        try:
            # Keep the script alive to maintain the tunnel
            ngrok_process = ngrok.get_ngrok_process()
            ngrok_process.proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down ngrok tunnel...")
        finally:
            # Disconnect all tunnels and kill the process
            ngrok.disconnect(public_url)
            ngrok.kill()
            print("ngrok tunnel shut down.")
