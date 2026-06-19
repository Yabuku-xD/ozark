import pretext from "pretext";

export function RichText({ text, as: Component = "div", className }) {
  if (!text) return null;
  // pretext(text) returns HTML string with paragraphs, bold, italic, code
  const html = pretext(text);
  return (
    <Component
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export function InlineCode({ children }) {
  return (
    <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono text-primary">
      {children}
    </code>
  );
}
