import { request } from "./http";

export interface OrderResult {
  order_id: string;
  quantity: number;
  unit_price: number;
  status: string;
}

export interface OrderSummary {
  message: string;
  status: string;
}

export const ordersApi = {
  place: (idempotencyKey: string, sku: string, quantity: number) =>
    request<OrderResult[]>("order", `/api/v1/order/place/${encodeURIComponent(idempotencyKey)}`, {
      method: "POST",
      body: [{ sku, quantity }],
    }),
  summary: (signal?: AbortSignal) =>
    request<OrderSummary>("order", "/api/v1/order/summary", { signal }),
  adminStatistics: (period: string) =>
    request("order", "/api/v1/order/admin/statistics", { query: { period } }),
  adminFailedStatistics: (period: string) =>
    request("order", "/api/v1/order/admin/failed-statistics", { query: { period } }),
};
