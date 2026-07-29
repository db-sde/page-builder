import shutil
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError


WEBP_QUALITY = 82
MAX_UPLOAD_SIDE = 1920
_WEBP_SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def optimize_uploaded_image(
    image_bytes: bytes,
    destination_dir: Path,
    filename_prefix: str,
    source_suffix: str,
) -> dict:
    """Store a newly uploaded raster image as a normalized WebP source asset.

    Existing workspace assets are intentionally left alone.  Unsupported image
    formats retain their original bytes so uploads remain backwards compatible.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    source_suffix = source_suffix.lower()
    original_size = len(image_bytes)

    if source_suffix not in _WEBP_SOURCE_SUFFIXES:
        destination = destination_dir / f"{filename_prefix}{source_suffix or '.img'}"
        destination.write_bytes(image_bytes)
        return {
            "path": destination,
            "optimized": False,
            "original_bytes": original_size,
            "optimized_bytes": original_size,
            "original_dimensions": None,
            "optimized_dimensions": None,
        }

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            original_dimensions = source.size
            image = ImageOps.exif_transpose(source)
            if max(image.size) > MAX_UPLOAD_SIDE:
                scale = MAX_UPLOAD_SIDE / max(image.size)
                image = image.resize(
                    (round(image.width * scale), round(image.height * scale)),
                    Image.Resampling.LANCZOS,
                )

            # Saving a fresh RGB/RGBA image strips EXIF and embedded profiles
            # without changing whether transparent source artwork stays transparent.
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            destination = destination_dir / f"{filename_prefix}.webp"
            image.save(destination, format="WEBP", quality=WEBP_QUALITY, method=6)
    except (UnidentifiedImageError, OSError, ValueError):
        destination = destination_dir / f"{filename_prefix}{source_suffix or '.img'}"
        destination.write_bytes(image_bytes)
        return {
            "path": destination,
            "optimized": False,
            "original_bytes": original_size,
            "optimized_bytes": original_size,
            "original_dimensions": None,
            "optimized_dimensions": None,
        }

    return {
        "path": destination,
        "optimized": True,
        "original_bytes": original_size,
        "optimized_bytes": destination.stat().st_size,
        "original_dimensions": original_dimensions,
        "optimized_dimensions": image.size,
    }

def optimize_images_pipeline(src_dir: Path, dst_dir: Path) -> dict:
    """
    Processes all PNG/JPG/WebP images in src_dir:
    1. Copies the original file to dst_dir.
    2. Generates responsive WebP variants: -480.webp, -768.webp, -1200.webp.
    3. Returns compression statistics.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    
    image_suffixes = {'.png', '.jpg', '.jpeg', '.webp'}
    target_widths = [480, 768, 1200]

    for p in src_dir.glob('*'):
        if not p.is_file() or p.suffix.lower() not in image_suffixes:
            continue
            
        try:
            # Copy original as fallback
            shutil.copy2(p, dst_dir / p.name)
            
            with Image.open(p) as img:
                orig_width, orig_height = img.size
                orig_size = p.stat().st_size
                
                variants_info = []
                # Save base WebP at original dimensions
                base_webp_name = p.stem + '.webp'
                base_webp_path = dst_dir / base_webp_name
                img.save(base_webp_path, format='WEBP', quality=WEBP_QUALITY)
                base_size = base_webp_path.stat().st_size
                
                # Responsive variants
                for w in target_widths:
                    if w >= orig_width:
                        # Skip generating variant if it is larger than or equal to original width
                        w_path = dst_dir / f"{p.stem}-{w}.webp"
                        img.save(w_path, format='WEBP', quality=WEBP_QUALITY)
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
                    resized_img.save(variant_path, format='WEBP', quality=WEBP_QUALITY)
                    
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
