import clsx from "clsx";
import { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ className, label, error, id, ...props }: InputProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-mobius-muted">
          {label}
        </label>
      )}
      <input
        id={id}
        className={clsx(
          "w-full rounded-lg border border-mobius-border bg-mobius-surface px-4 py-2.5",
          "text-mobius-text placeholder:text-mobius-muted",
          "focus:border-mobius-accent focus:outline-none focus:ring-1 focus:ring-mobius-accent",
          error && "border-mobius-error",
          className
        )}
        {...props}
      />
      {error && <p className="text-sm text-mobius-error">{error}</p>}
    </div>
  );
}
