import hashlib
import json
import os
import shutil
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError


WEBP_QUALITY = 82
MAX_UPLOAD_SIDE = 1920
_WEBP_SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_HASH_INDEX_FILENAME = ".image-hashes.json"


def _load_hash_index(directory: Path) -> dict[str, list[str]]:
    path = directory / _HASH_INDEX_FILENAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}

    if not isinstance(raw, dict):
        return {}
    return {
        digest: value if isinstance(value, list) else [value]
        for digest, value in raw.items()
        if isinstance(digest, str) and isinstance(value, (str, list))
    }


def _save_hash_index(directory: Path, index: dict[str, list[str]]) -> None:
    path = directory / _HASH_INDEX_FILENAME
    path.write_text(json.dumps(index, sort_keys=True), encoding="utf-8")


def _remove_indexed_name(index: dict[str, list[str]], filename: str) -> None:
    for digest, filenames in list(index.items()):
        remaining = [name for name in filenames if name != filename]
        if remaining:
            index[digest] = remaining
        else:
            del index[digest]


def _existing_content_path(directory: Path, content_hash: str, index: dict[str, list[str]]) -> Path | None:
    for filename in index.get(content_hash, []):
        candidate = directory / filename
        if candidate.is_file():
            return candidate

    # Legacy workspaces have no index. Scan only when an upload is not already
    # known, then record the match so following uploads are constant-time.
    for candidate in directory.iterdir():
        if not candidate.is_file() or candidate.name == _HASH_INDEX_FILENAME:
            continue
        if hashlib.sha256(candidate.read_bytes()).hexdigest() == content_hash:
            index.setdefault(content_hash, []).append(candidate.name)
            return candidate
    return None


def _replace_with_link(source: Path, destination: Path) -> bool:
    """Create a same-filesystem hard link, falling back to a normal copy."""
    if source.resolve() == destination.resolve():
        return True
    if destination.exists():
        destination.unlink()
    try:
        os.link(source, destination)
        return True
    except OSError:
        shutil.copy2(source, destination)
        return False


def _destination_for_upload(destination_dir: Path, filename_prefix: str, source_suffix: str) -> Path:
    suffix = ".webp" if source_suffix in _WEBP_SOURCE_SUFFIXES else source_suffix or ".img"
    return destination_dir / f"{filename_prefix}{suffix}"


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
    destination = _destination_for_upload(destination_dir, filename_prefix, source_suffix)
    content_hash = hashlib.sha256(image_bytes).hexdigest()
    index = _load_hash_index(destination_dir)

    existing = _existing_content_path(destination_dir, content_hash, index)
    if existing:
        # A legacy PNG/JPEG cannot be hard-linked into a new .webp filename:
        # its bytes would no longer match the extension. Reuse that compatible
        # legacy asset directly instead of creating a duplicate.
        if existing.suffix.lower() != destination.suffix.lower():
            try:
                with Image.open(existing) as image:
                    dimensions = image.size
            except (UnidentifiedImageError, OSError, ValueError):
                dimensions = None
            _save_hash_index(destination_dir, index)
            return {
                "path": existing,
                "optimized": False,
                "deduplicated": True,
                "original_bytes": original_size,
                "optimized_bytes": existing.stat().st_size,
                "original_dimensions": dimensions,
                "optimized_dimensions": dimensions,
            }
        _remove_indexed_name(index, destination.name)
        _replace_with_link(existing, destination)
        index.setdefault(content_hash, []).append(destination.name)
        _save_hash_index(destination_dir, index)
        try:
            with Image.open(existing) as image:
                dimensions = image.size
        except (UnidentifiedImageError, OSError, ValueError):
            dimensions = None
        return {
            "path": destination,
            "optimized": destination.suffix == ".webp",
            "deduplicated": True,
            "original_bytes": original_size,
            "optimized_bytes": destination.stat().st_size,
            "original_dimensions": dimensions,
            "optimized_dimensions": dimensions,
        }

    _remove_indexed_name(index, destination.name)
    if destination.exists():
        destination.unlink()

    if source_suffix not in _WEBP_SOURCE_SUFFIXES:
        destination.write_bytes(image_bytes)
        index.setdefault(content_hash, []).append(destination.name)
        _save_hash_index(destination_dir, index)
        return {
            "path": destination,
            "optimized": False,
            "deduplicated": False,
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
            image.save(destination, format="WEBP", quality=WEBP_QUALITY, method=6)
    except (UnidentifiedImageError, OSError, ValueError):
        destination.write_bytes(image_bytes)
        index.setdefault(content_hash, []).append(destination.name)
        _save_hash_index(destination_dir, index)
        return {
            "path": destination,
            "optimized": False,
            "deduplicated": False,
            "original_bytes": original_size,
            "optimized_bytes": original_size,
            "original_dimensions": None,
            "optimized_dimensions": None,
        }

    index.setdefault(content_hash, []).append(destination.name)
    _save_hash_index(destination_dir, index)
    return {
        "path": destination,
        "optimized": True,
        "deduplicated": False,
        "original_bytes": original_size,
        "optimized_bytes": destination.stat().st_size,
        "original_dimensions": original_dimensions,
        "optimized_dimensions": image.size,
    }

def optimize_images_pipeline(src_dir: Path, dst_dir: Path) -> dict:
    """
    Processes all PNG/JPG/WebP images in src_dir:
    1. Copies the original file to dst_dir.
    2. Generates only responsive WebP variants smaller than the source.
    3. Reuses generated assets for byte-identical legacy source files.
    4. Returns compression statistics.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    
    image_suffixes = {'.png', '.jpg', '.jpeg', '.webp'}
    target_widths = [480, 768, 1200]

    canonical_by_hash: dict[str, tuple[Path, dict]] = {}

    for p in src_dir.glob('*'):
        if not p.is_file() or p.suffix.lower() not in image_suffixes:
            continue
            
        try:
            content_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            if content_hash in canonical_by_hash:
                canonical_source, canonical_stats = canonical_by_hash[content_hash]
                for filename in [
                    p.name,
                    f"{p.stem}.webp",
                    *[f"{p.stem}-{variant['width']}.webp" for variant in canonical_stats["variants"]],
                ]:
                    source_name = filename.replace(p.stem, canonical_source.stem, 1)
                    _replace_with_link(dst_dir / source_name, dst_dir / filename)
                stats[p.name] = {
                    **canonical_stats,
                    "deduplicated_from": canonical_source.name,
                    "variants": [
                        {**variant, "filename": variant["filename"].replace(canonical_source.stem, p.stem, 1)}
                        for variant in canonical_stats["variants"]
                    ],
                }
                continue

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
                        # The base WebP already serves this viewport without
                        # enlarging the source or creating a duplicate file.
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
                canonical_by_hash[content_hash] = (p, stats[p.name])
        except Exception as e:
            print(f"Error optimizing {p.name}: {e}")
            
    return stats
