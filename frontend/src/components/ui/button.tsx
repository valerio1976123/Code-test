import * as React from "react";
import { cn } from "../../lib/utils";

type Variant = "default" | "secondary" | "destructive" | "ghost";
type Size = "sm" | "md";

const variantClasses: Record<Variant, string> = {
  default:
    "bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-400",
  secondary:
    "bg-slate-100 text-slate-900 hover:bg-slate-200 disabled:bg-slate-100",
  destructive:
    "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
  ghost: "bg-transparent hover:bg-slate-100 text-slate-900",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
};

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
};

export function Button({
  className,
  variant = "default",
  size = "md",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-70",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    />
  );
}

