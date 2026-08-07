import argparse
import os
import time

from agent.capture import FrameSource, ScreenGrabFrameSource, StubFrameSource
from agent.loop import WatchLoop
from agent.notifier import CompositeNotifier, ConsoleNotifier, NtfyNotifier, StubNotifier
from agent.notify_config import NtfyConfig
from agent.outcome import Outcome
from agent.vision import ClaudeVisionEvaluator, DetectionResult, StubVisionEvaluator, VisionEvaluator
from agent.watch_config import WatchConfig

# Watch the VTX feed on screen, evaluate each
# frame against the configured target, and push an alert to the operator's
# phone (via ntfy.sh) when it's seen.


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch the VTX feed for a target and alert the operator.")
    parser.add_argument("--target", help="Natural-language description of what to watch for, e.g. 'a blue Ford Bronco'. Overrides WATCH_TARGET.")
    parser.add_argument("--threshold", type=float, help="Confidence threshold (0.0-1.0) required to alert. Overrides WATCH_CONFIDENCE_THRESHOLD.")
    parser.add_argument("--interval", type=float, help="Seconds between frame captures. Overrides WATCH_CAPTURE_INTERVAL_S.")
    return parser.parse_args()


def build_notifier() -> CompositeNotifier:
    notifiers = [ConsoleNotifier()]
    if os.environ.get("AGENT_NOTIFY_STUB") == "1":
        notifiers.append(StubNotifier())
    else:
        ntfy_config = NtfyConfig.from_env()
        notifiers.append(NtfyNotifier(ntfy_config.topic_url, access_token=ntfy_config.access_token))
    return CompositeNotifier(notifiers)


def build_vision(watch_config: WatchConfig) -> VisionEvaluator:
    if os.environ.get("AGENT_VISION_STUB") == "1":
        # Deterministic "always detected" stub, for smoke-testing the loop
        # without burning real vision API calls.
        return StubVisionEvaluator(DetectionResult(detected=True, confidence=0.95, label="stub target"))
    return ClaudeVisionEvaluator(
        target_description=watch_config.target_description,
        model=watch_config.vision_model,
    )


def build_frame_source() -> FrameSource:
    if os.environ.get("AGENT_CAPTURE_STUB") == "1":
        return StubFrameSource(fixed_bytes=b"stub-frame")
    return ScreenGrabFrameSource()


def main() -> None:
    args = parse_args()
    watch_config = WatchConfig.from_env(
        target_override=args.target,
        threshold_override=args.threshold,
        interval_override=args.interval,
    )

    notifier = build_notifier()
    vision = build_vision(watch_config)
    frame_source = build_frame_source()
    loop = WatchLoop(vision=vision, notifier=notifier, config=watch_config)

    print(f"[main] Watching for {watch_config.target_description!r} "
          f"(threshold={watch_config.confidence_threshold}, cooldown={watch_config.cooldown_s}s, "
          f"interval={watch_config.capture_interval_s}s)")

    try:
        while True:
            try:
                frame = frame_source.capture()
                outcome = loop.process_frame(frame)
                if outcome == Outcome.NOT_DETECTED:
                    print("[main] no detection this frame")
            except Exception as exc:
                # A bad frame or a vision/SMS hiccup should never kill the loop.
                print(f"[main] frame processing failed: {exc}")
            time.sleep(watch_config.capture_interval_s)
    except KeyboardInterrupt:
        print("\n[main] stopped by operator")


if __name__ == "__main__":
    main()
