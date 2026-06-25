import { Send, Paperclip, Mic, Image as ImageIcon, Smile, X } from "lucide-react";
import { useState, useRef, type KeyboardEvent, type ChangeEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  centered?: boolean;
  attachments: File[];
  onRemoveAttachment: (index: number) => void;
}

export function ChatInput({ onSend, onFileSelect, disabled, centered, attachments, onRemoveAttachment }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if ((message.trim() || attachments.length > 0) && !disabled) {
      onSend(message);
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
      // Reset input value to allow selecting the same file again
      e.target.value = "";
    }
  };

  return (
    <div className={`border-t border-border bg-background p-4 ${centered ? "" : ""}`}>
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col gap-3">
          {/* File attachments preview */}
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 p-2 mb-1 bg-muted/30 rounded-xl border border-border max-w-fit">
              {attachments.map((file, idx) => {
                const isImage = file.type.startsWith("image/");
                return (
                  <div key={idx} className="flex items-center gap-2 bg-background border border-border rounded-lg p-1.5 pr-2 text-sm shadow-sm relative group">
                    {isImage ? (
                      <img
                        src={URL.createObjectURL(file)}
                        alt={file.name}
                        className="w-8 h-8 rounded object-cover"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary">
                        <Paperclip className="w-4 h-4" />
                      </div>
                    )}
                    <div className="flex flex-col max-w-[120px]">
                      <span className="truncate font-medium text-xs text-foreground">{file.name}</span>
                      <span className="text-[10px] text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</span>
                    </div>
                    <button
                      onClick={() => onRemoveAttachment(idx)}
                      className="p-1 hover:bg-accent rounded-full text-muted-foreground hover:text-foreground transition-colors ml-1 flex items-center justify-center"
                      title="Xóa tệp"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* Input area */}
          <div className="flex gap-2 items-end">
            {/* Action buttons - Left side */}
            <div className="flex gap-1 pb-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="w-9 h-9 rounded-lg hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                title="Tải lên tệp"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.txt,.csv,.png,.jpg,.jpeg,.webp"
                onChange={handleFileChange}
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="w-9 h-9 rounded-lg hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                title="Tải lên ảnh"
              >
                <ImageIcon className="w-5 h-5" />
              </button>
            </div>

            {/* Text input */}
            <div className="flex-1 relative">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Nhập câu hỏi của bạn..."
                disabled={disabled}
                rows={1}
                className="w-full resize-none rounded-2xl border border-border bg-muted text-foreground placeholder:text-muted-foreground px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  minHeight: "52px",
                  maxHeight: "200px",
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "52px";
                  target.style.height = Math.min(target.scrollHeight, 200) + "px";
                }}
              />

              {/* Emoji button inside input */}
              <button
                disabled={disabled}
                className="absolute right-3 bottom-3 w-6 h-6 rounded hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                title="Biểu tượng cảm xúc"
              >
                <Smile className="w-4 h-4" />
              </button>
            </div>

            {/* Action buttons - Right side */}
            <div className="flex gap-1 pb-2">
              <button
                disabled={disabled}
                className="w-9 h-9 rounded-lg hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                title="Ghi âm"
              >
                <Mic className="w-5 h-5" />
              </button>

              <button
                onClick={handleSend}
                disabled={(!message.trim() && attachments.length === 0) || disabled}
                className="w-9 h-9 rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity flex items-center justify-center"
                title="Gửi"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Helper text */}
          <p className="text-center text-sm text-muted-foreground">
            Nhấn Enter để gửi, Shift + Enter để xuống dòng
          </p>
        </div>
      </div>
    </div>
  );
}
