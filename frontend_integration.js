// ─────────────────────────────────────────────────────────────────────────────
// chatbot.js — drop this logic into your Lovable frontend
// Replace BACKEND_URL with your Railway public URL after deployment
// ─────────────────────────────────────────────────────────────────────────────

const BACKEND_URL = "https://your-backend.railway.app"; // ← update this

// Conversation history kept in memory for the session
let conversationHistory = [];

/**
 * Sends a user message to the backend and returns the AI reply.
 * @param {string} userMessage
 * @returns {Promise<string>} the AI reply text
 */
async function sendMessage(userMessage) {
  // Append the new user message to history
  conversationHistory.push({ role: "user", content: userMessage });

  const response = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: conversationHistory }),
  });

  if (response.status === 429) {
    throw new Error("Too many messages! Please wait a moment before continuing.");
  }

  if (!response.ok) {
    throw new Error("The chatbot is temporarily unavailable. Please try again later.");
  }

  const data = await response.json();
  const reply = data.reply;

  // Append the AI reply to history so context is preserved
  conversationHistory.push({ role: "model", content: reply });

  return reply;
}

/**
 * Clears the conversation history (e.g. on a "New conversation" button click)
 */
function resetConversation() {
  conversationHistory = [];
}

// ── Example usage in a React component ────────────────────────────────────────
//
// import { useState } from "react";
//
// export default function Chatbot() {
//   const [messages, setMessages] = useState([]);
//   const [input, setInput]       = useState("");
//   const [loading, setLoading]   = useState(false);
//   const [error, setError]       = useState(null);
//
//   async function handleSend() {
//     if (!input.trim()) return;
//     const userText = input;
//     setInput("");
//     setMessages(prev => [...prev, { role: "user", text: userText }]);
//     setLoading(true);
//     setError(null);
//     try {
//       const reply = await sendMessage(userText);
//       setMessages(prev => [...prev, { role: "model", text: reply }]);
//     } catch (err) {
//       setError(err.message);
//     } finally {
//       setLoading(false);
//     }
//   }
//
//   return (
//     <div>
//       {messages.map((m, i) => <p key={i}><b>{m.role}:</b> {m.text}</p>)}
//       {error && <p style={{ color: "red" }}>{error}</p>}
//       {loading && <p>Thinking…</p>}
//       <input value={input} onChange={e => setInput(e.target.value)} />
//       <button onClick={handleSend}>Send</button>
//     </div>
//   );
// }
