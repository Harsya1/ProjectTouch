"""
main.py
=======
Entry point for the Gesture-Triggered Generative Visual Art application.

Main loop:
  1. Capture a frame from the webcam.
  2. Mirror it horizontally (natural webcam feel).
  3. Run hand tracking → detect pinch gestures.
  4. On pinch, spawn a new Region at the pinch midpoint.
  5. Update all regions (advance animation progress, handle fade-out).
  6. Composite all region effects onto the webcam frame.
  7. Draw a debug overlay (FPS, region count, landmark dots).
  8. Display the result in an OpenCV window.

Controls:
  q  — quit
  c  — clear all active regions
"""

from __future__ import annotations

import sys

import cv2
from loguru import logger

import config
from core.hand_tracker import HandTracker
from core.region_manager import RegionManager
from core.compositor import composite
from utils.timing import FrameTimer


def main() -> None:
    logger.info("Starting Gesture Visual Art ...")
    logger.info(
        f"Camera: {config.CAMERA_INDEX}  "
        f"Target resolution: {config.FRAME_WIDTH}x{config.FRAME_HEIGHT}"
    )

    # ── Camera setup ───────────────────────────────────────────────
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        logger.error(f"Cannot open camera at index {config.CAMERA_INDEX}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    # Read back the actual resolution the camera negotiated.
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    config.FRAME_WIDTH = actual_w
    config.FRAME_HEIGHT = actual_h
    logger.info(f"Actual camera resolution: {actual_w}x{actual_h}")

    # ── Sub-systems ────────────────────────────────────────────────
    tracker = HandTracker()
    region_manager = RegionManager()
    timer = FrameTimer()

    logger.info("Running — press 'q' to quit, 'c' to clear all regions")

    # ── Main render loop ───────────────────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to read frame from camera")
            break

        # Mirror for natural webcam interaction.
        frame = cv2.flip(frame, 1)

        # Delta-time for animation.
        dt = timer.tick()

        # ── Hand tracking & pinch detection ────────────────────────
        landmarks_list = tracker.process(frame)
        for landmarks in landmarks_list:
            if tracker.is_pinching(landmarks, actual_w, actual_h):
                midpoint = tracker.get_pinch_midpoint(landmarks)
                region_manager.on_pinch_detected(midpoint)

        # ── Update animation state ─────────────────────────────────
        region_manager.update(dt)

        # ── Composite effects onto the frame ───────────────────────
        output = composite(frame, region_manager.regions)

        # ── Debug overlay ──────────────────────────────────────────
        # FPS + region count.
        cv2.putText(
            output,
            f"FPS: {timer.fps:.1f}  Regions: {len(region_manager.regions)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        # Visualise hand landmarks and pinch proximity.
        for landmarks in landmarks_list:
            thumb = landmarks[4]
            index = landmarks[8]
            # Dot on thumb tip.
            cv2.circle(
                output, (int(thumb[0]), int(thumb[1])), 5, (0, 255, 255), -1
            )
            # Dot on index tip.
            cv2.circle(
                output, (int(index[0]), int(index[1])), 5, (0, 255, 255), -1
            )

            dist = tracker.get_pinch_distance(landmarks, actual_w, actual_h)
            if dist < config.PINCH_THRESHOLD_PX * 2:
                mid = tracker.get_pinch_midpoint(landmarks)
                # Green circle when actively pinching, red when close.
                colour = (
                    (0, 255, 0) if dist < config.PINCH_THRESHOLD_PX
                    else (0, 0, 255)
                )
                cv2.circle(output, mid, 8, colour, 2)

        # ── Display ────────────────────────────────────────────────
        cv2.imshow("Gesture Visual Art", output)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            logger.info("Quit requested")
            break
        elif key == ord("c"):
            region_manager.regions.clear()
            logger.info("All regions cleared")

    # ── Cleanup ────────────────────────────────────────────────────
    cap.release()
    tracker.release()
    cv2.destroyAllWindows()
    logger.info("Application closed")


if __name__ == "__main__":
    main()
