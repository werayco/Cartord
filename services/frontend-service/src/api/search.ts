import { request } from "./http";
import { toProducts, type Product } from "./types";

export const searchApi = {
  async items(query: string, signal?: AbortSignal): Promise<Product[]> {
    return toProducts(await request("search", "/api/v1/search/items", { query: { query }, signal }));
  },
  async all(signal?: AbortSignal): Promise<Product[]> {
    return toProducts(await request("search", "/api/v1/search/items/all", { signal }));
  },
};
