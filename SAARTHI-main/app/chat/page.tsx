"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "../lib/auth";

type User = {
  id: string;
  name: string;
  role: "vendor" | "transporter";
  status: "online" | "offline" | "busy";
  lastSeen?: string;
  avatar: string;
};

type Message = {
  id: string;
  senderId: string;
  text?: string;
  type: "text" | "voice";
  duration?: string;
  timestamp: string;
  status: "sent" | "delivered" | "read";
};

const MOCK_USERS: User[] = [
  { id: "V001", name: "Ramesh Patel", role: "vendor", status: "online", avatar: "RP" },
  { id: "V002", name: "Sunita Devi", role: "vendor", status: "offline", lastSeen: "2h ago", avatar: "SD" },
  { id: "T001", name: "Arjun Singh", role: "transporter", status: "online", avatar: "AS" },
  { id: "T002", name: "Mohan Trucks", role: "transporter", status: "busy", avatar: "MT" },
  { id: "V003", name: "Kiran Farms", role: "vendor", status: "online", avatar: "KF" },
];

const MOCK_MESSAGES: Record<string, Message[]> = {
  V001: [
    { id: "1", senderId: "V001", text: "Bhai, mera 10 ton wheat ready hai. Kab pickup karoge?", type: "text", timestamp: "10:30 AM", status: "read" },
    { id: "2", senderId: "ME", text: "Kal subah 8 baje aa jaunga. Address confirm karo.", type: "text", timestamp: "10:32 AM", status: "read" },
    { id: "3", senderId: "V001", text: "Theek hai. Nagpur warehouse, Gate No. 3.", type: "text", timestamp: "10:33 AM", status: "read" },
    { id: "4", senderId: "ME", type: "voice", duration: "0:12", timestamp: "10:35 AM", status: "delivered" },
  ],
  T001: [
    { id: "1", senderId: "T001", text: "Sir, truck available hai aaj. 20 ton capacity.", type: "text", timestamp: "9:00 AM", status: "read" },
    { id: "2", senderId: "ME", text: "Rate kya hai Mumbai tak?", type: "text", timestamp: "9:05 AM", status: "read" },
    { id: "3", senderId: "T001", type: "voice", duration: "0:24", timestamp: "9:07 AM", status: "read" },
  ],
  V002: [],
  T002: [],
  V003: [],
};

export default function ChatPage() {
  const router = useRouter();
  const user = getUser();

  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isCallActive, setIsCallActive] = useState(false);
  const [callTime, setCallTime] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recordingInterval = useRef<NodeJS.Timeout | null>(null);
  const callInterval = useRef<NodeJS.Timeout | null>(null);

  const myId = "ME";

  useEffect(() => {
    if (!user) {
      router.replace("/login/supplier");
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const selectUser = (u: User) => {
    setSelectedUser(u);
    setMessages(MOCK_MESSAGES[u.id] || []);
    setIsCallActive(false);
    setCallTime(0);
    if (window.innerWidth < 768) setShowSidebar(false);
  };

  const sendMessage = () => {
    if (!inputText.trim() || !selectedUser) return;
    const newMsg: Message = {
      id: Date.now().toString(),
      senderId: myId,
      text: inputText,
      type: "text",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      status: "sent",
    };
    setMessages((prev) => [...prev, newMsg]);
    setInputText("");
  };

  const startRecording = () => {
    setIsRecording(true);
    setRecordingTime(0);
    recordingInterval.current = setInterval(() => {
      setRecordingTime((t) => t + 1);
    }, 1000);
  };

  const stopRecording = () => {
    if (!selectedUser) return;
    setIsRecording(false);
    if (recordingInterval.current) clearInterval(recordingInterval.current);
    const newMsg: Message = {
      id: Date.now().toString(),
      senderId: myId,
      type: "voice",
      duration: `0:${recordingTime.toString().padStart(2, "0")}`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      status: "sent",
    };
    setMessages((prev) => [...prev, newMsg]);
    setRecordingTime(0);
  };

  const startCall = () => {
    setIsCallActive(true);
    setCallTime(0);
    callInterval.current = setInterval(() => {
      setCallTime((t) => t + 1);
    }, 1000);
  };

  const endCall = () => {
    setIsCallActive(false);
    if (callInterval.current) clearInterval(callInterval.current);
    setCallTime(0);
  };

  const formatCallTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const filteredUsers = MOCK_USERS.filter((u) =>
    u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusColor = (status: string) => {
    if (status === "online") return "#22c55e";
    if (status === "busy") return "#f59e0b";
    return "#6b7280";
  };

  if (!user) return null;

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      width: "100vw",
      background: "#0a0f0a",
      fontFamily: "'Segoe UI', sans-serif",
      color: "#e8f5e9",
      overflow: "hidden",
    }}>

      {showSidebar && (
        <div style={{
          width: "340px",
          minWidth: "340px",
          background: "#0d1a0d",
          borderRight: "1px solid #1a2e1a",
          display: "flex",
          flexDirection: "column",
        }}>
          <div style={{
            padding: "20px 16px 12px",
            background: "#111f11",
            borderBottom: "1px solid #1a2e1a",
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{
                  width: "38px", height: "38px", borderRadius: "50%",
                  background: "linear-gradient(135deg, #22c55e, #16a34a)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "14px", fontWeight: "700", color: "white",
                }}>
                  {user.id.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div style={{ fontSize: "15px", fontWeight: "600" }}>{user.name}</div>
                  <div style={{ fontSize: "11px", color: "#4ade80" }}>● Online · {user.id}</div>
                </div>
              </div>
            </div>
            <div style={{
              background: "#0a150a",
              borderRadius: "8px",
              padding: "8px 12px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              border: "1px solid #1a2e1a",
            }}>
              <span style={{ color: "#4b5563", fontSize: "14px" }}>🔍</span>
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name or ID..."
                style={{
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "#e8f5e9",
                  fontSize: "13px",
                  width: "100%",
                }}
              />
            </div>
          </div>

          <div style={{ overflowY: "auto", flex: 1 }}>
            <div style={{ padding: "8px 16px 4px", fontSize: "11px", color: "#4ade80", fontWeight: "600", letterSpacing: "1px" }}>
              VENDORS
            </div>
            {filteredUsers.filter(u => u.role === "vendor").map((u) => (
              <UserItem key={u.id} user={u} selected={selectedUser?.id === u.id} onClick={() => selectUser(u)} statusColor={statusColor} />
            ))}

            <div style={{ padding: "12px 16px 4px", fontSize: "11px", color: "#60a5fa", fontWeight: "600", letterSpacing: "1px" }}>
              TRANSPORTERS
            </div>
            {filteredUsers.filter(u => u.role === "transporter").map((u) => (
              <UserItem key={u.id} user={u} selected={selectedUser?.id === u.id} onClick={() => selectUser(u)} statusColor={statusColor} />
            ))}
          </div>
        </div>
      )}

      <div style={{ flex: 1, display: "flex", flexDirection: "column", background: "#0a0f0a" }}>
        {!selectedUser ? (
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center", gap: "16px",
            color: "#374151",
          }}>
            <div style={{ fontSize: "64px" }}>🌾</div>
            <div style={{ fontSize: "22px", fontWeight: "600", color: "#1f2937" }}>SAARTHI Connect</div>
            <div style={{ fontSize: "14px", color: "#4b5563" }}>Select a vendor or transporter to start chatting</div>
          </div>
        ) : (
          <>
            <div style={{
              padding: "12px 20px",
              background: "#111f11",
              borderBottom: "1px solid #1a2e1a",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <button
                  onClick={() => setShowSidebar(true)}
                  style={{ background: "none", border: "none", color: "#9ca3af", cursor: "pointer", fontSize: "18px", display: showSidebar ? "none" : "block" }}
                >←</button>
                <div style={{ position: "relative" }}>
                  <div style={{
                    width: "42px", height: "42px", borderRadius: "50%",
                    background: selectedUser.role === "vendor"
                      ? "linear-gradient(135deg, #22c55e, #16a34a)"
                      : "linear-gradient(135deg, #3b82f6, #1d4ed8)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "13px", fontWeight: "700", color: "white",
                  }}>{selectedUser.avatar}</div>
                  <div style={{
                    position: "absolute", bottom: 1, right: 1,
                    width: "11px", height: "11px", borderRadius: "50%",
                    background: statusColor(selectedUser.status),
                    border: "2px solid #111f11",
                  }} />
                </div>
                <div>
                  <div style={{ fontSize: "15px", fontWeight: "600" }}>{selectedUser.name}</div>
                  <div style={{ fontSize: "11px", color: "#6b7280" }}>
                    ID: {selectedUser.id} · {selectedUser.status === "online" ? "Online" : selectedUser.lastSeen || selectedUser.status}
                  </div>
                </div>
              </div>

              <button
                onClick={isCallActive ? endCall : startCall}
                style={{
                  padding: "8px 16px",
                  borderRadius: "20px",
                  border: "none",
                  background: isCallActive
                    ? "linear-gradient(135deg, #ef4444, #dc2626)"
                    : "linear-gradient(135deg, #22c55e, #16a34a)",
                  color: "white",
                  fontWeight: "600",
                  fontSize: "13px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                {isCallActive ? `📵 End  ${formatCallTime(callTime)}` : "📞 Voice Call"}
              </button>
            </div>

            {isCallActive && (
              <div style={{
                background: "linear-gradient(135deg, #14532d, #166534)",
                padding: "10px 20px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "12px",
                fontSize: "14px",
                fontWeight: "500",
              }}>
                <span style={{ animation: "pulse 1s infinite" }}>🔴</span>
                <span>Call in progress with {selectedUser.name}</span>
                <span style={{ fontFamily: "monospace", fontSize: "16px", color: "#4ade80" }}>
                  {formatCallTime(callTime)}
                </span>
              </div>
            )}

            <div style={{
              flex: 1,
              overflowY: "auto",
              padding: "16px 20px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              backgroundImage: `radial-gradient(circle at 20% 50%, rgba(34,197,94,0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(59,130,246,0.03) 0%, transparent 50%)`,
            }}>
              {messages.length === 0 ? (
                <div style={{ textAlign: "center", color: "#374151", marginTop: "40px", fontSize: "13px" }}>
                  No messages yet. Start the conversation!
                </div>
              ) : (
                messages.map((msg) => (
                  <MessageBubble key={msg.id} msg={msg} isMe={msg.senderId === myId} />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div style={{
              padding: "12px 16px",
              background: "#111f11",
              borderTop: "1px solid #1a2e1a",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}>
              {isRecording ? (
                <div style={{
                  flex: 1, display: "flex", alignItems: "center", gap: "12px",
                  background: "#0a1a0a", borderRadius: "24px", padding: "10px 16px",
                  border: "1px solid #22c55e",
                }}>
                  <span style={{ color: "#ef4444", fontSize: "16px" }}>🔴</span>
                  <span style={{ color: "#4ade80", fontSize: "14px" }}>Recording... {recordingTime}s</span>
                  <div style={{ flex: 1, height: "2px", background: "#1a2e1a", borderRadius: "2px" }}>
                    <div style={{
                      height: "100%", background: "#22c55e", borderRadius: "2px",
                      width: `${Math.min(recordingTime * 3, 100)}%`,
                      transition: "width 1s linear",
                    }} />
                  </div>
                </div>
              ) : (
                <input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Type a message..."
                  style={{
                    flex: 1,
                    background: "#0a1a0a",
                    border: "1px solid #1a2e1a",
                    borderRadius: "24px",
                    padding: "10px 16px",
                    color: "#e8f5e9",
                    fontSize: "14px",
                    outline: "none",
                  }}
                />
              )}

              <button
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                onTouchStart={startRecording}
                onTouchEnd={stopRecording}
                style={{
                  width: "42px", height: "42px", borderRadius: "50%",
                  background: isRecording
                    ? "linear-gradient(135deg, #ef4444, #dc2626)"
                    : "linear-gradient(135deg, #374151, #1f2937)",
                  border: "none", cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "18px",
                }}
              >🎤</button>

              {!isRecording && (
                <button
                  onClick={sendMessage}
                  style={{
                    width: "42px", height: "42px", borderRadius: "50%",
                    background: inputText.trim()
                      ? "linear-gradient(135deg, #22c55e, #16a34a)"
                      : "linear-gradient(135deg, #374151, #1f2937)",
                    border: "none", cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "18px",
                    transition: "background 0.2s",
                  }}
                >➤</button>
              )}
            </div>
          </>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1a2e1a; border-radius: 4px; }
      `}</style>
    </div>
  );
}

function UserItem({ user, selected, onClick, statusColor }: {
  user: User;
  selected: boolean;
  onClick: () => void;
  statusColor: (s: string) => string;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: "10px 16px",
        display: "flex",
        alignItems: "center",
        gap: "12px",
        cursor: "pointer",
        background: selected ? "#0d2e0d" : "transparent",
        borderLeft: selected ? "3px solid #22c55e" : "3px solid transparent",
        transition: "all 0.15s",
      }}
      onMouseEnter={(e) => { if (!selected) (e.currentTarget as HTMLDivElement).style.background = "#0a1a0a"; }}
      onMouseLeave={(e) => { if (!selected) (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}
    >
      <div style={{ position: "relative", flexShrink: 0 }}>
        <div style={{
          width: "40px", height: "40px", borderRadius: "50%",
          background: user.role === "vendor"
            ? "linear-gradient(135deg, #22c55e, #16a34a)"
            : "linear-gradient(135deg, #3b82f6, #1d4ed8)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "12px", fontWeight: "700", color: "white",
        }}>{user.avatar}</div>
        <div style={{
          position: "absolute", bottom: 1, right: 1,
          width: "10px", height: "10px", borderRadius: "50%",
          background: statusColor(user.status),
          border: "2px solid #0d1a0d",
        }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: "14px", fontWeight: "500", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {user.name}
        </div>
        <div style={{ fontSize: "11px", color: "#4b5563" }}>ID: {user.id}</div>
      </div>
    </div>
  );
}

function MessageBubble({ msg, isMe }: { msg: Message; isMe: boolean }) {
  return (
    <div style={{
      display: "flex",
      justifyContent: isMe ? "flex-end" : "flex-start",
      marginBottom: "2px",
    }}>
      <div style={{
        maxWidth: "65%",
        background: isMe
          ? "linear-gradient(135deg, #166534, #14532d)"
          : "#1a2e1a",
        borderRadius: isMe ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        padding: "8px 12px",
        border: isMe ? "1px solid #22c55e22" : "1px solid #1f3d1f",
      }}>
        {msg.type === "voice" ? (
          <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: "140px" }}>
            <button style={{
              width: "30px", height: "30px", borderRadius: "50%",
              background: isMe ? "#22c55e" : "#3b82f6",
              border: "none", cursor: "pointer", color: "white", fontSize: "12px",
            }}>▶</button>
            <div style={{ flex: 1 }}>
              <div style={{ height: "2px", background: "#374151", borderRadius: "2px", marginBottom: "4px" }}>
                <div style={{ width: "0%", height: "100%", background: isMe ? "#22c55e" : "#3b82f6", borderRadius: "2px" }} />
              </div>
              <div style={{ fontSize: "11px", color: "#9ca3af" }}>🎤 {msg.duration}</div>
            </div>
          </div>
        ) : (
          <div style={{ fontSize: "14px", lineHeight: "1.4", color: "#e8f5e9" }}>{msg.text}</div>
        )}
        <div style={{
          display: "flex", justifyContent: "flex-end", alignItems: "center",
          gap: "4px", marginTop: "4px",
        }}>
          <span style={{ fontSize: "10px", color: "#4b5563" }}>{msg.timestamp}</span>
          {isMe && (
            <span style={{ fontSize: "11px", color: msg.status === "read" ? "#22c55e" : "#4b5563" }}>
              {msg.status === "read" ? "✓✓" : msg.status === "delivered" ? "✓✓" : "✓"}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}