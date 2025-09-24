# SVG Metadata & Gallery v2

**Goal:** Every output image is self-describing, and the gallery can filter/sort/search/rate results, enabling iterative “best-of” sweeps.

---

## Phase A (next release)

### 1) Embed metadata in SVG

Write a `<metadata>` element that includes:

1) **XMP (RDF/XML)** — compatible with Adobe Bridge, PS, etc.

Namespaces:
- `xmlns:x="adobe:ns:meta/"`
- `xmlns:dc="http://purl.org/dc/elements/1.1/"`
- `xmlns:xmp="http://ns.adobe.com/xap/1.0/"`
- `xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"`
- `xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"`
- `xmlns:cubist="https://example.com/ns/cubist/1.0/"`  (custom)

Fields:
- `dc:title` — filename
- `dc:creator` — "cubist_art"
- `xmp:CreateDate`, `xmp:MetadataDate` — ISO 8601
- `xmp:Rating` — 0–5 (int; default 0)
- `xmpMM:DocumentID`, `xmpMM:InstanceID` — UUIDs
- `photoshop:ColorMode` — "RGB"
- `cubist:*` (custom)
  - `toolVersion`, `gitCommit` (if available)
  - `geometry` (`delaunay|voronoi|rectangles|plugin`)
  - `points`, `seed`
  - `seedMode` (`uniform|poisson|edge|…`) + `poissonMinPx` (opt)
  - `cascadeStages` (opt), `cascadeFill` (`image|flat|…`, opt)
  - `inputPath` (relative), `inputHash` (SHA1)
  - `canvasSize` (e.g., `"1920x1080"`)
  - `paramsJSON` (minified JSON with **all** extra params)

2) **Compact JSON mirror** for fast internal parsing:

```xml
<metadata id="cubist-json" type="application/json">
{"tool":"cubist_art","v":"1.0.0","geometry":"delaunay","points":1200,"seed":123,"seed_mode":"poisson","poisson_min_px":22,"cascade":{"stages":3,"fill":"image"},"input":{"path":"./input/your_input_image.jpg","sha1":"..."},"canvas":{"w":1920,"h":1080},"extra":{},"rating":0,"tags":[]}
</metadata>
Optional: --embed-thumb adds <metadata id="cubist-thumb" type="image/jpeg">…base64…</metadata> (tiny ~320px JPEG preview).

Acceptance (Phase A):

New SVGs contain both XMP and JSON blocks.

scripts/make_gallery.py reads either block and displays key fields.

Gallery supports search/filter/sort without writing back stars.

Phase B (later)

Local gallery_server.py to persist ratings (ratings.json) and optionally write back xmp:Rating.

Sweep biasing: prod_sweep.py --use-top N re-runs with top-rated params.

Tagging/LUT presets.

Example <metadata> (truncated)
<metadata>
  <x:xmpmeta xmlns:x="adobe:ns:meta/">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:dc="http://purl.org/dc/elements/1.1/"
             xmlns:xmp="http://ns.adobe.com/xap/1.0/"
             xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
             xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
             xmlns:cubist="https://example.com/ns/cubist/1.0/">
      <rdf:Description xmp:CreateDate="2025-09-02T10:03:12Z"
                       xmp:MetadataDate="2025-09-02T10:03:12Z"
                       xmp:Rating="0"
                       xmpMM:DocumentID="xmp.did:7d0f0f4a-..."
                       xmpMM:InstanceID="xmp.iid:3b2a6f2e-..."
                       photoshop:ColorMode="RGB"
                       cubist:toolVersion="1.0.0"
                       cubist:gitCommit="abc1234"
                       cubist:geometry="delaunay"
                       cubist:points="1200"
                       cubist:seed="123"
                       cubist:seedMode="poisson"
                       cubist:poissonMinPx="22"
                       cubist:cascadeStages="3"
                       cubist:cascadeFill="image"
                       cubist:inputPath="./input/your_input_image.jpg"
                       cubist:inputHash="sha1:..."
                       cubist:canvasSize="1920x1080"
                       cubist:paramsJSON="{&quot;seed_mode&quot;:&quot;poisson&quot;, ...}">
        <dc:title><rdf:Alt><rdf:li xml:lang="x-default">prod_delaunay_poisson.svg</rdf:li></rdf:Alt></dc:title>
        <dc:creator><rdf:Seq><rdf:li>cubist_art</rdf:li></rdf:Seq></dc:creator>
      </rdf:Description>
    </rdf:RDF>
  </x:xmpmeta>

  <metadata id="cubist-json" type="application/json">
    {"tool":"cubist_art","v":"1.0.0", ...}
  </metadata>
</metadata>

Gallery v2 UI (Phase A)

Top controls: search box; filters (geometry, seed_mode, date, rating≥N); sorts (name/date/rating/points asc/desc).

Tile: SVG (object/embed) + collapsible metadata panel.

Ratings UI writes to local ratings.json only (no SVG write-back in Phase A).

Dev Notes

Escape braces in Python .format() HTML/CSS by doubling: {{ }}.

Keep metadata writer in svg_export.write_svg(..., meta=dict) to avoid touching geometry code.

Unit tests:

XMP + JSON present.

JSON round-trips to meta dict.

Gallery parser handles both blocks and missing fields gracefully.
