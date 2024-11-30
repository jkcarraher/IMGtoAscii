from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance
import numpy as np

app = Flask(__name__)
CORS(app)

# Define characters based on grayscale density (without space character)
chars = np.array(list("@%#*+=-:."))
chars = chars[chars != " "]  # Remove space character

def calculate_dynamic_brightness_mapping(img, chars):
    """Dynamically map brightness to characters based on image brightness distribution."""
    histogram, _ = np.histogram(img, bins=256, range=(0, 255))
    cumulative_dist = np.cumsum(histogram) / np.sum(histogram)
    char_indices = (cumulative_dist * (len(chars) - 1)).astype(int)
    return {i: chars[char_indices[i]] for i in range(256)}

# Generate color palette
def generate_color_palette(step=32):
    """Generate a broad set of RGB colors with a fixed step."""
    colors = []
    for r in range(0, 256, step):
        for g in range(0, 256, step):
            for b in range(0, 256, step):
                colors.append((r, g, b))
    return colors

# Define a set of predefined colors for the background
predefined_colors = generate_color_palette(step=32)

# Function to find the closest predefined color
def closest_predefined_color(pixel):
    """Find the closest predefined color for a given pixel."""
    r, g, b = pixel
    closest = min(predefined_colors, key=lambda color: (color[0] - r) ** 2 + (color[1] - g) ** 2 + (color[2] - b) ** 2)
    return closest

# Map brightness values dynamically to characters
def image_to_ascii(image_path):
    """Convert an image to ASCII art."""
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((100, 50))  # Resize for performance
    grayscale_img = img.convert("L")  # Convert to grayscale for brightness mapping
    grayscale_array = np.array(grayscale_img)
    
    # Generate the brightness-to-character map based on the grayscale image
    brightness_to_char = calculate_dynamic_brightness_mapping(grayscale_array, chars)
    
    img = np.array(img)
    ascii_art = "<pre>"

    for row in img:
        for pixel in row:
            r, g, b = pixel
            bg_color = closest_predefined_color((r, g, b))
            brightness = int((r + g + b) / 3)
            char = brightness_to_char[brightness]

            bg_color_str = f"rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})"
            
            # Adjust text color to overlay on the background and better match the original pixel color
            text_color = (min(r + 50, 255), min(g + 50, 255), min(b + 50, 255))
            text_color_str = f"rgb({text_color[0]},{text_color[1]},{text_color[2]})"
            
            ascii_art += f'<span style="background-color:{bg_color_str}; color:{text_color_str};">{char}</span>'
        ascii_art += "<br>"
    ascii_art += "</pre>"
    return ascii_art

@app.route("/convert", methods=["POST"])
def convert_image():
    """Handle image-to-ASCII conversion."""
    if "image" not in request.files:
        return jsonify({"error": "No image file uploaded"}), 400

    file = request.files["image"]
    file_path = f"/tmp/{file.filename}"
    file.save(file_path)

    ascii_art = image_to_ascii(file_path)
    return jsonify({"ascii": ascii_art})

if __name__ == "__main__":
    app.run(debug=True)
