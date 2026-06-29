import shutil
from pathlib import Path
from PIL import Image

def optimize_images_pipeline(src_dir: Path, dst_dir: Path) -> dict:
    """
    Processes all PNG/JPG images in src_dir:
    1. Copies the original file to dst_dir.
    2. Generates responsive WebP variants: -480.webp, -768.webp, -1200.webp.
    3. Returns compression statistics.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    
    image_suffixes = {'.png', '.jpg', '.jpeg'}
    target_widths = [480, 768, 1200]

    for p in src_dir.glob('*'):
        if not p.is_file() or p.suffix.lower() not in image_suffixes:
            continue
            
        # Copy original as fallback
        shutil.copy2(p, dst_dir / p.name)
        
        try:
            with Image.open(p) as img:
                orig_width, orig_height = img.size
                orig_size = p.stat().st_size
                
                variants_info = []
                # Save base WebP at original dimensions
                base_webp_name = p.stem + '.webp'
                base_webp_path = dst_dir / base_webp_name
                img.save(base_webp_path, format='WEBP', quality=82)
                base_size = base_webp_path.stat().st_size
                
                # Responsive variants
                for w in target_widths:
                    if w >= orig_width:
                        # Skip generating variant if it is larger than or equal to original width
                        w_path = dst_dir / f"{p.stem}-{w}.webp"
                        img.save(w_path, format='WEBP', quality=82)
                        variants_info.append({
                            "width": orig_width,
                            "height": orig_height,
                            "size": base_size,
                            "filename": w_path.name
                        })
                        continue
                        
                    # Calculate new height to maintain aspect ratio
                    h = int((w / orig_width) * orig_height)
                    resized_img = img.resize((w, h), Image.Resampling.LANCZOS)
                    
                    variant_name = f"{p.stem}-{w}.webp"
                    variant_path = dst_dir / variant_name
                    resized_img.save(variant_path, format='WEBP', quality=82)
                    
                    variants_info.append({
                        "width": w,
                        "height": h,
                        "size": variant_path.stat().st_size,
                        "filename": variant_name
                    })
                
                stats[p.name] = {
                    "format": img.format,
                    "width": orig_width,
                    "height": orig_height,
                    "original_size": orig_size,
                    "base_webp_size": base_size,
                    "variants": variants_info
                }
        except Exception as e:
            print(f"Error optimizing {p.name}: {e}")
            
    return stats
