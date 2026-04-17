"""
=============================================================================
Amrit Vaayu dMRV — Vision Classifier (Mock)
=============================================================================
Mock implementation of the Wet/Dry image classifier for paddy field photos.

In production, this module would:
  1. Download the image from the Twilio media URL
  2. Preprocess it (resize, normalize) for the trained model
  3. Run inference on a fine-tuned CNN (e.g., ResNet-18 or MobileNetV3)
  4. Return the classification ("Wet" or "Dry") with confidence

For the hackathon demo, we use a deterministic random classifier seeded
by the image URL hash to ensure consistent results for the same image.

Author: Binary Bros (Vedant Shivarkar & Akshad Kolawar)
=============================================================================
"""

import hashlib
import random
from typing import Optional


def classify_image(image_url: Optional[str] = None) -> dict:
    """
    Mock Wet/Dry classifier for paddy field images.

    Args:
        image_url: The Twilio media URL of the submitted image.
                   Used as a seed for deterministic mock classification.

    Returns:
        dict with keys:
            - "state": "Wet" or "Dry"
            - "confidence": float between 0.70 and 0.99
            - "model": identifier of the classification model used
    """
    # ---------------------------------------------------------------------------
    # Generate a deterministic seed from the image URL so that the same image
    # always produces the same classification result (important for demos).
    # ---------------------------------------------------------------------------
    if image_url:
        url_hash = int(hashlib.md5(image_url.encode()).hexdigest(), 16)
        rng = random.Random(url_hash)
    else:
        rng = random.Random()

    # ---------------------------------------------------------------------------
    # Simulate classification with realistic confidence distribution
    # AWD fields are roughly 60% Wet / 40% Dry in active cycles
    # ---------------------------------------------------------------------------
    state = "Wet" if rng.random() < 0.6 else "Dry"

    # Confidence typically falls between 0.75 and 0.98 for a well-trained model
    confidence = round(rng.uniform(0.75, 0.98), 4)

    return {
        "state": state,
        "confidence": confidence,
        "model": "mock-resnet18-v1.0",
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test with a sample URL
    result = classify_image("https://api.twilio.com/2010-04-01/Accounts/test/Messages/media/sample.jpg")
    print(f"Classification: {result['state']} (Confidence: {result['confidence']:.2%})")
    print(f"Model: {result['model']}")

    # Test determinism — same URL should produce same result
    result2 = classify_image("https://api.twilio.com/2010-04-01/Accounts/test/Messages/media/sample.jpg")
    assert result == result2, "FAIL: Non-deterministic classification!"
    print("✓ Determinism check passed.")

    # Test without URL
    result3 = classify_image(None)
    print(f"Random classification: {result3['state']} ({result3['confidence']:.2%})")
