import { forwardRef, useId, useState, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { Icon, type IconName } from "./Icon";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
  icon?: IconName;
}

export const Input = forwardRef<HTMLInputElement, FieldProps>(function Input(
  { label, error, hint, icon, type = "text", className = "", id, ...rest },
  ref,
) {
  const auto = useId();
  const fieldId = id ?? auto;
  const [shown, setShown] = useState(false);
  const isPassword = type === "password";
  return (
    <div className={className}>
      <label htmlFor={fieldId} className="mb-1.5 block text-sm font-semibold">
        {label}
      </label>
      <div className="relative">
        {icon && <Icon name={icon} size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink/40" />}
        <input
          ref={ref}
          id={fieldId}
          type={isPassword && shown ? "text" : type}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${fieldId}-err` : undefined}
          className={`field ${icon ? "pl-10" : ""} ${isPassword ? "pr-11" : ""} ${error ? "border-red-500" : ""}`}
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShown((s) => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/50 hover:text-ink"
            aria-label={shown ? "Hide password" : "Show password"}
          >
            <Icon name={shown ? "eyeOff" : "eye"} size={16} />
          </button>
        )}
      </div>
      {error ? (
        <p id={`${fieldId}-err`} className="mt-1 text-xs text-red-600">
          {error}
        </p>
      ) : (
        hint && <p className="mt-1 text-xs text-ink/55">{hint}</p>
      )}
    </div>
  );
});

interface AreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

export function TextArea({ label, error, className = "", id, ...rest }: AreaProps) {
  const auto = useId();
  const fieldId = id ?? auto;
  return (
    <div className={className}>
      <label htmlFor={fieldId} className="mb-1.5 block text-sm font-semibold">
        {label}
      </label>
      <textarea id={fieldId} rows={4} className={`field ${error ? "border-red-500" : ""}`} {...rest} />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
