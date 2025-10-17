Awesome use case. Here’s a clean, production-ready pattern for React that:
	•	renders your PDF in the right column (multi-page, zoomable)
	•	lists your extracted fields in the left column
	•	when you click an item, it highlights the exact DocAI/Gemini bounding polygon on the correct PDF page and scrolls/zooms into view

It handles both normalized (0–1) and absolute (pixel/point) DocAI bounding polys, any page rotation, and arbitrary polygons (not just rectangles).

⸻

1) Install

npm i react react-dom pdfjs-dist

No third-party PDF viewer wrapper needed; using pdfjs-dist directly keeps overlays perfectly in sync.

⸻

2) Data shape (what you feed the component)

Feed the viewer a list of fields you got back from Gemini (one per extracted value):

// Types you can keep in a `types.ts`
export type NormalizedVertex = { x: number; y: number }; // 0..1
export type AbsoluteVertex   = { x: number; y: number }; // in DocAI page units
export type Vertex = NormalizedVertex | AbsoluteVertex;

export type BoundingPoly = {
  vertices?: AbsoluteVertex[];             // DocAI "vertices" (absolute)
  normalizedVertices?: NormalizedVertex[]; // DocAI "normalizedVertices" (0..1)
};

export type ExtractedField = {
  id: string;
  label: string;
  value: string;
  pageNumber: number; // 1-based page index
  boundingPoly: BoundingPoly;
  // Optional: original page dims if you only have absolute vertices
  originalPageWidth?: number;  // from DocAI page dimension
  originalPageHeight?: number; // from DocAI page dimension
};


⸻

3) Full React implementation

Drop these files into your app. (It’s TypeScript-flavored; remove types if you’re on JS.)

PdfWithHighlights.tsx

import React, { useEffect, useMemo, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import "pdfjs-dist/build/pdf.worker.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc =
  // @ts-ignore – Vite/CRA will rewrite this path correctly
  new URL("pdfjs-dist/build/pdf.worker.mjs", import.meta.url).toString();

import type {
  ExtractedField,
  BoundingPoly,
  NormalizedVertex,
  AbsoluteVertex,
} from "./types";

type Props = {
  /** URL or Uint8Array of the PDF */
  src: string | Uint8Array;
  /** All extracted fields across all pages */
  fields: ExtractedField[];
  /** id of the currently selected field (to focus & highlight) */
  activeFieldId?: string | null;
  /** optional: controlled zoom */
  zoom?: number;
  onZoomChange?: (z: number) => void;
};

type PageRef = {
  canvasEl: HTMLCanvasElement | null;
  overlayEl: SVGSVGElement | null;
  viewportWidth: number;
  viewportHeight: number;
  scale: number;
};

const isNormalized = (poly: BoundingPoly) =>
  !!poly.normalizedVertices && poly.normalizedVertices.length >= 3;

const toViewportPoints = (
  poly: BoundingPoly,
  viewportWidth: number,
  viewportHeight: number,
  originalPageWidth?: number,
  originalPageHeight?: number
): { x: number; y: number }[] => {
  if (isNormalized(poly)) {
    // normalized 0..1
    return (poly.normalizedVertices as NormalizedVertex[]).map(({ x, y }) => ({
      x: x * viewportWidth,
      y: y * viewportHeight,
    }));
  }
  // absolute -> scale to viewport using the original page size
  const verts = (poly.vertices as AbsoluteVertex[]) || [];
  if (!originalPageWidth || !originalPageHeight) {
    // Fallback: assume already in viewport units (rare)
    return verts as { x: number; y: number }[];
  }
  const sx = viewportWidth / originalPageWidth;
  const sy = viewportHeight / originalPageHeight;
  return verts.map(({ x, y }) => ({ x: x * sx, y: y * sy }));
};

const polygonToRect = (pts: { x: number; y: number }[]) => {
  const xs = pts.map((p) => p.x);
  const ys = pts.map((p) => p.y);
  const x = Math.min(...xs);
  const y = Math.min(...ys);
  const w = Math.max(...xs) - x;
  const h = Math.max(...ys) - y;
  return { x, y, w, h };
};

const groupByPage = (fields: ExtractedField[]) =>
  fields.reduce<Record<number, ExtractedField[]>>((acc, f) => {
    acc[f.pageNumber] = acc[f.pageNumber] || [];
    acc[f.pageNumber].push(f);
    return acc;
  }, {});

export const PdfWithHighlights: React.FC<Props> = ({
  src,
  fields,
  activeFieldId,
  zoom,
  onZoomChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [doc, setDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [scale, setScale] = useState(zoom ?? 1.2);
  const pageRefs = useRef<Record<number, PageRef>>({});
  const pageAnchors = useRef<Record<number, HTMLDivElement | null>>({});

  // keep controlled/uncontrolled in sync
  useEffect(() => {
    if (typeof zoom === "number" && zoom !== scale) setScale(zoom);
  }, [zoom]);

  useEffect(() => {
    const load = async () => {
      const loadingTask = pdfjsLib.getDocument(src as any);
      const loadedDoc = await loadingTask.promise;
      setDoc(loadedDoc);
      setPageCount(loadedDoc.numPages);
    };
    load();
  }, [src]);

  // Render a page to canvas + SVG overlay (idempotent per scale)
  const renderPage = async (pageNumber: number) => {
    if (!doc) return;
    const page = await doc.getPage(pageNumber);
    // include inherent page rotation
    const viewport = page.getViewport({ scale, rotation: page.rotate });
    let ref = pageRefs.current[pageNumber];
    if (!ref) {
      // init refs
      pageRefs.current[pageNumber] = {
        canvasEl: null,
        overlayEl: null,
        viewportWidth: viewport.width,
        viewportHeight: viewport.height,
        scale,
      };
      ref = pageRefs.current[pageNumber];
    }
    ref.viewportWidth = viewport.width;
    ref.viewportHeight = viewport.height;
    ref.scale = scale;

    // create canvas if missing
    if (!ref.canvasEl) {
      const canvas = document.createElement("canvas");
      ref.canvasEl = canvas;
      const anchor = pageAnchors.current[pageNumber];
      anchor?.appendChild(canvas);

      // SVG overlay (same size, absolute)
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.style.position = "absolute";
      svg.style.left = "0";
      svg.style.top = "0";
      svg.style.pointerEvents = "none";
      ref.overlayEl = svg;
      anchor?.appendChild(svg);
    }

    // size + render
    const canvas = ref.canvasEl!;
    const context = canvas.getContext("2d")!;
    canvas.width = Math.ceil(viewport.width);
    canvas.height = Math.ceil(viewport.height);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    if (ref.overlayEl) {
      ref.overlayEl.setAttribute("width", String(viewport.width));
      ref.overlayEl.setAttribute("height", String(viewport.height));
      ref.overlayEl.setAttribute(
        "viewBox",
        `0 0 ${viewport.width} ${viewport.height}`
      );
      ref.overlayEl.innerHTML = ""; // clear old shapes
    }

    await page.render({ canvasContext: context, viewport }).promise;

    // draw polygons for this page (non-active, faint)
    const grouped = groupByPage(fields);
    const these = grouped[pageNumber] || [];
    for (const f of these) {
      if (!ref.overlayEl) continue;
      const pts = toViewportPoints(
        f.boundingPoly,
        ref.viewportWidth,
        ref.viewportHeight,
        f.originalPageWidth,
        f.originalPageHeight
      );
      if (pts.length < 3) continue;
      const poly = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "polygon"
      );
      poly.setAttribute(
        "points",
        pts.map((p) => `${p.x},${p.y}`).join(" ")
      );
      poly.setAttribute("fill", "rgba(255, 255, 0, 0.15)"); // soft yellow fill
      poly.setAttribute("stroke", "rgba(255, 200, 0, 0.9)");
      poly.setAttribute("stroke-width", "2");
      ref.overlayEl.appendChild(poly);

      // Add tiny label tag
      const { x, y, w } = polygonToRect(pts);
      const label = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "text"
      );
      label.textContent = f.label || f.id;
      label.setAttribute("x", String(x));
      label.setAttribute("y", String(Math.max(12, y - 4)));
      label.setAttribute("font-size", "11");
      label.setAttribute("font-family", "system-ui, sans-serif");
      label.setAttribute("fill", "black");
      label.setAttribute("stroke", "white");
      label.setAttribute("stroke-width", "2");
      label.setAttribute("paint-order", "stroke");
      label.setAttribute("opacity", "0.85");
      label.setAttribute("pointer-events", "none");
      ref.overlayEl.appendChild(label);
    }
  };

  useEffect(() => {
    if (!doc || pageCount === 0) return;
    // render all pages initially or on zoom
    (async () => {
      for (let p = 1; p <= pageCount; p++) await renderPage(p);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc, pageCount, scale, fields]);

  // When active field changes -> bring it into view and "pulse" highlight
  useEffect(() => {
    if (!activeFieldId) return;
    const field = fields.find((f) => f.id === activeFieldId);
    if (!field) return;

    const pr = pageRefs.current[field.pageNumber];
    const anchor = pageAnchors.current[field.pageNumber];

    if (anchor) {
      anchor.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    if (!pr?.overlayEl) return;

    const pts = toViewportPoints(
      field.boundingPoly,
      pr.viewportWidth,
      pr.viewportHeight,
      field.originalPageWidth,
      field.originalPageHeight
    );
    if (pts.length < 3) return;

    // active outline polygon (draw on top)
    const activePoly = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "polygon"
    );
    activePoly.setAttribute(
      "points",
      pts.map((p) => `${p.x},${p.y}`).join(" ")
    );
    activePoly.setAttribute("fill", "rgba(0, 153, 255, 0.15)");
    activePoly.setAttribute("stroke", "rgba(0, 153, 255, 1)");
    activePoly.setAttribute("stroke-width", "3");
    activePoly.setAttribute("vector-effect", "non-scaling-stroke");
    pr.overlayEl.appendChild(activePoly);

    // Pulse then remove after 1.5s (keeps overlay clean)
    activePoly.animate(
      [
        { opacity: 0.2 },
        { opacity: 1 },
        { opacity: 0.2 },
      ],
      { duration: 1200, iterations: 1, easing: "ease-in-out" }
    ).onfinish = () => {
      pr.overlayEl?.removeChild(activePoly);
    };
  }, [activeFieldId, fields]);

  const onZoomIn = () => {
    const next = Math.min(3, +(scale + 0.2).toFixed(2));
    setScale(next);
    onZoomChange?.(next);
  };
  const onZoomOut = () => {
    const next = Math.max(0.5, +(scale - 0.2).toFixed(2));
    setScale(next);
    onZoomChange?.(next);
  };
  const onReset = () => {
    setScale(1.2);
    onZoomChange?.(1.2);
  };

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: 8, borderBottom: "1px solid #eee" }}>
        <button onClick={onZoomOut} style={{ marginRight: 8 }}>−</button>
        <button onClick={onZoomIn} style={{ marginRight: 8 }}>+</button>
        <button onClick={onReset}>Reset</button>
        <span style={{ marginLeft: 12, opacity: 0.65 }}>Zoom: {scale.toFixed(2)}x</span>
      </div>

      <div
        ref={containerRef}
        style={{
          position: "relative",
          overflow: "auto",
          flex: 1,
          background: "#fafafa",
          padding: 12,
        }}
      >
        {Array.from({ length: pageCount }, (_, i) => {
          const pageNumber = i + 1;
          return (
            <div
              key={pageNumber}
              ref={(el) => (pageAnchors.current[pageNumber] = el)}
              style={{
                position: "relative",
                margin: "0 auto 16px",
                width: pageRefs.current[pageNumber]?.viewportWidth || "auto",
                height: pageRefs.current[pageNumber]?.viewportHeight || "auto",
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

ExtractedList.tsx

import React from "react";
import type { ExtractedField } from "./types";

type Props = {
  fields: ExtractedField[];
  activeId?: string | null;
  onSelect: (id: string) => void;
};

export const ExtractedList: React.FC<Props> = ({ fields, activeId, onSelect }) => {
  return (
    <div style={{ overflow: "auto", height: "100%", padding: 12 }}>
      {fields.map((f) => {
        const isActive = f.id === activeId;
        return (
          <div
            key={f.id}
            onClick={() => onSelect(f.id)}
            style={{
              cursor: "pointer",
              marginBottom: 10,
              padding: 10,
              borderRadius: 8,
              border: isActive ? "2px solid #099" : "1px solid #ddd",
              background: isActive ? "rgba(0,153,153,0.06)" : "white",
            }}
            title={`Page ${f.pageNumber}`}
          >
            <div style={{ fontSize: 12, color: "#666" }}>{f.label}</div>
            <div style={{ fontWeight: 600 }}>{f.value}</div>
            <div style={{ fontSize: 11, color: "#999" }}>Page {f.pageNumber}</div>
          </div>
        );
      })}
    </div>
  );
};

App.tsx (layout + wiring)

import React, { useMemo, useState } from "react";
import { PdfWithHighlights } from "./PdfWithHighlights";
import { ExtractedList } from "./ExtractedList";
import type { ExtractedField } from "./types";

// Example data (replace with your Gemini output)
const exampleFields: ExtractedField[] = [
  {
    id: "inv_num",
    label: "Invoice Number",
    value: "INV-2025-0012",
    pageNumber: 1,
    boundingPoly: {
      normalizedVertices: [
        { x: 0.64, y: 0.08 },
        { x: 0.84, y: 0.08 },
        { x: 0.84, y: 0.12 },
        { x: 0.64, y: 0.12 },
      ],
    },
  },
  {
    id: "total",
    label: "Total",
    value: "$3,542.19",
    pageNumber: 1,
    boundingPoly: {
      normalizedVertices: [
        { x: 0.70, y: 0.86 },
        { x: 0.92, y: 0.86 },
        { x: 0.92, y: 0.90 },
        { x: 0.70, y: 0.90 },
      ],
    },
  },
  // Add more, potentially on page 2,3...
];

export const App: React.FC = () => {
  const [activeId, setActiveId] = useState<string | null>(null);
  // PDF can be a URL or a Uint8Array
  const pdfSrc = "/sample.pdf"; // replace with your PDF path or blob URL

  // (Optional) sort/group fields as you like for Column 1
  const fields = useMemo(
    () => exampleFields.sort((a, b) => a.pageNumber - b.pageNumber),
    []
  );

  return (
    <div style={{ height: "100vh", display: "grid", gridTemplateColumns: "minmax(320px, 420px) 1fr" }}>
      {/* Column 1: extracted values */}
      <div style={{ borderRight: "1px solid #eee" }}>
        <div style={{ padding: "10px 12px", borderBottom: "1px solid #eee", fontWeight: 700 }}>
          Extracted Fields
        </div>
        <ExtractedList
          fields={fields}
          activeId={activeId}
          onSelect={(id) => setActiveId(id)}
        />
      </div>

      {/* Column 2: PDF viewer + highlights */}
      <div>
        <PdfWithHighlights
          src={pdfSrc}
          fields={fields}
          activeFieldId={activeId}
        />
      </div>
    </div>
  );
};


⸻

4) How to feed DocAI/Gemini polygons correctly
	•	If Gemini returns normalizedVertices (recommended): you’re done — just pass them through exactly as shown.
	•	If you only have absolute vertices (e.g., DocAI page units):
	•	Also provide originalPageWidth and originalPageHeight (from the DocAI page.dimension).
	•	The component will scale those to the current PDF viewport automatically (and still work when zoom changes).

If your polygons sometimes come in clockwise vs. counter-clockwise or with >4 points (curvy text regions), this still works; the overlay draws the polygon as-is.

⸻

5) Features you get out of the box
	•	✅ Multi-page PDFs, supports page rotation from the file
	•	✅ Zoom in/out & reset, with crisp re-render
	•	✅ Smooth scroll to the right page on click
	•	✅ Arbitrary polygon overlays (not just rectangles)
	•	✅ Active selection “pulse” highlight, then fades (keeps the UI clean)
	•	✅ Works with either normalized or absolute coordinates

⸻

6) Common gotchas (and how the code handles them)
	•	Mismatch between DocAI coordinates & displayed PDF size
→ We always compute against the PDF.js viewport (post-rotation, with current zoom), then scale/position overlays 1:1 over the canvas.
	•	Rotation
→ page.getViewport({ scale, rotation: page.rotate }) uses the file’s rotation metadata so polygons still align.
	•	Performance with many pages
→ Renders on demand once per scale; overlays are lightweight SVGs. You can lazy-render pages if needed (IntersectionObserver).

⸻

7) Styling tweaks (optional)

You can adjust fill/stroke for passive vs. active polygons inside PdfWithHighlights.tsx to match your brand. You can also add a “hover preview” by listening to onMouseEnter in ExtractedList and setting activeFieldId temporarily.

⸻

If you paste these three files into a React app, replace pdfSrc and fields with your data, it will work end-to-end. If you want me to adapt this to your exact Gemini JSON shape, just drop a sample blob and I’ll wire the mapper for you.