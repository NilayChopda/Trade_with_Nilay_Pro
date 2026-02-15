from PIL import Image, ImageDraw, ImageFont
import os

# Define paths relative to Nilay's Scanner
output_dir = "../frontend/static"
os.makedirs(output_dir, exist_ok=True)

def create_icon(size, filename):
    # Create a new image with a dark background
    img = Image.new('RGB', (size, size), color='#0F172A')
    d = ImageDraw.Draw(img)
    
    # Draw a circle/background shape
    margin = size // 10
    d.ellipse([margin, margin, size-margin, size-margin], fill='#1E293B', outline='#F59E0B', width=size//20)
    
    # Draw text "TN" (Trade with Nilay)
    try:
        # Try to use a default font, size depends on image size
        font_size = int(size / 2.5)
        # Using a simple sans-serif if available, else default
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text = "TN"
    
    # Calculate text position to center it
    # unexpected logic here as getsize is deprecated in recent Pillow, using getbbox
    try:
        left, top, right, bottom = d.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
    except AttributeError:
        # Fallback for older Pillow
        text_width, text_height = d.textsize(text, font=font)
        
    # Center text
    x = (size - text_width) / 2
    y = (size - text_height) / 2
    
    d.text((x, y), text, fill='#F59E0B', font=font)
    
    # Save the image
    save_path = os.path.join(output_dir, filename)
    img.save(save_path)
    print(f"Created {save_path}")


# Generate icons
create_icon(192, "icon-192.png")
create_icon(512, "icon-512.png")
