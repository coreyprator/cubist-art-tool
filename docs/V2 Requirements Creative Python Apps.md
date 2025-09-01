# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/V2 Requirements Creative Python Apps.md
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:30+02:00
# === CUBIST STAMP END ===
1. Project Purpose
1.1. What’s the high-level goal of V2?
1.2. The purpose of version 2 of this project is to take the app to a new level of creativity.
1.3. V1 was a proof of concept: generate cubist images from a reference image.
1.4. V1 limitations: geometric shapes based on a fixed set of random points, bound by an input mask at the edge of the image.
1.5. V2 adds the following features.

2. Key New Features in V2
// The following features are intended to push the creative boundaries beyond V1’s geometry-locked design and static output limitations.
2.1. Expanded Input Support: Accepts both raster (PNG, JPEG) and, optionally, vector (SVG) images as input. JSON config files (required for advanced geometric and color customization) are supported.
2.2. Flexible Output Options: Exports to PNG, SVG (with layers/groups/metadata), and optionally layered PSD. Supports animated SVG morphs and image series for animation workflows.
2.3. Modular Plugin System: Easily add new shape modes, export types, or AI-based features (e.g., mask generation) without modifying core code.
2.4. Preset Management: Save, load, and share presets for shapes, palettes, brushes, and settings to streamline creative workflows.
2.5. AI-Assisted Masking: Optional integration with external tools or plugins for automated region selection and edge detection.
2.6. Cross-Platform & Web-Ready: Designed for Windows, macOS, and Linux, with planned support for web and mobile platforms in future versions. GUI can be Tkinter (desktop) or a lightweight web UI (browser/mobile).
2.7. Performance & Scalability: Async rendering and shape count limits maintain responsiveness, even with large images or complex fills.
2.8. Enhanced Usability: Clear documentation, tooltips, error messages, and debug overlays for color/geometry decisions.
2.9. Testability & Maintainability: Modular architecture, unit tests for rendering/geometry, and clean separation of logic and UI.

3. Canonical User Stories
3.1. 🎨 Digital Artist: As a digital artist, I want to export artwork as SVG or layered PSD so I can edit it precisely in Illustrator or Photoshop.
3.2. 🧑‍🎨 Power User: As a power user, I want to apply different LUTs, color themes, and custom palettes to influence mood and palette.
3.3. 🌀 Generative Art Tinkerer: As a generative art tinkerer, I want to switch between Delaunay, Voronoi, rectangles, circles, polygons, blobs, and custom shapes.
3.4. 👨‍💻 Creative Coder: As a creative coder, I want to preview the fill process step-by-step and export animations or morphs.
3.5. 🖌️ Designer: As a designer, I want to combine and configure different shape types and brush presets for unique effects.
3.6. 👤 User: As a user, I want to adjust edge sensitivity, influence, and use AI-assisted masks for smarter shape placement.
3.7. 🖍️ Illustrator: As an illustrator, I want to use and share custom brushes for lines and fills, compatible with Adobe standards.
3.8. ⚙️ Batch User: As a batch user, I want to run the app from the command line with config files for automation and scripting.
3.9. 🤝 Collaborator: As a collaborator, I want session history, logs, and shared presets for reviewing and sharing my creative process.
3.10. 🌐 Cross-Platform User: As a cross-platform user, I want the app to work on Windows, macOS, Linux, or web/mobile.
3.11. 👨‍💻 Developer: As a developer, I want a modular, plugin-friendly architecture for easy extension and maintenance.
3.12. 👤 User: As a user, I want to save, load, and share presets for quick reuse of favorite settings.
3.13. 🎞️ Animator: As an animator, I want to export animated SVG morphs or image series for dynamic artwork.
3.14. 🧑‍🔬 Technical User: As a technical user, I want debug overlays for color and geometry to fine-tune results.
3.15. 👤 User: As a user, I want to import SVG input and export annotated overlays for Illustrator guides.
3.16. 🤖 User: As a user, I want to use AI-based mask generation to automate region selection or edge detection.

4. Feature Requirements
4.1. Advanced Geometry Engine // Supports 3.3, 3.4, 3.5
4.1.1. Support Delaunay, Voronoi, rectangles, circles, mesh, ellipses, polygons, and blobs as fill modes.
4.1.2. Implement shape-packing logic that prioritizes larger geometric primitives first.
4.1.3. Edge-aware fill using Canny/Sobel, with user controls for edge sensitivity and influence.
4.2. Step-by-Step Fill Preview & Live UI Controls // Supports 3.4, 3.5
4.2.1. Preview fill process incrementally (point-by-point or in batches).
4.2.2. Timeline scrubber UI with playback speed controls and frame navigation.
4.2.3. Allow configuration and combination of shape types and parameters (e.g., ellipse aspect ratio, polygon sides).
4.3. Enhanced Output Formats & Post-Editing // Supports 3.1, 3.10
4.3.1. Export to PNG (raster), SVG (vector with groups/layers/metadata), and optionally layered PSD.
4.3.2. SVG output preserves geometry, color, and layer structure for editing in Illustrator.
4.3.3. Configurable export settings for post-processing workflows.
4.4. Color Handling & Palette/LUT Controls // Supports 3.2, 3.5, 3.14
4.4.1. Select/import custom palettes, apply LUTs/gradient ramps.
4.4.2. Previews and adjustment tools for palette/LUT effects.
4.4.3. Debug overlays to visualize color and LUT decisions.
4.5. Customizable Brushes for Line/Stroke and Fill // Supports 3.5, 3.7
4.5.0. Vector and raster brush customization enables artists to achieve both scalable (SVG) and painterly (PNG/PSD) effects, supporting a wide range of creative workflows.
4.5.1. Vector brushes: SVG output supports custom vector brushes (width, shape, style).
4.5.2. Raster brushes: PNG/PSD output supports raster brush textures, opacity, and blending.
4.5.3. Save, import, and export brush presets (Adobe-compatible).
4.6. Automation, CLI, and Session Management // Supports 3.8, 3.9
4.6.1. CLI switches and batch mode for automation.
4.6.2. Config file support for reproducible runs.
4.6.3. Session history and logs for traceability.
4.7. Modular Plugin Architecture // Supports 3.11
4.7.1. Core logic and UI layers are modular and decoupled.
4.7.2. Plugins can add new shape modes, export types, or AI features without modifying core code.
4.8. Preset Manager // Supports 3.12, 3.9
4.8.1. Save, load, and share presets for shapes, palettes, brushes, and settings.
4.9. AI-Assisted Mask Generation // Supports 3.6, 3.16
4.9.1. Optional integration with external tools or plugins for automated region selection and edge detection.

5. Inputs & Outputs
5.1. Accepted Input Formats
5.1.1. Raster images (PNG, JPEG)
5.1.2. Optional: Vector images (SVG) for future support
5.1.3. JSON config files for geometry and color
5.2. Output Formats
5.2.1. Raster: PNG
5.2.2. Vector: SVG with groups/layers and attributes
5.2.3. Optional: Annotated mask/overlay for Illustrator guides (SVG/PNG)
5.2.4. Optional: Layered PSD (see Stretch Goals)
5.2.5. Optional: Export frame-by-frame PNG or animated SVG for use in post-production tools.

6. Technical Requirements
6.1. Core Dependencies
6.1.1. Python 3.11+ (runtime)
6.1.2. scipy
6.1.3. matplotlib
6.1.4. opencv-python
6.1.5. svgwrite
6.1.6. cairosvg
6.2. Optional/Recommended Dependencies
6.2.1. Tkinter (desktop GUI)
6.2.2. Lightweight web UI framework (future)
6.2.3. pytest (testing)
6.2.4. Pillow (image manipulation)
6.2.5. pydantic (config validation)
6.3. Future/Stretch Dependencies
6.3.1. svgpathtools (advanced SVG manipulation)
6.4. Supported Operating Systems
6.4.1. Windows
6.4.2. macOS
6.4.3. Linux

7. Non-Functional Goals
7.1. Performance: Cap shape count or use async rendering for responsiveness. // Supports 3.7, 3.13
7.2. Maintainability: Clean separation of logic and GUI. // Supports 3.11
7.3. Testability: Unit tests for rendering and geometry. // Supports 3.4, 3.9
7.4. Extensibility: Modular architecture for plugins and new features. // Supports 3.11
7.5. Usability: Clear documentation, tooltips, and error messages. // Supports 3.8, 3.10

8. Cross-References & Consistency
8.1. User stories (Section 3) are the canonical source; all features and requirements should trace back to these.
8.2. Plugin architecture, preset manager, and AI mask generation are now in Feature Requirements, not Outputs.
8.3. All sections reference and build on each other for clarity and maintainability.

9. Stretch Goals
9.1. Layered PSD export for advanced post-editing.
9.2. SVG input for vector-based workflows.
9.3. Web/mobile UI prototype (e.g., Streamlit, Gradio, or PyScript).
9.4. AI-based mask generation and smart region selection.
9.5. Advanced animation export (SVG morphs, GIF, video).

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:30+02:00
# === CUBIST FOOTER STAMP END ===
