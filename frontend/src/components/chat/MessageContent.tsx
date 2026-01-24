import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { cn } from "@/lib/utils";

interface MessageContentProps {
  content: string;
  isUser?: boolean;
}

export function MessageContent({ content, isUser }: MessageContentProps) {
  // User messages are rendered as plain text
  if (isUser) {
    return <p className="whitespace-pre-wrap text-sm">{content}</p>;
  }

  // Assistant messages are rendered with Markdown
  return (
    <div
      className={cn(
        "prose prose-sm max-w-none dark:prose-invert",
        "prose-p:leading-relaxed prose-pre:p-0",
        "prose-headings:font-semibold prose-headings:tracking-tight",
        "prose-code:rounded prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5",
        "prose-code:before:content-none prose-code:after:content-none"
      )}
    >
      <ReactMarkdown
        components={{
          code({ node, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const inline = !match && !className;

            if (inline) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            }

            return (
              <div className="relative group">
                <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(String(children).replace(/\n$/, ""));
                    }}
                    className="rounded bg-background/80 px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
                  >
                    Copy
                  </button>
                </div>
                <SyntaxHighlighter
                  style={oneDark}
                  language={match?.[1] || "text"}
                  PreTag="div"
                  className="!rounded-lg !bg-[#1a1a1a] !my-3"
                  customStyle={{
                    margin: 0,
                    padding: "1rem",
                    fontSize: "0.875rem",
                  }}
                >
                  {String(children).replace(/\n$/, "")}
                </SyntaxHighlighter>
              </div>
            );
          },
          a({ children, href, ...props }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
                {...props}
              >
                {children}
              </a>
            );
          },
          ul({ children }) {
            return <ul className="my-2 ml-4 list-disc">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="my-2 ml-4 list-decimal">{children}</ol>;
          },
          li({ children }) {
            return <li className="my-1">{children}</li>;
          },
          p({ children }) {
            return <p className="mb-2 last:mb-0">{children}</p>;
          },
          h1({ children }) {
            return <h1 className="text-lg font-semibold mt-4 mb-2">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-base font-semibold mt-3 mb-2">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-sm font-semibold mt-2 mb-1">{children}</h3>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-2 border-muted-foreground/30 pl-4 italic text-muted-foreground">
                {children}
              </blockquote>
            );
          },
          table({ children }) {
            return (
              <div className="my-2 overflow-x-auto rounded-lg border">
                <table className="w-full text-sm">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="border-b bg-muted px-4 py-2 text-left font-medium">
                {children}
              </th>
            );
          },
          td({ children }) {
            return <td className="border-b px-4 py-2">{children}</td>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
