declare global {
  interface Window {
    __CARTORD_CONFIG__?: Record<string, string>;
  }
}

const runtime = window.__CARTORD_CONFIG__ ?? {};
const buildTime = import.meta.env as unknown as Record<string, string | undefined>;

function pick(key: string, fallback: string): string {
  const value = runtime[key] || buildTime[key];
  return (value && value.length > 0 ? value : fallback).replace(/\/+$/, "");
}

const aiUrl = pick("VITE_AI_SERVICE_URL", "http://localhost:9000");

export const config = {
  services: {
    auth: pick("VITE_AUTH_SERVICE_URL", "http://localhost:9001"),
    inventory: pick("VITE_INVENTORY_SERVICE_URL", "http://localhost:9002"),
    order: pick("VITE_ORDER_SERVICE_URL", "http://localhost:9004"),
    payment: pick("VITE_PAYMENT_SERVICE_URL", "http://localhost:9005"),
    search: pick("VITE_SEARCH_SERVICE_URL", "http://localhost:9007"),
    ai: aiUrl,
  },
  aiWsUrl: pick("VITE_AI_WS_URL", `${aiUrl.replace(/^http/, "ws")}/api/v1/ws/chat`),
  aiWsMessageField: runtime.VITE_AI_WS_MESSAGE_FIELD || buildTime.VITE_AI_WS_MESSAGE_FIELD || "content",
  currency: runtime.VITE_CURRENCY || buildTime.VITE_CURRENCY || "NGN",
};

export type ServiceName = keyof typeof config.services;
