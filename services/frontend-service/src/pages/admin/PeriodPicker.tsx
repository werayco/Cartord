import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";

/** The statistics endpoints take a free-form `period` query (default "all"); valid values are defined by the backend. */
export function PeriodPicker({ value, onApply }: { value: string; onApply: (v: string) => void }) {
  const [draft, setDraft] = useState(value);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    onApply(draft.trim() || "all");
  };
  return (
    <form onSubmit={submit} className="flex items-center gap-2">
      <label htmlFor="period" className="text-sm font-semibold">Period</label>
      <input id="period" value={draft} onChange={(e) => setDraft(e.target.value)} className="field w-32 py-1.5" placeholder="all" />
      <Button type="submit" size="sm" variant="outline">Apply</Button>
    </form>
  );
}
