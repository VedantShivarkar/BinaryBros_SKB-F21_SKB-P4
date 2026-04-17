import random

def classify_image(image_url: str) -> str:
    """
    Mock script for wet/dry image classification.
    In a real-world scenario, this runs a CNN model to classify SAR or RGB imagery
    to detect if the Alternate Wetting and Drying (AWD) cycle is maintained.
    """
    # Simple deterministic/localized mock for the hackathon
    if image_url and "dry" in image_url.lower():
        return "Dry"
    return random.choice(["Wet", "Wet", "Dry"])
