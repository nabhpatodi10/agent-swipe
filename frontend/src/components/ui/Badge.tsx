import { cn } from "../../lib/utils";

type Variant = "default" | "accent" | "success" | "warning" | "danger" | "outline";

interface BadgeProps {
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
}

const variantStyles: Record<Variant, string> = {
  default: "bg-surface-300/60 text-text-secondary",
  accent: "bg-accent/15 text-accent-light border border-accent/20",
  success: "bg-success/15 text-success border border-success/20",
  warning: "bg-warning/15 text-warning border border-warning/20",
  danger: "bg-danger/15 text-danger border border-danger/20",
  outline: "bg-transparent text-text-secondary border border-border",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-lg text-xs font-medium",
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
