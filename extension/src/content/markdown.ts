// ─── Safe Markdown -> DOM renderer for chat replies ───────────────────────────
// Chat answers (LLM or rule-based) contain **bold**, lists, `code`, fenced blocks, headings, quotes and tables.
// Everything is built with createElement/textContent — model or profile text is NEVER assigned to innerHTML, so
// `<script>`, `<img onerror=…>` and `javascript:` links render as harmless text. Only http(s) links are linkified.

const FENCE = /^\s{0,3}(`{3,}|~{3,})\s*([\w+#-]*)\s*$/;
const HEADING = /^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$/;
const HR = /^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/;
const BULLET = /^(\s*)([-*•+])\s+(.*)$/;
const ORDERED = /^(\s*)(\d{1,3})[.)]\s+(.*)$/;
const QUOTE = /^\s{0,3}>\s?(.*)$/;
const TABLE_SEP = /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/;

const el = <K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
};

// ── inline ───────────────────────────────────────────────────────────────────

const INLINE_SRC = new RegExp(
  [
    "(`+)([\\s\\S]*?[^`])\\1(?!`)",                       // 1,2  inline code
    "\\*\\*([\\s\\S]+?)\\*\\*",                            // 3    bold
    "__([\\s\\S]+?)__",                                    // 4    bold
    "~~([\\s\\S]+?)~~",                                    // 5    strikethrough
    "\\*([^\\s*](?:[\\s\\S]*?[^\\s*])?)\\*",               // 6    italic
    "(?<![\\w])_([^\\s_](?:[\\s\\S]*?[^\\s_])?)_(?![\\w])", // 7    italic
    "\\[([^\\]]+)\\]\\((https?:\\/\\/[^\\s)]+)\\)",        // 8,9  link
    "(https?:\\/\\/[^\\s<>()]+[^\\s<>().,;:!?'\"])",        // 10   bare url
  ].join("|"),
  "g",
).source;

export function renderInline(text: string, parent: Node): void {
  let last = 0;
  // A fresh RegExp per call: renderInline recurses (bold inside italic ...) and a shared global regex would have its
  // lastIndex reset by the inner call, sending the outer loop back to the start forever.
  const INLINE = new RegExp(INLINE_SRC, "g");
  for (let m = INLINE.exec(text); m; m = INLINE.exec(text)) {
    if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
    if (m[2] !== undefined) parent.appendChild(el("code", undefined, m[2].trim()));
    else if (m[3] !== undefined || m[4] !== undefined) { const s = el("strong"); renderInline(m[3] ?? m[4], s); parent.appendChild(s); }
    else if (m[5] !== undefined) { const s = el("del"); renderInline(m[5], s); parent.appendChild(s); }
    else if (m[6] !== undefined || m[7] !== undefined) { const s = el("em"); renderInline(m[6] ?? m[7], s); parent.appendChild(s); }
    else if (m[8] !== undefined) parent.appendChild(link(m[9], m[8]));
    else if (m[10] !== undefined) parent.appendChild(link(m[10], m[10]));
    last = m.index + m[0].length;
  }
  if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
}

function link(href: string, label: string): HTMLAnchorElement {
  const a = el("a", undefined, label);
  a.href = href; // regex guarantees http(s)
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

// ── blocks ───────────────────────────────────────────────────────────────────

function codeBlock(lang: string, lines: string[]): HTMLElement {
  const wrap = el("div", "cq-code");
  const head = el("div", "cq-code-head");
  head.appendChild(el("span", undefined, lang || "code"));
  const copy = el("button", "cq-copy", "Copy");
  copy.type = "button";
  const body = lines.join("\n");
  copy.addEventListener("click", () => {
    navigator.clipboard?.writeText(body).then(() => { copy.textContent = "Copied"; setTimeout(() => (copy.textContent = "Copy"), 1200); }).catch(() => {});
  });
  head.appendChild(copy);
  const pre = el("pre");
  pre.appendChild(el("code", undefined, body));
  wrap.append(head, pre);
  return wrap;
}

interface ListItem { el: HTMLLIElement; indent: number }

function splitRow(line: string): string[] {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}

const isBlockStart = (l: string): boolean =>
  FENCE.test(l) || HEADING.test(l) || HR.test(l) || BULLET.test(l) || ORDERED.test(l) || QUOTE.test(l);

/** Render Markdown text into a DocumentFragment (safe: no innerHTML anywhere). */
export function renderMarkdown(src: string): DocumentFragment {
  const out = document.createDocumentFragment();
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }

    const f = line.match(FENCE);
    if (f) {
      const mark = f[1][0], lang = f[2];
      const body: string[] = [];
      i++;
      while (i < lines.length && !new RegExp(`^\\s{0,3}${mark}{${f[1].length},}\\s*$`).test(lines[i])) body.push(lines[i++]);
      i++; // closing fence (or end of a still-streaming block)
      out.appendChild(codeBlock(lang, body));
      continue;
    }

    const h = line.match(HEADING);
    if (h) {
      const level = Math.min(h[1].length, 3) + 2; // # -> h3 ... ### and deeper -> h5 (chat bubbles are small)
      const node = el(`h${level}` as "h3" | "h4" | "h5");
      renderInline(h[2], node);
      out.appendChild(node);
      i++; continue;
    }

    if (HR.test(line)) { out.appendChild(el("hr")); i++; continue; }

    if (QUOTE.test(line)) {
      const q: string[] = [];
      while (i < lines.length && QUOTE.test(lines[i])) q.push(lines[i++].match(QUOTE)![1]);
      const bq = el("blockquote");
      bq.appendChild(renderMarkdown(q.join("\n")));
      out.appendChild(bq);
      continue;
    }

    if (BULLET.test(line) || ORDERED.test(line)) {
      const root = el(ORDERED.test(line) && !BULLET.test(line) ? "ol" : "ul");
      const stack: { list: HTMLElement; indent: number }[] = [{ list: root, indent: (line.match(/^\s*/)![0]).length }];
      let last: ListItem | null = null;
      while (i < lines.length) {
        const bm = lines[i].match(BULLET), om = lines[i].match(ORDERED), m = bm ?? om;
        if (!m) {
          // continuation line of the previous item (indented text) — keep it inside that item
          if (last && lines[i].trim() && /^\s{2,}\S/.test(lines[i]) && !isBlockStart(lines[i])) {
            last.el.appendChild(document.createElement("br"));
            renderInline(lines[i].trim(), last.el); i++; continue;
          }
          break;
        }
        const indent = m[1].length, ordered = !!om && !bm;
        while (stack.length > 1 && indent < stack[stack.length - 1].indent) stack.pop();
        if (indent > stack[stack.length - 1].indent && last) {
          const sub = el(ordered ? "ol" : "ul");
          last.el.appendChild(sub);
          stack.push({ list: sub, indent });
        }
        const li = el("li");
        renderInline(m[3], li);
        stack[stack.length - 1].list.appendChild(li);
        last = { el: li, indent };
        i++;
      }
      out.appendChild(root);
      continue;
    }

    if (line.includes("|") && i + 1 < lines.length && TABLE_SEP.test(lines[i + 1]) && lines[i + 1].includes("-")) {
      const head = splitRow(line); i += 2;
      const table = el("table"), thead = el("thead"), tr = el("tr");
      head.forEach((c) => { const th = el("th"); renderInline(c, th); tr.appendChild(th); });
      thead.appendChild(tr); table.appendChild(thead);
      const tbody = el("tbody");
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        const row = el("tr");
        splitRow(lines[i++]).forEach((c) => { const td = el("td"); renderInline(c, td); row.appendChild(td); });
        tbody.appendChild(row);
      }
      table.appendChild(tbody);
      const scroller = el("div", "cq-table"); scroller.appendChild(table); out.appendChild(scroller);
      continue;
    }

    // paragraph: consecutive plain lines; single newlines stay visible as line breaks
    const p = el("p");
    let first = true;
    while (i < lines.length && lines[i].trim() && (first || !isBlockStart(lines[i]))) {
      if (!first) p.appendChild(document.createElement("br"));
      renderInline(lines[i].trim(), p);
      first = false; i++;
    }
    out.appendChild(p);
  }
  return out;
}

/** Markdown -> readable plain text (for text-to-speech and copy-to-clipboard). */
export function stripMarkdown(src: string): string {
  return src
    .replace(/```[\s\S]*?```/g, " code block. ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!?\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/(\*\*|__|~~)(.+?)\1/g, "$2")
    .replace(/(^|\s)[*_]([^*_\n]+)[*_](?=\s|$|[.,!?])/g, "$1$2")
    .replace(/^\s{0,3}#{1,6}\s+/gm, "")
    .replace(/^\s*[-*•+]\s+/gm, "")
    .replace(/^\s*>\s?/gm, "")
    .replace(/\|/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
