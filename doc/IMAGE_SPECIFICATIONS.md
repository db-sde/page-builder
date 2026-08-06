# DegreeBaba Image Specifications & Rendering Guide

This document serves as the **canonical guide for graphic designers, AI image creators, and content teams** when producing image assets for the DegreeBaba static platform. 

It details the exact dimensions, aspect ratios, file formats, safe zones, and HTML/CSS rendering mechanics for every image type across all university workspace pages.

---

## Technical Image Pipeline Overview

Before diving into page-specific guidelines, here is how the DegreeBaba platform processes, optimizes, and serves all images:

1. **Format Normalization**: All uploaded PNG/JPG/JPEG images are automatically downscaled (max side: `1920px`) and converted into high-efficiency **WebP** assets (`82%` quality) via Pillow (`backend/workspace/image_optimizer.py`).
2. **Responsive Variant Generation**: At build time (`backend/renderer/engine.py`), the compiler generates 3 responsive WebP variants for every asset:
   * **Desktop (`1200w`)**: Used for viewports `<= 1200px`
   * **Tablet (`768w`)**: Used for viewports `<= 768px`
   * **Mobile (`480w`)**: Used for viewports `<= 480px`
3. **HTML `<picture>` Delivery**: HTML templates render images inside HTML5 `<picture>` tags with media queries and `fetchpriority="high"` / `loading="lazy"` attributes for instant initial page loads and high LCP performance.

---

## 1. University (Home) Page Hero Image

* **Field Name**: `hero_image_url`
* **Template Path**: [`backend/templates/university.html`](file:///Users/aryankinha/Documents/Degree/temp/acfTOhtml%20copy/backend/templates/university.html#L107)

### Rendering & Container Specs
* **Container CSS**: `width: 100%; height: 430px; object-fit: cover; border-radius: 16px;`
* **Grid Layout**: 2-Column Split (`1.12fr` text / `.88fr` image). Display container is approx. `500px × 430px` on desktop.
* **Display Aspect Ratio**: **`4 : 3`** (approx. `1.16 : 1`)

### Image Creation Guidelines
* **Target Resolution**: **`1920 × 1440 px`** (4:3 ratio, 4K/Retina high resolution)
* **Minimum Resolution**: **`1200 × 900 px`**
* **Format**: WebP / PNG / JPG
* **Overlay & Safe Zone**:
  > [!IMPORTANT]
  > The HTML template places an absolute floating stat badge (`position: absolute; left: 18px; bottom: 18px`).
  > **Keep the bottom-left `200 × 90 px` corner clean and dark/uncluttered** so the floating badge sits gracefully without obscuring logos, faces, or text.

---

## 2. Course Page Hero Image

* **Field Name**: `hero_image_url`
* **Template Path**: [`backend/templates/course.html`](file:///Users/aryankinha/Documents/Degree/temp/acfTOhtml%20copy/backend/templates/course.html#L112)

### Rendering & Container Specs
* **Container CSS**: `width: 100%; height: 410px; object-fit: cover; border-radius: 16px;`
* **Grid Layout**: 2-Column Split (`1fr` text / `540-580px` image column).
* **Display Aspect Ratio**: **`4 : 3`** (approx. `1.35 : 1`)

### Image Creation Guidelines
* **Target Resolution**: **`1920 × 1440 px`** (4:3 ratio)
* **Widescreen Alternative**: **`1920 × 1080 px`** (16:9 ratio)
* **Minimum Resolution**: **`1200 × 900 px`**
* **Format**: WebP / PNG / JPG
* **Overlay & Safe Zone**:
  > [!NOTE]
  > Similar to the university page, a stat badge or NAAC accreditation box sits at `left: 18px; bottom: 18px`. Avoid placing critical text, logos, or visual elements in the bottom-left corner.

---

## 3. Sample Degree Certificate Image

* **Field Name**: `certificate_image_url`
* **Template Path**: [`backend/templates/course.html`](file:///Users/aryankinha/Documents/Degree/temp/acfTOhtml%20copy/backend/templates/course.html#L352)

### Rendering & Container Specs
* **Container CSS**: `max-width: 100%; max-height: 240px; object-fit: contain; display: block;`
* **Grid Layout**: 2-Column Grid inside Placement & Certificate section (`300px` certificate box / `1fr` description box).

### Image Creation Guidelines
* **Target Resolution**: **`1200 × 900 px`** (4:3 ratio) or **`1414 × 1000 px`** (Standard A4 Landscape ratio)
* **Minimum Resolution**: **`800 × 600 px`**
* **Format**: PNG / JPG / WebP
* **Design Note**: Uses `object-fit: contain`, so the certificate image will **never be cropped**. Provide a high-clarity sample degree/diploma scan or realistic mockup with clean borders.

---

## 4. Specialization Page Hero Image

* **Field Name**: `hero_image_url`
* **Template Path**: [`backend/templates/specialization.html`](file:///Users/aryankinha/Documents/Degree/temp/acfTOhtml%20copy/backend/templates/specialization.html#L109)

### Rendering & Container Specs
* **Container CSS**: `width: 100%; aspect-ratio: 4/3; object-fit: cover; border-radius: 16px;`
* **Grid Layout**: 2-Column Split (`1.05fr` text / `.95fr` image).

### Image Creation Guidelines
* **Target Resolution**: **`1920 × 1440 px`** (Explicit `4:3` ratio)
* **Minimum Resolution**: **`1200 × 900 px`**
* **Format**: WebP / PNG / JPG
* **Overlay & Safe Zone**: Floating badge at `left: 18px; bottom: 18px`. Bottom-left corner must remain clean.

---

## 5. Blog Article Hero / Featured Image

* **Field Name**: `featured_image_url` / `hero_image_url`
* **Template Path**: [`backend/templates/blog.html`](file:///Users/aryankinha/Documents/Degree/temp/acfTOhtml%20copy/backend/templates/blog.html#L97)

### Rendering & Container Specs
* **Container CSS**: `width: 100%; aspect-ratio: 3/2; object-fit: cover; border-radius: 16px;`
* **Grid Layout**: Hero header split (`1fr` article title / `.82fr` featured image).

### Image Creation Guidelines
* **Target Resolution**: **`1800 × 1200 px`** (Explicit `3:2` ratio)
* **Minimum Resolution**: **`1200 × 800 px`**
* **Format**: WebP / JPG / PNG
* **Design Note**: Clean 3:2 landscape ratio. No floating card overlays sit on this image.

---

## 6. Branding Assets (Logo & Favicon)

### University Logo
* **Field Name**: `branding.logo`
* **Path**: `workspaces/<slug>/Assets/images/branding-<slug>-logo.webp`
* **Container CSS**: `max-height: 44px; max-width: 240px; object-fit: contain;`
* **Target Resolution**: **`600 × 150 px`** (Aspect ratio `4:1` or `3:1`)
* **Format**: Transparent PNG or WebP

### Favicon
* **Field Name**: `branding.favicon`
* **Path**: `workspaces/<slug>/Assets/images/branding-<slug>-favicon.png`
* **Target Resolution**: **`64 × 64 px`** or **`128 × 128 px`** (Square)
* **Format**: PNG / ICO

---

## Quick Reference Summary Table

| Page Type | Field Name | Target Resolution | Aspect Ratio | CSS `object-fit` | Special Safe Zone Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **University / Home** | `hero_image_url` | `1920 × 1440 px` | **4 : 3** | `cover` | Keep bottom-left `200×90px` clean (floating stat card) |
| **Course** | `hero_image_url` | `1920 × 1440 px` | **4 : 3** | `cover` | Keep bottom-left `200×90px` clean (floating stat card) |
| **Sample Certificate** | `certificate_image_url` | `1200 × 900 px` | **4 : 3** / **A4** | `contain` | No cropping applied; full diploma scan visible |
| **Specialization** | `hero_image_url` | `1920 × 1440 px` | **4 : 3** | `cover` | Keep bottom-left `200×90px` clean (floating stat card) |
| **Blog Featured** | `featured_image_url` | `1800 × 1200 px` | **3 : 2** | `cover` | Clean 3:2 landscape image |
| **Logo** | `branding.logo` | `600 × 150 px` | **4 : 1** | `contain` | Transparent background PNG/WebP |
| **Favicon** | `branding.favicon` | `64 × 64 px` | **1 : 1** | `contain` | Transparent square PNG/ICO |
