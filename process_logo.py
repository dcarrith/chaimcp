from PIL import Image
import sys

def make_transparent(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    datas = img.getdata()
    
    # Simple threshold approach might remove internal white.
    # We should use flood fill from the edges.
    
    # Create a seed point at (0,0) - likely background
    # We will use ImageDraw.floodfill like logic, but PIL doesn't have a direct floodfill for transparency easily without a draw object.
    
    # Alternative: Use BFS (Breadth First Search) to find connected background pixels starting from corners
    
    width, height = img.size
    pixels = img.load()
    
    # Queue for BFS
    queue = [(0, 0), (width-1, 0), (0, height-1), (width-1, height-1)]
    visited = set(queue)
    
    # Background color target (approx white)
    # We'll assume the top-left pixel is the background color
    bg_color = pixels[0, 0] # (R, G, B, A)
    threshold = 30 # Tolerance
    
    def is_match(p_color, t_color):
        return (abs(p_color[0] - t_color[0]) < threshold and
                abs(p_color[1] - t_color[1]) < threshold and
                abs(p_color[2] - t_color[2]) < threshold)

    if not is_match(bg_color, (255, 255, 255, 255)):
        print(f"Warning: Top-left pixel is not white {bg_color}, proceeding anyway assuming it is background.")

    while queue:
        x, y = queue.pop(0)
        
        # Set to transparent
        pixels[x, y] = (0, 0, 0, 0)
        
        # Check neighbors
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in visited:
                    current_pixel = pixels[nx, ny]
                    if is_match(current_pixel, bg_color):
                        visited.add((nx, ny))
                        queue.append((nx, ny))
                        
    img.save(output_path, "PNG")
    print(f"Saved transparent image to {output_path}")

if __name__ == "__main__":
    make_transparent('assets/chai_logo.png', 'assets/chai_logo_transparent.png')
