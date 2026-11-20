import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";
import { ChatSocket, type ChatCard, type ChatStatus, type IncomingChat } from "../../api/ai";
import { tokenStore } from "../../api/tokenStore";
import type { Product } from "../../api/types";
import { useAuth } from "../../context/AuthContext";
import { usePersisted } from "../../hooks/usePersisted";
import { ProductCard } from "../../components/ProductCard";
import { Logo } from "../../components/Logo";
import { Icon } from "../../components/ui/Icon";
import { AssistantCards, AssistantMarkdown } from "../../components/chat/AssistantContent";
import { ThoughtTicker } from "../../components/chat/ThoughtTicker";
import { homeFor } from "../../lib/routes";
import { uid } from "../../lib/uid";

interface Message {
  id: string;
  from: "user" | "assistant";
  text: string;
  products?: Product[];
  cards?: ChatCard[];
  error?: boolean;
  thoughts?: string[];
  isThinking?: boolean;
  thoughtTickerVisible?: boolean;
}
interface Conversation {
  id: string;
  serverId?: string;
  title: string;
  updatedAt: number;
  messages: Message[];
}

interface PendingMessage {
  conversationId: string;
  messageId: string;
}

const WAIT_MS = 60_000;
const newConversation = (): Conversation => ({ id: uid(), title: "New chat", updatedAt: Date.now(), messages: [] });

export default function ChatPage() {
  const { user, role } = useAuth();
  /* No conversation-history endpoint exists, so chats are stored in this browser (see README gaps). */
  const [chats, setChats] = usePersisted<Conversation[]>(user ? `cartord.${user.username}.chats` : null, []);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState<ChatStatus>("connecting");
  const [waiting, setWaiting] = useState(false);
  const [sidebar, setSidebar] = useState(false);
  const socket = useRef<ChatSocket | null>(null);
  const activeRef = useRef<string | null>(null);
  const pendingRef = useRef<PendingMessage | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const bottom = useRef<HTMLDivElement>(null);

  const active = useMemo(() => chats.find((c) => c.id === activeId) ?? null, [chats, activeId]);
  const lastMessageId = active?.messages[active.messages.length - 1]?.id;
  const activePending = pendingRef.current;
  const pendingAssistantMessage =
    active && activePending?.conversationId === active.id
      ? active.messages.find((message) => message.id === `assistant-${activePending.messageId}`)
      : undefined;
  const latestThought =
    pendingAssistantMessage?.thoughts?.[pendingAssistantMessage.thoughts.length - 1] ?? "";
  activeRef.current = activeId;

  const append = useCallback(
    (id: string, msg: Message) =>
      setChats((all) =>
        all
          .map((c) => (c.id === id ? { ...c, updatedAt: Date.now(), messages: [...c.messages, msg] } : c))
          .sort((a, b) => b.updatedAt - a.updatedAt),
      ),
    [setChats],
  );

  const updateAssistantMessage = useCallback(
    (conversationId: string, messageId: string, update: (message: Message) => Message) =>
      setChats((all) =>
        all
          .map((chat) => {
            if (chat.id !== conversationId) return chat;
            const assistantId = `assistant-${messageId}`;
            const existing = chat.messages.find((message) => message.id === assistantId);
            const current = existing ?? {
              id: assistantId,
              from: "assistant" as const,
              text: "",
              thoughts: [],
            };
            const updated = update(current);
            return {
              ...chat,
              updatedAt: Date.now(),
              messages: existing
                ? chat.messages.map((message) => (message.id === assistantId ? updated : message))
                : [...chat.messages, updated],
            };
          })
          .sort((a, b) => b.updatedAt - a.updatedAt),
      ),
    [setChats],
  );

  const appendCard = useCallback(
    (conversationId: string, messageId: string, card: ChatCard) =>
      updateAssistantMessage(conversationId, messageId, (message) => ({
        ...message,
        cards: [...(message.cards ?? []), card],
        isThinking: false,
      })),
    [updateAssistantMessage],
  );

  const appendToken = useCallback(
    (conversationId: string, messageId: string, delta: string) =>
      updateAssistantMessage(conversationId, messageId, (message) => ({
        ...message,
        text: message.text + delta,
        isThinking: false,
      })),
    [updateAssistantMessage],
  );

  const appendThought = useCallback(
    (conversationId: string, messageId: string, thought: string) =>
      updateAssistantMessage(conversationId, messageId, (message) => ({
        ...message,
        thoughts:
          message.text || message.isThinking === false
            ? message.thoughts ?? []
            : [...(message.thoughts ?? []), thought],
        isThinking: !message.text && message.isThinking !== false,
        thoughtTickerVisible: !message.text && message.isThinking !== false,
      })),
    [updateAssistantMessage],
  );

  const finishAssistantMessage = useCallback(
    (
      conversationId: string,
      messageId: string,
      response?: { text?: string; products?: Product[]; card?: ChatCard; cards?: ChatCard[]; error?: boolean },
    ) =>
      updateAssistantMessage(conversationId, messageId, (message) => ({
        ...message,
        text:
          response?.text && message.text
            ? `${message.text}\n\n${response.text}`
            : response?.text || message.text,
        products: response?.products ?? message.products,
        cards: response?.cards?.length
          ? [...(message.cards ?? []), ...response.cards]
          : response?.card
            ? [...(message.cards ?? []), response.card]
            : message.cards,
        error: response?.error ?? message.error,
        isThinking: false,
      })),
    [updateAssistantMessage],
  );

  const clearThoughtTicker = useCallback(
    (conversationId: string, messageId: string) =>
      setChats((all) =>
        all.map((chat) =>
          chat.id !== conversationId
            ? chat
            : {
                ...chat,
                messages: chat.messages.map((message) =>
                  message.id === `assistant-${messageId}`
                    ? { ...message, thoughts: [], thoughtTickerVisible: false }
                    : message,
                ),
              },
        ),
      ),
    [setChats],
  );

  const onMessage = useCallback(
    (m: IncomingChat) => {
      // Replies belong to the chat the question was asked in, even if the user switched chats meanwhile.
      const pending = pendingRef.current;
      const id = pending?.conversationId ?? activeRef.current;

      if (m.type === "title") {
        if (m.title) {
          const title = m.title;
          setChats((all) =>
            all.map((chat) =>
              (m.conversationId && chat.serverId === m.conversationId) ||
              chat.id === pending?.conversationId
                ? { ...chat, title }
                : chat,
            ),
          );
        }
        return;
      }

      if (m.type === "ack") {
        if (id && m.conversationId) {
          setChats((all) =>
            all.map((chat) => (chat.id === id ? { ...chat, serverId: m.conversationId } : chat)),
          );
        }
        return;
      }

      if (m.type === "thought") {
        if (id && m.text) {
          appendThought(id, m.messageId ?? pending?.messageId ?? uid(), m.text);
        }
        return;
      }

      if (m.type === "token") {
        if (id && m.text) appendToken(id, m.messageId ?? pending?.messageId ?? uid(), m.text);
        return;
      }

      if (m.type === "card") {
        if (id && m.card) appendCard(id, m.messageId ?? pending?.messageId ?? uid(), m.card);
        return;
      }

      window.clearTimeout(timer.current);
      setWaiting(false);
      if (m.type === "done") {
        if (id && pending?.messageId) finishAssistantMessage(id, pending.messageId);
        pendingRef.current = null;
        return;
      }

      const incomingCards = m.cards?.length ? m.cards : m.card ? [m.card] : [];
      if (id && (m.text || m.products.length > 0 || incomingCards.length > 0)) {
        const assistantMessageId = m.messageId ?? pending?.messageId;
        if (assistantMessageId) {
          finishAssistantMessage(id, assistantMessageId, {
            text: m.text,
            products: m.products,
            cards: incomingCards,
            error: m.type === "error",
          });
        } else {
          append(id, {
            id: uid(),
            from: "assistant",
            text: m.text,
            products: m.products,
            cards: incomingCards,
            error: m.type === "error",
          });
        }
      }
      pendingRef.current = null;
    },
    [append, appendCard, appendThought, appendToken, finishAssistantMessage, setChats],
  );

  useEffect(() => {
    const token = tokenStore.get().access;
    if (!token) return;
    const s = new ChatSocket(token, { onStatus: setStatus, onMessage });
    socket.current = s;
    s.connect();
    return () => {
      window.clearTimeout(timer.current);
      s.close();
    };
  }, [onMessage]);

  useEffect(() => {
    if (!activeId && chats.length > 0) setActiveId(chats[0].id);
  }, [chats, activeId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [active?.messages.length, latestThought, pendingAssistantMessage?.text, waiting]);

  const startNew = () => {
    const c = newConversation();
    setChats((all) => [c, ...all]);
    setActiveId(c.id);
    setSidebar(false);
  };

  const deliver = (text: string) => {
    if (!text || waiting) return;
    let id = activeId;
    if (!id) {
      const c = newConversation();
      setChats((all) => [c, ...all]);
      setActiveId(c.id);
      activeRef.current = c.id;
      id = c.id;
    }
    const convId = id;
    setChats((all) => all.map((c) => (c.id === convId && c.messages.length === 0 ? { ...c, title: text.slice(0, 40) } : c)));
    const messageId = uid();
    append(convId, { id: messageId, from: "user", text });
    const serverId = chats.find((chat) => chat.id === convId)?.serverId;
    pendingRef.current = { conversationId: convId, messageId };
    if (socket.current?.send(text, messageId, serverId)) {
      updateAssistantMessage(convId, messageId, (message) => ({
        ...message,
        thoughts: [],
        isThinking: true,
        thoughtTickerVisible: true,
      }));
      setWaiting(true);
      timer.current = window.setTimeout(() => {
        setWaiting(false);
        pendingRef.current = null;
        finishAssistantMessage(convId, messageId, {
          text: "The assistant took too long to reply. Try sending your message again.",
          error: true,
        });
      }, WAIT_MS);
    } else {
      pendingRef.current = null;
      append(convId, { id: uid(), from: "assistant", text: "You're not connected to the assistant right now. Reconnecting; send your message again in a moment.", error: true });
    }
  };

  const send = (e?: FormEvent) => {
    e?.preventDefault();
    const text = draft.trim();
    if (!text || waiting) return;
    setDraft("");
    deliver(text);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const deleteChat = (id: string) => {
    setChats((all) => all.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(null);
  };

  const statusLabel = status === "open" ? "Online" : status === "connecting" ? "Connecting…" : "Reconnecting…";

  const list = (
    <div className="flex h-full flex-col bg-ink-800 text-white/80">
      <div className="p-4"><Logo to={homeFor(role)} dark /></div>
      <div className="px-3">
        <button onClick={startNew} className="flex w-full items-center gap-2 rounded-xl bg-lime-400 px-3 py-2.5 text-sm font-bold text-ink hover:bg-lime-300">
          <Icon name="plus" size={16} /> New chat
        </button>
      </div>
      <p className="mt-5 px-4 text-xs font-semibold text-white/50">Chats</p>
      <ul className="mt-2 flex-1 space-y-1 overflow-y-auto px-3 pb-3">
        {chats.length === 0 && <li className="px-2 py-2 text-sm text-white/50">Your conversations will appear here.</li>}
        {chats.map((c) => (
          <li key={c.id} className="group flex items-center">
            <button onClick={() => { setActiveId(c.id); setSidebar(false); }} className={`min-w-0 flex-1 truncate rounded-xl px-3 py-2 text-left text-sm ${c.id === activeId ? "bg-white/15 text-white" : "hover:bg-white/10"}`}>
              {c.title}
            </button>
            <button onClick={() => deleteChat(c.id)} className="ml-1 rounded-full p-1.5 text-white/40 opacity-0 hover:text-white focus:opacity-100 group-hover:opacity-100" aria-label={`Delete chat ${c.title}`}>
              <Icon name="trash" size={14} />
            </button>
          </li>
        ))}
      </ul>
      <Link to={homeFor(role)} className="flex items-center gap-2 border-t border-white/10 px-4 py-3 text-sm hover:text-white">
        <Icon name="layout" size={16} /> Back to dashboard
      </Link>
    </div>
  );

  return (
    <div className="flex h-screen">
      <aside className="hidden w-72 shrink-0 lg:block">{list}</aside>
      {sidebar && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-ink/50" onClick={() => setSidebar(false)} />
          <div className="absolute inset-y-0 left-0 w-72">{list}</div>
        </div>
      )}

      <section className="flex min-w-0 flex-1 flex-col bg-white">
        <header className="flex items-center gap-3 border-b border-ink/5 px-4 py-3">
          <button className="rounded-full p-2 hover:bg-ink/5 lg:hidden" onClick={() => setSidebar(true)} aria-label="Open chats"><Icon name="menu" size={20} /></button>
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-white"><Icon name="star" size={16} /></span>
          <div>
            <p className="text-sm font-bold">Cartord assistant</p>
            <p className="flex items-center gap-1.5 text-xs text-ink/60">
              <span className={`h-2 w-2 rounded-full ${status === "open" ? "bg-brand-500" : "bg-amber-500"}`} /> {statusLabel}
            </p>
          </div>
        </header>

        <div className="flex-1 space-y-5 overflow-y-auto bg-cream px-4 py-6 sm:px-8" aria-live="polite">
          {(!active || active.messages.length === 0) && (
            <div className="mx-auto mt-10 max-w-md text-center">
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-brand-700"><Icon name="chat" size={26} /></span>
              <h2 className="mt-4 text-xl font-extrabold">How can I help you shop?</h2>
              <p className="mt-1 text-sm text-ink/60">Ask about products, compare options, or get answers about orders and returns.</p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {["Show me products under ₦50,000", "How do I return an item?", "Recommend a gift for a photographer"].map((s) => (
                  <button key={s} onClick={() => setDraft(s)} className="rounded-full border border-ink/10 bg-white px-3 py-1.5 text-sm hover:border-brand-400">{s}</button>
                ))}
              </div>
            </div>
          )}
          {active?.messages.map((m) => (
            <div key={m.id} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] space-y-3 sm:max-w-[70%]`}>
                {m.thoughtTickerVisible && active && (
                  <ThoughtTicker
                    active={Boolean(m.isThinking)}
                    thoughts={m.thoughts ?? []}
                    onExited={() => clearThoughtTicker(active.id, m.id.slice("assistant-".length))}
                  />
                )}
                {m.text && m.from === "assistant" && !m.error ? (
                  <AssistantMarkdown text={m.text} />
                ) : m.text ? (
                  <p className={`whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${m.from === "user" ? "rounded-br-sm bg-brand-600 text-white" : "rounded-bl-sm bg-red-50 text-red-700"}`}>
                    {m.text}
                  </p>
                ) : null}
                {m.cards && m.cards.length > 0 && (
                  <AssistantCards
                    cards={m.cards}
                    onChoose={
                      m.id === lastMessageId && !waiting && status === "open"
                        ? deliver
                        : undefined
                    }
                  />
                )}
                {m.products && m.products.length > 0 && (
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {m.products.map((p) => <ProductCard key={p.sku || p.name} product={p} compact />)}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottom} />
        </div>

        <form onSubmit={send} className="flex items-end gap-2 border-t border-ink/5 bg-white p-3 sm:p-4">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKey}
            rows={1}
            aria-label="Message"
            placeholder="Type a message…"
            className="field max-h-32 min-h-[2.75rem] flex-1 resize-none rounded-2xl"
          />
          <button type="submit" disabled={!draft.trim() || waiting || status !== "open"} className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-600 text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Send message">
            <Icon name="send" size={18} />
          </button>
        </form>
      </section>
    </div>
  );
}
