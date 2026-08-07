# FPV Drone with AI Vision Pipeline
A custom-built FPV quadcopter with an AI vision and notification pipeline built in python. It captures aerial footage, analyzes it in real time using a vision language model, and sends push notifications to my phone when it detects a preconfigured object. The drone also supports GPS waypoint navigation through its BN-880 onboard GPS and BetaFlight software.

## What It Does
The drone flies over an area and streams video to my laptop via its Caddx Ratel2 camera and a 5.8Ghz analog VTX link. A python script captures the live feed from my laptop on a timed basis, sending each frame to Claude's vision API. If the object the program is configured to detect is detected past a certain confidence threshold, a push notification is sent to my phone via ntfy.sh. Because the drone doesn't have any onboard computing power, the drone could be created cheaply and with a small footprint (5" propeller diameter).

## Hardware

| Component | Part |
|---|---|
| Frame | TBS Source One V6 5" |
| Flight Controller | SpeedyBee F405 V5 |
| ESC | SpeedyBee 55A 4-in-1 | 
| Motors | DYS Sun_Fun 2207 1750KV 6S |
| Propellers | HQProp 5x4.3x3 |
| Battery | Ovonic 1300mAh 6S |
| RC System | Flysky FS-i6X + FS-iA6B |
| GPS | BN-880 (GPS & Integrated Compass) |
| Camera | Caddx Ratel 2 (1200TVL, WDR) |
| VTX | SpeedyBee TX800 + 5.8GHz Antenna |
| Video Receiver | EWRF 5.8GHz 56CH UVC OTG |
| Firmware | BetaFlight |

**Main Hardware Decisions:**
- **5" FPV Frame** - Using a small FPV frame was the only way I could get the cost down to a reasonable level to actually go forward with the project. Originally I wanted a larger drone to accommodate a top-down camera orientation, but this was way over budget.
- **No onboard companion computer** - Since the drone frame had significant space restrictions, a raspberry pi onboard was not an option, and all computing had to be moved to my laptop.
- **Analog VTX via EWRF receiver** - The ERWF receiver is recognized natively on Macs and doesn't require any dependencies. This made it an easier option compared to the typical headset setup for FPV drones.

## Software Architecture
The drone is flown manually or on a GPS-waypoint mission through the BetaFlight software. The software covers a one-way observe and alert loop where it captures a frame from the live VTX feed and asks the vision model if the target is in the frame. If the confidence is above threshold and a notification hasn't already been sent (Repeat notifications are handled with a cooldown window) a notification is pushed to the user. The agent folder is subdivided into capture, vision, notify, and outcome.py files, with loop.py handling the loop between checks. The vision evaluator takes a natural-language description of a target (such as "a blue ford bronco" or a "a black mini cooper"

## Running The Software
While the drone is in the air and streaming video to the laptop, the user can run this python command in the terminal to start vision analysis:
'''Bash
python3 main.py --target "type in plain language what the desired target is here"
'''
The user can also pass --threshold and --interval arguments to set override the desired threshold and interval values.

## Future Plans
Since the drone is able to perform a GPS waypoint guided mission autonomously (this is a recent addition to the BetaFlight software). I would like to add additional autonomous capability such as the AI agent being able to call return-to-home or loiter-commands when a target is detected. Adding this functionality would need an upgrade in hardware and the addition of a ESP DroneBridge module so commands can be sent from ground to the drone. I would also like to migrate the drone to a new frame so it is more resilient and durable. 




