import argparse
import sys
import os

# Ensure the 'jules' module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jules.tracker import start_tracking

def main():
    """
    Main function to handle command-line arguments for Project Sanjaya.
    """
    parser = argparse.ArgumentParser(
        description="Project Sanjaya - A real-time tracking and visualization tool."
    )
    parser.add_argument(
        "command",
        choices=["start", "stop"],
        help="The command to execute."
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=300,
        help="Tracking interval in seconds. Default is 300 (5 minutes)."
    )

    args = parser.parse_args()

    if args.command == "start":
        print("🚀 Starting Jules Tracker...")
        print(f"📡 Logging location every {args.interval} seconds. Press Ctrl+C to stop.")
        try:
            start_tracking(interval=args.interval)
        except KeyboardInterrupt:
            print("\n🛑 Tracker stopped manually. Goodbye!")
            sys.exit(0)
    elif args.command == "stop":
        # This is a placeholder for future functionality.
        # In this version, the tracker is stopped with Ctrl+C.
        print("🛑 Stop command received. To stop a running tracker, use Ctrl+C in its terminal window.")
        print("Future versions will support graceful remote stopping.")

if __name__ == "__main__":
    main()