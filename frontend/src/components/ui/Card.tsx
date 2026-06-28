import clsx from "clsx";
import { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

export function Card({ className, elevated, children, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        "rounded-xl border border-mobius-border p-5",
        elevated ? "bg-mobius-elevated" : "bg-mobius-surface",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={clsx("text-sm font-semibold text-mobius-muted uppercase tracking-wide mb-3", className)} {...props}>
      {children}
    </h3>
  );
}
