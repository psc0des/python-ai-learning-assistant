/**
 * CodeMirror 6 initializer for Python Skill Lab.
 *
 * Loaded as an ES module (<script type="module">), so it runs after app.js.
 * If CDN imports fail, the plain textarea still works.
 *
 * Bridge design:
 * - textarea.value getter reads from CodeMirror doc
 * - textarea.value setter writes into CodeMirror doc
 * - CodeMirror updates emit textarea input events for autosave
 *
 * The bridge intentionally avoids writing textarea.value inside update
 * listeners to prevent recursive update loops.
 */

import { EditorState } from "https://esm.sh/@codemirror/state@6";
import {
  EditorView,
  keymap,
  lineNumbers,
  highlightActiveLine,
  drawSelection,
  rectangularSelection,
  crosshairCursor,
} from "https://esm.sh/@codemirror/view@6";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "https://esm.sh/@codemirror/commands@6";
import { python } from "https://esm.sh/@codemirror/lang-python@6";
import {
  syntaxHighlighting,
  defaultHighlightStyle,
  indentOnInput,
  bracketMatching,
} from "https://esm.sh/@codemirror/language@6";
import { closeBrackets, closeBracketsKeymap } from "https://esm.sh/@codemirror/autocomplete@6";

const editorTheme = EditorView.theme({
  "&": {
    background: "#111916",
    color: "#e9f1e9",
  },
  ".cm-content": { caretColor: "#7fae95" },
  "&.cm-focused .cm-cursor": { borderLeftColor: "#7fae95" },
  ".cm-gutters": {
    background: "#17241f",
    color: "#6f8a7b",
    border: "none",
  },
  ".cm-activeLineGutter": { background: "#21332b" },
  ".cm-activeLine": { background: "#1d2c25" },
  ".cm-selectionBackground, ::selection": {
    background: "rgba(127,174,149,0.24) !important",
  },
  ".cm-scroller": { overflow: "auto" },
}, { dark: true });

let cmView = null;

const baseExtensions = [
  history(),
  lineNumbers(),
  drawSelection(),
  rectangularSelection(),
  crosshairCursor(),
  highlightActiveLine(),
  indentOnInput(),
  bracketMatching(),
  closeBrackets(),
  syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
  python(),
  keymap.of([
    indentWithTab,
    ...closeBracketsKeymap,
    ...defaultKeymap,
    ...historyKeymap,
  ]),
  EditorView.lineWrapping,
  EditorView.updateListener.of((update) => {
    if (!update.docChanged) return;
    const textarea = document.getElementById("editor");
    if (!textarea) return;
    if (textarea.dataset.cmApplying === "1") return;
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }),
];

function mountEditor() {
  const textarea = document.getElementById("editor");
  if (!textarea) return;

  const state = EditorState.create({
    doc: textarea.value || "",
    extensions: [...baseExtensions, editorTheme],
  });

  cmView = new EditorView({
    state,
    parent: textarea.parentElement,
  });

  textarea.parentElement.insertBefore(cmView.dom, textarea);
  textarea.classList.add("cm-hidden");
  textarea.setAttribute("aria-hidden", "true");

  Object.defineProperty(textarea, "value", {
    get() {
      return cmView ? cmView.state.doc.toString() : "";
    },
    set(nextValue) {
      if (!cmView) return;
      const next = String(nextValue ?? "");
      const current = cmView.state.doc.toString();
      if (next === current) return;

      textarea.dataset.cmApplying = "1";
      cmView.dispatch({
        changes: {
          from: 0,
          to: cmView.state.doc.length,
          insert: next,
        },
      });
      textarea.dataset.cmApplying = "0";
    },
    configurable: true,
  });

  textarea.addEventListener("focus", () => cmView && cmView.focus());

  cmView.dom.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      document.getElementById("runBtn")?.click();
    }
    if ((event.key === "s" || event.key === "S") && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      const coachStatus = document.getElementById("coachStatus");
      if (coachStatus) {
        coachStatus.textContent = "Draft saved";
        setTimeout(() => { coachStatus.textContent = "Provider ready"; }, 1500);
      }
      textarea.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });

  console.log("[CodeMirror 6] Mounted successfully.");
}

window.addEventListener("DOMContentLoaded", () => {
  setTimeout(mountEditor, 300);
});
