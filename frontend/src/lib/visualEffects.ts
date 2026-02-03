/**
 * Advanced Visual Effects
 * Glass morphism, gradients, glows, and modern UI effects
 */

/**
 * Glass morphism effects
 */
export const glass = {
  default: "backdrop-blur-md bg-white/70 dark:bg-gray-900/70 border border-white/20",
  strong: "backdrop-blur-lg bg-white/80 dark:bg-gray-900/80 border border-white/30",
  subtle: "backdrop-blur-sm bg-white/50 dark:bg-gray-900/50 border border-white/10",
  card: "backdrop-blur-md bg-white/60 dark:bg-gray-900/60 border border-white/20 shadow-xl",
};

/**
 * Gradient backgrounds
 */
export const gradients = {
  primary: "bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600",
  secondary: "bg-gradient-to-br from-purple-500 via-purple-600 to-pink-600",
  success: "bg-gradient-to-br from-green-500 via-emerald-600 to-teal-600",
  warning: "bg-gradient-to-br from-orange-500 via-amber-600 to-yellow-600",
  danger: "bg-gradient-to-br from-red-500 via-rose-600 to-pink-600",

  // Subtle gradients
  subtlePrimary: "bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-blue-950 dark:via-indigo-950 dark:to-purple-950",
  subtleSecondary: "bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-purple-950 dark:via-pink-950 dark:to-rose-950",

  // Mesh gradients
  mesh: "bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 opacity-20",
  meshDark: "bg-gradient-to-br from-blue-600 via-purple-700 to-pink-700 opacity-10",

  // Animated gradients
  animated: "bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 bg-[length:200%_100%] animate-gradient",
  shimmer: "bg-gradient-to-r from-transparent via-white/20 to-transparent bg-[length:200%_100%]",
};

/**
 * Glow effects
 */
export const glows = {
  blue: "shadow-[0_0_30px_rgba(59,130,246,0.3)]",
  green: "shadow-[0_0_30px_rgba(34,197,94,0.3)]",
  purple: "shadow-[0_0_30px_rgba(168,85,247,0.3)]",
  orange: "shadow-[0_0_30px_rgba(249,115,22,0.3)]",

  strong: {
    blue: "shadow-[0_0_50px_rgba(59,130,246,0.5)]",
    green: "shadow-[0_0_50px_rgba(34,197,94,0.5)]",
    purple: "shadow-[0_0_50px_rgba(168,85,247,0.5)]",
    orange: "shadow-[0_0_50px_rgba(249,115,22,0.5)]",
  },

  subtle: {
    blue: "shadow-[0_0_15px_rgba(59,130,246,0.2)]",
    green: "shadow-[0_0_15px_rgba(34,197,94,0.2)]",
    purple: "shadow-[0_0_15px_rgba(168,85,247,0.2)]",
    orange: "shadow-[0_0_15px_rgba(249,115,22,0.2)]",
  }
};

/**
 * Shadow variations
 */
export const shadows = {
  soft: "shadow-lg shadow-black/5",
  medium: "shadow-xl shadow-black/10",
  hard: "shadow-2xl shadow-black/20",
  colored: {
    blue: "shadow-xl shadow-blue-500/20",
    green: "shadow-xl shadow-green-500/20",
    purple: "shadow-xl shadow-purple-500/20",
    orange: "shadow-xl shadow-orange-500/20",
  },
  inner: "shadow-inner shadow-black/10",
  glow: "shadow-[0_0_40px_rgba(0,0,0,0.1)]"
};

/**
 * Border effects
 */
export const borders = {
  gradient: {
    blue: "border border-transparent bg-gradient-to-r from-blue-500 to-indigo-500 bg-clip-border",
    purple: "border border-transparent bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-border",
    rainbow: "border border-transparent bg-gradient-to-r from-red-500 via-yellow-500 to-blue-500 bg-clip-border",
  },
  glow: {
    blue: "border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]",
    green: "border border-green-500/50 shadow-[0_0_15px_rgba(34,197,94,0.3)]",
    purple: "border border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.3)]",
  },
  animated: "border border-blue-500/50 animate-pulse"
};

/**
 * Background patterns
 */
export const patterns = {
  dots: "bg-[radial-gradient(circle,rgba(0,0,0,0.1)_1px,transparent_1px)] bg-[size:20px_20px]",
  grid: "bg-[linear-gradient(rgba(0,0,0,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.05)_1px,transparent_1px)] bg-[size:20px_20px]",
  diagonal: "bg-[repeating-linear-gradient(45deg,transparent,transparent_10px,rgba(0,0,0,0.03)_10px,rgba(0,0,0,0.03)_20px)]",
  mesh: "bg-[radial-gradient(ellipse_at_top_right,rgba(59,130,246,0.1),transparent_50%),radial-gradient(ellipse_at_bottom_left,rgba(168,85,247,0.1),transparent_50%)]"
};

/**
 * Hover effects
 */
export const hovers = {
  lift: "transition-all duration-300 hover:-translate-y-2 hover:shadow-xl",
  glow: "transition-all duration-300 hover:shadow-[0_0_30px_rgba(59,130,246,0.4)]",
  scale: "transition-transform duration-300 hover:scale-105",
  brightness: "transition-all duration-300 hover:brightness-110",

  card: "transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:shadow-black/10",
  button: "transition-all duration-200 hover:scale-105 hover:shadow-lg active:scale-95",
};

/**
 * Loading shimmer effect
 */
export const shimmer = {
  base: "relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent",
  slow: "relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer-slow before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent",
};

/**
 * Text effects
 */
export const textEffects = {
  gradient: {
    blue: "bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent",
    purple: "bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent",
    rainbow: "bg-gradient-to-r from-red-500 via-yellow-500 to-blue-500 bg-clip-text text-transparent",
  },
  glow: {
    blue: "text-blue-500 drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]",
    green: "text-green-500 drop-shadow-[0_0_10px_rgba(34,197,94,0.5)]",
    purple: "text-purple-500 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]",
  },
  shimmer: "bg-gradient-to-r from-gray-900 via-gray-600 to-gray-900 bg-[length:200%_100%] bg-clip-text text-transparent animate-shimmer",
};

/**
 * Backdrop filters
 */
export const backdrops = {
  blur: {
    sm: "backdrop-blur-sm",
    md: "backdrop-blur-md",
    lg: "backdrop-blur-lg",
    xl: "backdrop-blur-xl",
  },
  saturate: "backdrop-saturate-150",
  brightness: "backdrop-brightness-110",
  contrast: "backdrop-contrast-125",
  combined: "backdrop-blur-md backdrop-saturate-150 backdrop-brightness-110"
};

/**
 * Combine effects helper
 */
export const combine = (...effects: string[]) => effects.join(" ");
