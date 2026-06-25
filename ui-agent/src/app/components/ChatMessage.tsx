import { Bot, User, FileText, Image as ImageIcon, Reply, Edit, Trash2, Copy } from "lucide-react";
import { useState } from "react";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  file?: {
    name: string;
    type: string;
    url?: string;
  };
  files?: Array<{
    name: string;
    type: string;
    url?: string;
  }>;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
  onReply?: (message: Message) => void;
  onEdit?: (message: Message) => void;
  onDelete?: (messageId: string) => void;
  onCopy?: (content: string) => void;
}

export function ChatMessage({ message, onReply, onEdit, onDelete, onCopy }: ChatMessageProps) {
  const isUser = message.role === "user";
  const [showActions, setShowActions] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    if (onCopy) onCopy(message.content);
  };

  if (isUser) {
    // User message - right aligned
    return (
      <div
        className="flex gap-4 p-4 justify-end group"
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        <div className="flex gap-4 max-w-3xl">
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="font-medium mb-1 text-right">Bạn</div>

            {/* File attachments */}
            {((message.files && message.files.length > 0) || message.file) && (
              <div className="flex flex-col gap-2 mb-3 items-end">
                {(message.files || (message.file ? [message.file] : [])).map((file, idx) => (
                  <div key={idx} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/10 text-sm max-w-fit ml-auto">
                    {file.type.startsWith("image/") ? (
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-1.5 text-xs text-primary-foreground/80 justify-end">
                          <ImageIcon className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="truncate max-w-[150px]">{file.name}</span>
                        </div>
                        {file.url && (
                          <img
                            src={file.url}
                            alt={file.name}
                            className="max-w-xs max-h-40 rounded object-contain"
                          />
                        )}
                      </div>
                    ) : (
                      <>
                        <FileText className="w-4 h-4 flex-shrink-0" />
                        <span className="truncate max-w-[180px]">{file.name}</span>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Message text */}
            <div className="bg-primary text-primary-foreground rounded-2xl px-4 py-3 inline-block max-w-full">
              <p className="whitespace-pre-wrap m-0">{message.content}</p>
            </div>

            {/* Timestamp */}
            <div className="text-xs text-muted-foreground mt-2 text-right">
              {message.timestamp.toLocaleTimeString("vi-VN", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>

            {/* Action buttons - always rendered but hidden to prevent layout shift */}
            <div className={`flex items-center gap-1 mt-2 justify-end transition-opacity ${showActions ? "opacity-100" : "opacity-0"}`}>
              {onEdit && (
                <button
                  onClick={() => onEdit(message)}
                  className="p-1.5 rounded hover:bg-accent transition-colors"
                  title="Chỉnh sửa"
                  disabled={!showActions}
                >
                  <Edit className="w-3.5 h-3.5" />
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => onDelete(message.id)}
                  className="p-1.5 rounded hover:bg-accent transition-colors"
                  title="Xóa"
                  disabled={!showActions}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                onClick={handleCopy}
                className="p-1.5 rounded hover:bg-accent transition-colors"
                title="Sao chép"
                disabled={!showActions}
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Avatar */}
          <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-primary text-primary-foreground">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  // AI message - left aligned
  return (
    <div
      className="flex gap-4 p-4 bg-muted/30 group"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex gap-4 max-w-3xl w-full">
        {/* Avatar */}
        <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-accent">
          <Bot className="w-4 h-4" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="font-medium mb-1">X-Agent</div>

          {/* File attachments */}
          {((message.files && message.files.length > 0) || message.file) && (
            <div className="flex flex-col gap-2 mb-3 items-start">
              {(message.files || (message.file ? [message.file] : [])).map((file, idx) => (
                <div key={idx} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-accent text-sm max-w-fit">
                  {file.type.startsWith("image/") ? (
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <ImageIcon className="w-3.5 h-3.5 flex-shrink-0" />
                        <span className="truncate max-w-[150px]">{file.name}</span>
                      </div>
                      {file.url && (
                        <img
                          src={file.url}
                          alt={file.name}
                          className="max-w-xs max-h-40 rounded object-contain"
                        />
                      )}
                    </div>
                  ) : (
                    <>
                      <FileText className="w-4 h-4 flex-shrink-0" />
                      <span className="truncate max-w-[180px]">{file.name}</span>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Message text */}
          <div className="prose prose-sm max-w-none dark:prose-invert min-h-[1.5rem]">
            {message.content ? (
              renderContent(message.content)
            ) : (
              <div className="flex space-x-1 items-center h-5 opacity-50">
                <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div className="text-xs text-muted-foreground mt-2">
            {message.timestamp.toLocaleTimeString("vi-VN", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>

          {/* Action buttons - always rendered but hidden to prevent layout shift */}
          <div className={`flex items-center gap-1 mt-2 transition-opacity ${showActions ? "opacity-100" : "opacity-0"}`}>
            {onReply && (
              <button
                onClick={() => onReply(message)}
                className="p-1.5 rounded hover:bg-accent transition-colors"
                title="Trả lời"
                disabled={!showActions}
              >
                <Reply className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={handleCopy}
              className="p-1.5 rounded hover:bg-accent transition-colors"
              title="Sao chép"
              disabled={!showActions}
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
            {onDelete && (
              <button
                onClick={() => onDelete(message.id)}
                className="p-1.5 rounded hover:bg-accent transition-colors"
                title="Xóa"
                disabled={!showActions}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Markdown / Table Renderer Helpers
function renderContent(content: string) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  
  let inTable = false;
  let tableHeader: string[] = [];
  let tableRows: string[][] = [];
  
  let inList = false;
  let listItems: React.ReactNode[] = [];

  const flushList = (key: string | number) => {
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`ul-${key}`} className="list-disc pl-6 my-2 space-y-1 text-foreground/90">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const flushTable = (key: string | number) => {
    if (inTable && tableHeader.length > 0) {
      elements.push(
        <div key={`table-wrapper-${key}`} className="overflow-x-auto my-4 rounded-xl border border-border/80 shadow-md">
          <table className="min-w-full divide-y divide-border border-collapse text-sm">
            <thead className="bg-muted/80">
              <tr>
                {tableHeader.map((cell, idx) => (
                  <th key={`th-${idx}`} className="px-4 py-3 text-left font-semibold text-foreground/90 tracking-wider border-b border-border">
                    {parseInlineMarkdown(cell.trim())}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 bg-card">
              {tableRows.map((row, rowIdx) => (
                <tr key={`tr-${rowIdx}`} className="hover:bg-muted/40 transition-colors odd:bg-background/30 even:bg-muted/10">
                  {row.map((cell, cellIdx) => (
                    <td key={`td-${cellIdx}`} className="px-4 py-3 text-foreground/80 font-medium">
                      {parseInlineMarkdown(cell.trim())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableHeader = [];
      tableRows = [];
      inTable = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // 1. Check Table
    if (line.trim().startsWith('|')) {
      flushList(i);
      
      const parts = line.split('|').map(s => s.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
      
      // Bỏ qua dòng separator `|---|---|`
      if (parts.every(p => /^:?-+:?$/.test(p))) {
        inTable = true;
        continue;
      }
      
      if (!inTable) {
        // Đây là header
        tableHeader = parts;
        inTable = true;
      } else {
        // Đây là row
        tableRows.push(parts);
      }
      continue;
    } else {
      flushTable(i);
    }

    // 2. Check List
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      inList = true;
      const text = line.trim().substring(2);
      listItems.push(
        <li key={`li-${i}`}>
          {parseInlineMarkdown(text)}
        </li>
      );
      continue;
    } else {
      flushList(i);
    }

    // 3. Regular Paragraphs or Headers
    if (line.trim() === '') {
      elements.push(<div key={`br-${i}`} className="h-2" />);
    } else {
      if (line.startsWith('###')) {
        elements.push(
          <h3 key={`h3-${i}`} className="text-base font-semibold text-foreground mt-4 mb-2">
            {parseInlineMarkdown(line.substring(3).trim())}
          </h3>
        );
      } else if (line.startsWith('##')) {
        elements.push(
          <h2 key={`h2-${i}`} className="text-lg font-bold text-foreground mt-5 mb-3">
            {parseInlineMarkdown(line.substring(2).trim())}
          </h2>
        );
      } else {
        elements.push(
          <p key={`p-${i}`} className="my-1.5 leading-relaxed text-foreground/90">
            {parseInlineMarkdown(line)}
          </p>
        );
      }
    }
  }

  // Flush remaining elements
  flushList('end');
  flushTable('end');

  return <div className="space-y-1.5">{elements}</div>;
}

function parseInlineMarkdown(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const boldParts = text.split('**');
  
  for (let bIdx = 0; bIdx < boldParts.length; bIdx++) {
    const isBold = bIdx % 2 === 1;
    const currentPart = boldParts[bIdx];
    
    if (isBold) {
      parts.push(<strong key={`b-${bIdx}`} className="font-bold text-foreground">{parseItalicOrCode(currentPart)}</strong>);
    } else {
      parts.push(<span key={`n-${bIdx}`}>{parseItalicOrCode(currentPart)}</span>);
    }
  }
  
  return <>{parts}</>;
}

function parseItalicOrCode(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const codeParts = text.split('`');
  
  for (let cIdx = 0; cIdx < codeParts.length; cIdx++) {
    const isCode = cIdx % 2 === 1;
    const currentPart = codeParts[cIdx];
    
    if (isCode) {
      parts.push(
        <code key={`c-${cIdx}`} className="bg-muted px-1.5 py-0.5 rounded font-mono text-xs text-primary font-medium border border-border/30">
          {currentPart}
        </code>
      );
    } else {
      const italicParts = currentPart.split('*');
      for (let iIdx = 0; iIdx < italicParts.length; iIdx++) {
        const isItalic = iIdx % 2 === 1;
        const subPart = italicParts[iIdx];
        if (isItalic) {
          parts.push(<em key={`i-${iIdx}`} className="italic text-foreground/95">{subPart}</em>);
        } else {
          parts.push(<span key={`s-${iIdx}`}>{subPart}</span>);
        }
      }
    }
  }
  
  return <>{parts}</>;
}
