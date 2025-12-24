from PIL import Image
import numpy as np

def remove_white_background(input_path, output_path):
    print(f"Processing {input_path}...")
    try:
        img = Image.open(input_path).convert("RGBA")
        data = np.array(img)
        
        # Define white threshold (adjust if needed)
        threshold = 240
        
        # Create mask for white pixels
        r, g, b, a = data.T
        white_areas = (r > threshold) & (g > threshold) & (b > threshold)
        
        # Set alpha to 0 for white pixels
        data[..., 3][white_areas.T] = 0
        
        # Save result
        new_img = Image.fromarray(data)
        new_img.save(output_path)
        print(f"Saved transparent logo to {output_path}")
        
    except Exception as e:
        print(f"Error processing image: {e}")

# Process the logo
input_file = "/home/ubuntu/nucleus_teaser_website/client/public/images/nucleus_logo_final_clean.png"
output_file = "/home/ubuntu/nucleus_teaser_website/client/public/images/nucleus_logo_transparent.png"

remove_white_background(input_file, output_file)
