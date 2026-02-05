/**
 * Foundever Brand Design Tokens
 * ==============================
 * Extracted from Foundever Brand Graphic Guidelines 2024.
 *
 * This is the single source of truth for brand colors, typography,
 * and spacing in the frontend. All components should reference these
 * tokens rather than hardcoding values.
 *
 * Color system: 60/30/10 rule
 *   60% — background (indigo, white, or midnight depending on theme)
 *   30% — secondary (titles, paragraphs)
 *   10% — accent (highlights, a single accent per layout)
 */

// ---------------------------------------------------------------------------
// Colors
// ---------------------------------------------------------------------------

export const colors = {
  /** Primary brand color — "the heart of our color universe" */
  indigo: "#4b4bf9",

  /** Primary neutral — text, backgrounds, headings */
  midnight: "#09092d",

  white: "#ffffff",

  /** Subtle backgrounds */
  lightGrey: "#f3f3f7",

  /** Accent colors — use ONE per layout, never as dominant */
  accent: {
    lemon: "#f9ef77",
    coral: "#ff8d96",
    lavender: "#bfa1ff",
    mint: "#8bf0bb",
  },
} as const;

// ---------------------------------------------------------------------------
// Typography
// ---------------------------------------------------------------------------

export const fonts = {
  /** Headings, sub-headings, captions — never for body text */
  primary: "'Foundever Sans', sans-serif",

  /** Body copy, fallback for headings when primary unavailable */
  secondary: "'Calibri', sans-serif",

  /** System fallback stack */
  system:
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
} as const;

export const fontSizes = {
  title: "42pt",
  subtitle: "20pt",
  caption: "16pt",
  body: "13pt",
  detail: "11pt",
} as const;

export const fontPairings = {
  title: { family: fonts.primary, weight: 700, size: fontSizes.title },
  subtitle: { family: fonts.primary, weight: 300, size: fontSizes.subtitle },
  body: { family: fonts.secondary, weight: 400, size: fontSizes.body },
  bodyBold: { family: fonts.secondary, weight: 700, size: fontSizes.body },
  caption: { family: fonts.primary, weight: 400, style: "italic" as const, size: fontSizes.caption },
  detail: { family: fonts.primary, weight: 300, size: fontSizes.detail },
} as const;

// ---------------------------------------------------------------------------
// Spacing & Layout
// ---------------------------------------------------------------------------

export const spacing = {
  /** Logo clear space is Xx4 where X = width of two icon strokes */
  logoClearSpace: "Xx4",
  /** Partner logo gap */
  partnerLogoGap: "Xx16",
  /** Letter spacing range for body text only (0-50% of font size) */
  letterSpacingRange: [0, 0.5] as const,
  /** Leading range (20-50% of font size) */
  leadingRange: [0.2, 0.5] as const,
} as const;

// ---------------------------------------------------------------------------
// Logo
// ---------------------------------------------------------------------------

export const logo = {
  /** Minimum size for print */
  minPrint: "30mm",
  /** Minimum size for screen */
  minScreen: "60px",
  /** Icon background opacity range */
  iconBgOpacity: { min: 0.05, max: 0.1 },
  /** Default: indigo icon + midnight wordmark */
  defaultColors: {
    icon: colors.indigo,
    wordmark: colors.midnight,
  },
  /** On dark backgrounds */
  darkBgColors: {
    icon: colors.white,
    wordmark: colors.white,
  },
} as const;

// ---------------------------------------------------------------------------
// Color themes (60/30/10 rule)
// ---------------------------------------------------------------------------

export type ColorTheme = "main" | "white" | "dark" | "alternative";

export const colorThemes: Record<
  ColorTheme,
  { bg: string; secondary: string; accent: string; description: string }
> = {
  main: {
    bg: colors.indigo,
    secondary: colors.midnight,
    accent: colors.accent.mint,
    description: "Most corporate, main communication assets",
  },
  white: {
    bg: colors.white,
    secondary: colors.indigo,
    accent: colors.accent.lemon,
    description: "Long content — white papers, annual reports",
  },
  dark: {
    bg: colors.midnight,
    secondary: colors.indigo,
    accent: colors.accent.lemon,
    description: "Dark version of corporate theme",
  },
  alternative: {
    bg: colors.accent.mint,
    secondary: colors.midnight,
    accent: colors.indigo,
    description: "Social media, dedicated comms (requires studio approval)",
  },
};

// ---------------------------------------------------------------------------
// Brand rules (for validation / linting)
// ---------------------------------------------------------------------------

export const brandRules = {
  /** Text alignment must always be left, never justified */
  textAlignment: "left" as const,

  /** Max words for ALL CAPS labels */
  maxCapsWords: 3,

  /** Only one accent color per layout */
  maxAccentColorsPerLayout: 1,

  /** Never cover eyes in photography with text overlay */
  photographyEyeRule: true,

  /** Accent colors cannot be used on icons */
  accentOnIcons: false,
} as const;
