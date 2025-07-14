# Adding Draw.io Diagrams to Your Presentation

## For Slidev Presentation

1. **Export your draw.io diagrams:**
   - Open your diagram in draw.io
   - File → Export as → PNG or SVG
   - Choose high resolution (300 DPI for PNG)
   - Save with descriptive names like:
     - `architecture-diagram.png`
     - `data-flow.svg`
     - `webhook-sequence.png`

2. **Add to presentation:**
   - Place the exported files in the `presentation/public/` directory
   - Reference in your slides:

```markdown
---
layout: image-right
image: /architecture-diagram.png
---

# Architecture Overview

Your content here...
```

Or for full-page images:

```markdown
---
layout: image
image: /data-flow.svg
backgroundSize: contain
---
```

3. **Multiple diagrams on one slide:**

```markdown
# System Components

<div class="grid grid-cols-2 gap-4">
  <img src="/component-1.png" class="rounded shadow-lg" />
  <img src="/component-2.png" class="rounded shadow-lg" />
</div>
```

## For Reveal.js Presentation

1. **Add to HTML:**

```html
<section data-background="/architecture-diagram.png" data-background-size="contain">
    <h2>Architecture Overview</h2>
</section>
```

2. **Inline images:**

```html
<section>
    <h2>Data Flow</h2>
    <img src="data-flow.svg" style="width: 80%; border: none; box-shadow: none;" />
</section>
```

## Best Practices

1. **File formats:**
   - Use SVG for diagrams with text (scalable)
   - Use PNG for complex diagrams with many colors
   - Keep file sizes under 1MB for smooth performance

2. **Naming convention:**
   - Use descriptive names: `inventory-sync-flow.png`
   - Avoid spaces in filenames
   - Use lowercase with hyphens

3. **Diagram recommendations:**
   - Architecture overview
   - Data flow diagrams
   - API endpoint map
   - Database schema visualization
   - Deployment topology
   - User journey flows

4. **Tools to create diagrams:**
   - draw.io (free, web-based)
   - Lucidchart
   - Mermaid (already integrated in Slidev)
   - PlantUML

## Example Draw.io Diagrams to Create

1. **System Architecture:**
   - Frontend (React)
   - Backend (FastAPI)
   - Database (PostgreSQL)
   - Cache (Redis)
   - External APIs (Shopify)

2. **Custom Fields Flow:**
   - User creates field → API processes → Database storage → Shopify sync

3. **Authentication Sequence:**
   - OAuth flow with Shopify

4. **Deployment Architecture:**
   - Docker containers
   - Load balancer
   - Database cluster

Remember to update the image paths in the presentation files after adding your diagrams!
