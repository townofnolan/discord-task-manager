"""Script to generate placeholder mascot images for UI examples."""

import os
import sys

from PIL import Image, ImageDraw, ImageFont


def create_mascot_image(filename, text, color):
    """Create a simple mascot image with text."""
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a colored circle
    draw.ellipse((20, 20, 180, 180), fill=color)

    # Add text
    try:
        font = ImageFont.truetype("Arial", 30)
    except IOError:
        font = ImageFont.load_default()

    # Use font.getbbox() for newer Pillow versions
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((200 - text_width) // 2, (200 - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)

    # Save image
    img.save(filename)
    print(f"Created {filename}")


def main():
    # Get the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, "assets", "ui")

    # Create the directory if it doesn't exist
    os.makedirs(assets_dir, exist_ok=True)

    # Create mascot images
    create_mascot_image(
        os.path.join(assets_dir, "penguin.png"), "Penguin", (0, 123, 255, 255)  # Blue
    )
    create_mascot_image(
        os.path.join(assets_dir, "cat.png"), "Cat", (255, 105, 180, 255)  # Pink
    )

    print("Mascot images created successfully!")


if __name__ == "__main__":
    main()
