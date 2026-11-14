import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { inventoryApi } from "../../api/inventory";
import { errorMessage } from "../../api/http";
import { useAsync } from "../../hooks/useAsync";
import { Button, LinkButton } from "../../components/ui/Button";
import { Input, TextArea } from "../../components/ui/Input";
import { PageHeader } from "../../components/ui/StatCard";
import { ErrorState, GapNotice, InlineError, Skeleton } from "../../components/ui/feedback";
import { hasErrors, positiveNumber, required, type Errors } from "../../lib/validate";

const MAX_IMAGE_COUNT = 5;
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export default function ProductForm() {
  const { sku: skuParam } = useParams();
  const editing = Boolean(skuParam);
  const navigate = useNavigate();

  const existing = useAsync((s) => inventoryApi.list(s), [skuParam], editing);
  const current = existing.data?.find((p) => p.sku === skuParam);

  const [form, setForm] = useState({ name: "", description: "", unit_price: "", sku: "", available_quantity: "0" });
  const [errors, setErrors] = useState<Errors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [images, setImages] = useState<File[]>([]);
  const [imageError, setImageError] = useState<string | null>(null);
  const [deletingImageId, setDeletingImageId] = useState<string | null>(null);

  useEffect(() => {
    if (current) {
      setForm({
        name: current.name,
        description: current.description,
        unit_price: String(current.unit_price),
        sku: current.sku,
        available_quantity: String(current.available_quantity),
      });
    }
  }, [current]);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const uploadImage = async (sku: string, file: File) => {
    let imageId: string | null = null;
    try {
      const intent = await inventoryApi.createImageUpload(sku, file, form.name.trim());
      imageId = intent.image_id;
      const response = await fetch(intent.upload_url, {
        method: "PUT",
        headers: { "Content-Type": intent.content_type },
        body: file,
      });
      if (!response.ok) {
        throw new Error(`Image upload failed (${response.status}).`);
      }
      await inventoryApi.completeImageUpload(sku, intent.image_id);
    } catch (error) {
      if (imageId) {
        try {
          await inventoryApi.deleteImage(sku, imageId);
        } catch (cleanupError) {
          console.error("Could not clean up an incomplete product image upload.", cleanupError);
        }
      }
      throw error;
    }
  };

  const removeImage = async (imageId: string) => {
    if (!current) return;
    setDeletingImageId(imageId);
    setImageError(null);
    try {
      await inventoryApi.deleteImage(current.sku, imageId);
      if (editing) existing.reload();
    } catch (error) {
      setImageError(errorMessage(error));
    } finally {
      setDeletingImageId(null);
    }
  };

  const selectImages = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(event.target.files ?? []);
    event.target.value = "";
    const existingCount = current?.images.length ?? 0;
    if (existingCount + images.length + selected.length > MAX_IMAGE_COUNT) {
      setImageError(`A product can have at most ${MAX_IMAGE_COUNT} images.`);
      return;
    }
    const invalid = selected.find((file) => !IMAGE_TYPES.has(file.type) || file.size === 0 || file.size > MAX_IMAGE_SIZE);
    if (invalid) {
      setImageError(`${invalid.name} must be a non-empty JPEG, PNG, or WebP image no larger than 5 MB.`);
      return;
    }
    setImageError(null);
    setImages((currentImages) => [...currentImages, ...selected]);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next: Errors = {
      name: required(form.name, "Product name"),
      description: required(form.description, "Description"),
      sku: editing ? required(form.sku, "SKU") : undefined,
      unit_price: positiveNumber(form.unit_price, "Price"),
      available_quantity: positiveNumber(form.available_quantity, "Stock"),
    };
    setErrors(next);
    if (hasErrors(next)) return;
    setBusy(true);
    setApiError(null);
    setImageError(null);
    const product = {
      name: form.name.trim(),
      description: form.description.trim(),
      sku: form.sku.trim(),
      unit_price: Number(form.unit_price),
      available_quantity: Math.floor(Number(form.available_quantity)),
      reserved_quantity: current?.reserved_quantity ?? 0,
      images: current?.images ?? [],
    };
    try {
      const sku = editing ? product.sku : (await inventoryApi.create(product)).sku;
      if (editing) {
        await inventoryApi.update(product);
      } else {
        setForm((currentForm) => ({ ...currentForm, sku }));
        navigate(`/seller/products/${encodeURIComponent(sku)}/edit`, { replace: true });
      }
      for (const image of images) {
        await uploadImage(sku, image);
        setImages((currentImages) => currentImages.filter((item) => item !== image));
      }
      navigate("/seller/products", { replace: true });
    } catch (err) {
      setApiError(errorMessage(err));
      existing.reload();
    } finally {
      setBusy(false);
    }
  };

  if (editing && existing.loading) return <Skeleton className="h-96 max-w-2xl" />;
  if (editing && existing.error) return <ErrorState message={existing.error} onRetry={existing.reload} />;
  if (editing && !current) return <ErrorState message="We couldn't find that product in your catalogue." />;

  return (
    <>
      <PageHeader title={editing ? "Edit product" : "Add product"} subtitle={editing ? current?.name : "Create a new listing."} />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,40rem)_1fr]">
        <form onSubmit={submit} className="card space-y-4 p-6" noValidate>
          <Input label="Product name" value={form.name} onChange={set("name")} error={errors.name} />
          <TextArea label="Description" value={form.description} onChange={set("description")} error={errors.description} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Price" type="number" min="0" step="0.01" inputMode="decimal" value={form.unit_price} onChange={set("unit_price")} error={errors.unit_price} />
            <Input label="Available stock" type="number" min="0" step="1" inputMode="numeric" value={form.available_quantity} onChange={set("available_quantity")} error={errors.available_quantity} />
          </div>
          {editing ? (
            <Input label="SKU" value={form.sku} onChange={set("sku")} error={errors.sku} disabled hint="The SKU identifies the product and can't be changed." />
          ) : (
            <p className="text-sm text-ink/55">The inventory service will assign a SKU when this product is created.</p>
          )}
          <div className="space-y-3">
            <label className="block text-sm font-semibold" htmlFor="product-images">Product images</label>
            <input
              id="product-images"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              onChange={selectImages}
              disabled={busy || Boolean(deletingImageId)}
              className="block w-full text-sm text-ink/70 file:mr-3 file:rounded-full file:border-0 file:bg-brand-50 file:px-4 file:py-2 file:font-semibold file:text-brand-700 hover:file:bg-brand-100"
            />
            <p className="text-xs text-ink/55">JPEG, PNG, or WebP; up to 5 MB each and 5 images per product.</p>
            {current?.images.map((image) => (
              <div key={image.id} className="flex items-center gap-3 rounded-xl border border-ink/10 p-2">
                <img src={image.url} alt={image.alt_text || current.name} className="h-14 w-14 rounded-lg object-cover" />
                <span className="min-w-0 flex-1 truncate text-sm">{image.alt_text || current.name}</span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  loading={deletingImageId === image.id}
                  disabled={busy || Boolean(deletingImageId)}
                  onClick={() => removeImage(image.id)}
                >
                  Remove
                </Button>
              </div>
            ))}
            {images.map((image, index) => (
              <div key={`${image.name}-${image.lastModified}-${index}`} className="flex items-center gap-3 text-sm text-ink/70">
                <span className="min-w-0 flex-1 truncate">{image.name}</span>
                <button type="button" className="font-semibold text-red-600 hover:underline" onClick={() => setImages((currentImages) => currentImages.filter((_, itemIndex) => itemIndex !== index))}>
                  Remove
                </button>
              </div>
            ))}
            <InlineError message={imageError} />
          </div>
          <InlineError message={apiError} />
          <div className="flex gap-2">
            <Button type="submit" loading={busy}>{editing ? "Save changes" : "Create product"}</Button>
            <LinkButton to="/seller/products" variant="outline">Cancel</LinkButton>
          </div>
        </form>
        <GapNotice title="Listing details">
          Product images are stored with the listing. Categories, custom attributes and a draft or published status are not currently supported.
        </GapNotice>
      </div>
    </>
  );
}
