"""Industrial Factory Line -> Ignition SCADA Main Application.

Provides two modes:
  1. Publisher (Default): Simulates factory machines streaming live telemetry into Ignition.
  2. Subscriber: Receives and displays live telemetry streamed from Ignition.

Run Publisher:
    python main.py
    (or: python main.py --publisher)

Run Subscriber:
    python main.py --subscriber
    (or: python subscriber.py)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_publisher():
    # Import the standalone publisher logic
    import simulator.sparkplug_factory as sim
    sim.main()


def run_subscriber():
    # Import subscriber logic
    import subscriber
    subscriber.main()


if __name__ == "__main__":
    if "--subscriber" in sys.argv:
        sys.argv.remove("--subscriber")
        run_subscriber()
    elif "-s" in sys.argv:
        sys.argv.remove("-s")
        run_subscriber()
    else:
        if "--publisher" in sys.argv:
            sys.argv.remove("--publisher")
        run_publisher()
