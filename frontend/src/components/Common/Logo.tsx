import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const content = (
    <span
      className={cn(
        "font-semibold text-foreground",
        variant === "icon" ? "text-sm" : "text-lg",
        variant === "responsive" && "text-lg group-data-[collapsible=icon]:text-sm",
        className,
      )}
    >
      {variant === "icon" ? "AJ" : variant === "responsive" ? (
        <>
          <span className="group-data-[collapsible=icon]:hidden">Alignment Journal</span>
          <span className="hidden group-data-[collapsible=icon]:inline">AJ</span>
        </>
      ) : "Alignment Journal"}
    </span>
  )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
