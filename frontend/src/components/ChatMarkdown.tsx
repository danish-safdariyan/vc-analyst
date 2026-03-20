"use client";

import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";

const components: Components = {
  p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ol: ({ children }) => (
    <ol className="mb-3 list-decimal space-y-2 pl-5 last:mb-0 marker:text-slate-500">{children}</ol>
  ),
  ul: ({ children }) => (
    <ul className="mb-3 list-disc space-y-2 pl-5 last:mb-0 marker:text-slate-500">{children}</ul>
  ),
  li: ({ children }) => <li className="leading-relaxed [&>p]:mb-0">{children}</li>,
  h1: ({ children }) => <h1 className="mb-2 mt-4 text-base font-bold first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 mt-4 text-sm font-bold first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-2 mt-3 text-sm font-semibold first:mt-0">{children}</h3>,
  blockquote: ({ children }) => (
    <blockquote className="mb-3 border-l-2 border-slate-300 pl-3 text-slate-600 italic">
      {children}
    </blockquote>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-indigo-600 underline underline-offset-2 hover:text-indigo-800"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
  hr: () => <hr className="my-4 border-slate-200" />,
  code: ({ className, children, ...props }) => {
    const inline = !className;
    if (inline) {
      return (
        <code
          className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.9em] text-slate-800"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code className={`font-mono text-xs text-slate-800 ${className ?? ""}`} {...props}>
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="mb-3 overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs last:mb-0">{children}</pre>
  ),
};

export default function ChatMarkdown({ children }: { children: string }) {
  return (
    <div className="mt-1 text-sm text-slate-800">
      <ReactMarkdown components={components}>{children}</ReactMarkdown>
    </div>
  );
}
