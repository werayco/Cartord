import { request } from "./http";
import { toProducts, type Product, type ProductImage } from "./types";

const base = "/api/v1/inventory/";

interface ProductImageUploadIntent {
  image_id: string;
  object_key: string;
  upload_url: string;
  content_type: string;
}

interface InventoryCreateResponse {
  message: string;
  sku: string;
}

const createPayload = (p: Product) => ({
  name: p.name,
  description: p.description,
  unit_price: p.unit_price,
  available_quantity: p.available_quantity,
  reserved_quantity: p.reserved_quantity,
});

const updatePayload = (p: Product) => ({ ...createPayload(p), sku: p.sku });

export const inventoryApi = {
  async list(signal?: AbortSignal): Promise<Product[]> {
    return toProducts(await request("inventory", base, { signal }));
  },
  create: (p: Product) =>
    request<InventoryCreateResponse>("inventory", base, { method: "POST", body: createPayload(p) }),
  update: (p: Product) => request("inventory", base, { method: "PUT", body: updatePayload(p) }),
  remove: (p: Product) => request("inventory", base, { method: "DELETE", body: updatePayload(p) }),
  createImageUpload: (sku: string, file: File, altText?: string) =>
    request<ProductImageUploadIntent>(
      "inventory",
      `${base}${encodeURIComponent(sku)}/images/upload-url`,
      {
        method: "POST",
        body: { content_type: file.type, file_size: file.size, alt_text: altText },
      },
    ),
  completeImageUpload: (sku: string, imageId: string) =>
    request<ProductImage>(
      "inventory",
      `${base}${encodeURIComponent(sku)}/images/complete`,
      { method: "POST", body: { image_id: imageId } },
    ),
  deleteImage: (sku: string, imageId: string) =>
    request(
      "inventory",
      `${base}${encodeURIComponent(sku)}/images/${encodeURIComponent(imageId)}`,
      { method: "DELETE" },
    ),

  adminSummary: () => request("inventory", `${base}admin/summary`),
  async adminLowStock(): Promise<Product[]> {
    return toProducts(await request("inventory", `${base}admin/low-stock`));
  },
  async adminOutOfStock(): Promise<Product[]> {
    return toProducts(await request("inventory", `${base}admin/out-of-stock`));
  },
};
