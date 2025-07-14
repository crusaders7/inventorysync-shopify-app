# InventorySync Presentation

This is a developer-friendly presentation built with Slidev, featuring code syntax highlighting, animations, and interactive elements.

## Getting Started

### Prerequisites
- Node.js 18+ installed on your system

### Installation

1. Navigate to the presentation directory:
```bash
cd presentation
```

2. Install dependencies:
```bash
npm install
```

### Running the Presentation

1. **Development mode** (with hot reload):
```bash
npm run dev
```
This will open the presentation in your browser at http://localhost:3030

2. **Build for production**:
```bash
npm run build
```

3. **Export to PDF**:
```bash
npm run export-pdf
```

4. **Export to static HTML**:
```bash
npm run export
```

## Features

- **Code Syntax Highlighting**: Beautiful code blocks with Shiki
- **Animations**: Smooth transitions and click animations
- **Interactive Elements**: Navigate with keyboard, mouse, or touch
- **Mermaid Diagrams**: Flow charts and sequence diagrams
- **Icons**: Carbon icon set integrated
- **Dark Mode**: Automatic theme switching
- **Export Options**: PDF, PNG, or hosted SPA

## Presentation Structure

1. **Title Slide**: Project introduction
2. **Table of Contents**: Auto-generated navigation
3. **Project Overview**: Key features and tech stack
4. **Architecture**: System design and components
5. **Custom Fields Deep Dive**: Core feature demonstration
6. **Code Examples**: Backend and frontend implementations
7. **Database Schema**: Performance optimizations
8. **Authentication Flow**: Mermaid sequence diagram
9. **Deployment**: Production architecture
10. **Testing & Security**: Best practices
11. **Future Roadmap**: Upcoming features

## Adding Images

To include your draw.io diagrams or screenshots:

1. Export your draw.io diagrams as PNG or SVG
2. Place them in the `public/` directory
3. Reference them in slides:
```markdown
---
layout: image
image: /your-diagram.png
---
```

## Customization

- Edit `slides.md` to modify content
- Update `style.css` for custom styling
- Modify `package.json` scripts for additional commands

## Keyboard Shortcuts

- **Space/Right Arrow**: Next slide
- **Left Arrow**: Previous slide
- **F**: Fullscreen
- **O**: Overview mode
- **D**: Dark mode toggle
- **G**: Go to slide (enter number)

## Tips for Presenting

1. Use presenter mode (press `P`) to see notes
2. Draw on slides with `D` key
3. Use laser pointer with mouse
4. Export to PDF for offline backup

## Troubleshooting

If you encounter Node.js version issues:
1. Use nvm or fnm to switch to Node.js 20+
2. Or use the alternative setup with npx:
```bash
npx @slidev/cli@latest slides.md
```

## Resources

- [Slidev Documentation](https://sli.dev)
- [Theme Gallery](https://sli.dev/themes/gallery.html)
- [Icon Explorer](https://icones.js.org/)
