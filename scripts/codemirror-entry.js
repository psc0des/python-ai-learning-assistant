// Entry point for the CodeMirror bundle.
// All exports needed by static/codemirror-init.js are re-exported here
// so esbuild can tree-shake and produce one self-contained file.

export { EditorState } from "@codemirror/state";
export {
  EditorView,
  keymap,
  lineNumbers,
  highlightActiveLine,
  drawSelection,
  rectangularSelection,
  crosshairCursor,
} from "@codemirror/view";
export { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
export { python } from "@codemirror/lang-python";
export { syntaxHighlighting, indentOnInput, bracketMatching } from "@codemirror/language";
export { oneDarkHighlightStyle } from "@codemirror/theme-one-dark";
export { closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
