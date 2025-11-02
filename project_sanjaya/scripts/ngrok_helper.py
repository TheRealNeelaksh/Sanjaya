from pyngrok import ngrok
import os
from dotenv import load_dotenv

# Load environment variables from project_sanjaya/.env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# It's recommended to set the NGROK_AUTHTOKEN as an environment variable
# or configure it in the .env file. pyngrok will automatically use it.
# Example .env entry: NGROK_AUTHTOKEN='your_auth_token_here'

def start_ngrok_tunnel(port=8000):
    """
    Starts an ngrok tunnel for the specified port and returns the public URL.
    """
    try:
        # This will use the authtoken from the environment variables if it's set
        public_url = ngrok.connect(port, "http")
        print(f" * ngrok tunnel available at: {public_url}")
        return public_url
    except Exception as e:
        print(f"Error starting ngrok tunnel: {e}")
        print("Please ensure your ngrok authtoken is configured correctly.")
        return None

if __name__ == "__main__":
    print("Starting ngrok tunnel for port 8000...")
    url = start_ngrok_tunnel()
    if url:
        print("\nKeep this script running to maintain the ngrok tunnel.")
        print("Press Ctrl+C to stop.")
        try:
            # Keep the script alive to maintain the tunnel
            ngrok_process = ngrok.get_ngrok_process()
            ngrok_process.proc.wait()
        except KeyboardInterrupt:
            print("Shutting down ngrok tunnel.")
            ngrok.disconnect(url)
            ngrok.kill()
