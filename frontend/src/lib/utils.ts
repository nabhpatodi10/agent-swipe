import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function truncate(str: string, max: number): string {
  if (str.length <= max) return str;
  return str.slice(0, max - 3) + "...";
}

export function pricingLabel(model: string): string {
  switch (model) {
    case "free":
      return "Free";
    case "freemium":
      return "Freemium";
    case "paid":
      return "Paid";
    default:
      return model;
  }
}

export function categoryColor(category: string): string {
  const colors: Record<string, string> = {
    productivity: "from-amber-700 to-yellow-600",
    coding: "from-brown to-amber-800",
    writing: "from-orange-700 to-red-800",
    research: "from-yellow-700 to-amber-600",
    design: "from-accent to-orange-600",
    data: "from-stone-600 to-amber-700",
    marketing: "from-rose-700 to-orange-700",
    support: "from-yellow-800 to-amber-700",
  };
  return colors[category.toLowerCase()] ?? "from-accent to-brown";
}
