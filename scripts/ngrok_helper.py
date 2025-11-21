"""
NGROK Helper Script for Project Sanjaya v2.1
Manages NGROK tunnel for remote access
"""
from pyngrok import ngrok
import os
import sys
import time
import json


def start_ngrok_tunnel(port=8000, auth_token=None):
    """
    Start NGROK tunnel
    
    Args:
        port: Local port to expose (default: 8000 for FastAPI)
        auth_token: Optional NGROK auth token
    
    Returns:
        Public URL string
    """
    # Set auth token if provided
    if auth_token:
        ngrok.set_auth_token(auth_token)
    elif os.getenv("NGROK_AUTH_TOKEN"):
        ngrok.set_auth_token(os.getenv("NGROK_AUTH_TOKEN"))
    
    # Start tunnel
    try:
        print(f"🚀 Starting NGROK tunnel on port {port}...")
        
        public_url = ngrok.connect(port, bind_tls=True)
        
        print(f"✅ NGROK tunnel established!")
        print(f"📡 Public URL: {public_url}")
        print(f"🔗 Local URL: http://localhost:{port}")
        
        # Save URL to file
        save_ngrok_url(str(public_url))
        
        return str(public_url)
    
    except Exception as e:
        print(f"❌ Failed to start NGROK tunnel: {e}")
        sys.exit(1)


def save_ngrok_url(url):
    """Save NGROK URL to file for other components to read"""
    config = {
        "ngrok_url": url,
        "timestamp": time.time()
    }
    
    os.makedirs("logs", exist_ok=True)
    
    with open("logs/ngrok_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"💾 NGROK URL saved to logs/ngrok_config.json")


def load_ngrok_url():
    """Load NGROK URL from config file"""
    config_file = "logs/ngrok_config.json"
    
    if not os.path.exists(config_file):
        return None
    
    with open(config_file, "r") as f:
        config = json.load(f)
    
    return config.get("ngrok_url")


def stop_all_tunnels():
    """Stop all NGROK tunnels"""
    try:
        ngrok.kill()
        print("✅ All NGROK tunnels stopped")
    except Exception as e:
        print(f"⚠️ Error stopping tunnels: {e}")


def list_tunnels():
    """List all active NGROK tunnels"""
    try:
        tunnels = ngrok.get_tunnels()
        
        if tunnels:
            print("\n📡 Active NGROK Tunnels:")
            for tunnel in tunnels:
                print(f"  - {tunnel.public_url} -> {tunnel.config['addr']}")
        else:
            print("No active tunnels")
        
        return tunnels
    
    except Exception as e:
        print(f"⚠️ Error listing tunnels: {e}")
        return []


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NGROK Tunnel Helper for Project Sanjaya")
    parser.add_argument("--port", type=int, default=8000, help="Local port to expose")
    parser.add_argument("--token", type=str, help="NGROK auth token")
    parser.add_argument("--stop", action="store_true", help="Stop all tunnels")
    parser.add_argument("--list", action="store_true", help="List active tunnels")
    
    args = parser.parse_args()
    
    if args.stop:
        stop_all_tunnels()
        return
    
    if args.list:
        list_tunnels()
        return
    
    # Start tunnel
    public_url = start_ngrok_tunnel(args.port, args.token)
    
    print("\n" + "="*60)
    print("✨ NGROK Tunnel Active")
    print("="*60)
    print(f"\n📍 Share this URL with parents for tracking:")
    print(f"   {public_url}/track/<username>-<session_hash>")
    print(f"\n💡 Press Ctrl+C to stop the tunnel\n")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping NGROK tunnel...")
        stop_all_tunnels()
        print("✅ Tunnel stopped successfully")


if __name__ == "__main__":
    main()