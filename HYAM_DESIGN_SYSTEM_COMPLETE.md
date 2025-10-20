# HY.AM Studios - Complete Design System
## Comprehensive Analysis from Live Website

**Source:** https://www.hyam.de/en/join-us
**Analysis Date:** 2025-10-16
**Method:** Live DOM inspection + Screenshot analysis

---

## 🎨 Color Palette (Exact Values)

### Primary Colors
```css
/* Backgrounds */
--bg-primary: rgb(17, 17, 17);           /* #111111 - Very dark charcoal */
--bg-white: rgb(255, 255, 255);          /* #FFFFFF - Pure white */
--bg-transparent: rgba(0, 0, 0, 0);      /* Transparent */

/* Text Colors */
--text-primary: rgb(255, 255, 255);      /* #FFFFFF - Pure white */
--text-secondary: rgb(0, 0, 0);          /* #000000 - Pure black */
--text-dark: rgb(17, 17, 17);            /* #111111 - Dark charcoal */
```

### Usage Guidelines
- **Strict Monochrome**: Only black, white, and charcoal - NO other colors
- **High Contrast**: Pure white text on very dark backgrounds
- **Transparency**: Used sparingly for overlays and transitions
- **Inversion**: White/black swap for different sections

---

## 📝 Typography System (Live Website Values)

### Font Families
```css
/* Primary (Headlines) */
--font-headline: "Helvetica Neue", sans-serif;

/* Secondary (Body/Mono) */
--font-body: "Apercu Pro Mono", mono;

/* System Fallback */
--font-system: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, "Noto Sans", sans-serif;
```

### Heading Styles (Exact Computed Values)

#### H1 - Main Headlines
```css
.heading-h1 {
  font-family: "Helvetica Neue", sans-serif;
  font-size: 40px;
  font-weight: 700;
  line-height: 36px;               /* Very tight - 90% of font size */
  text-transform: uppercase;
  letter-spacing: normal;
  color: rgb(255, 255, 255);
}
```

#### H2 - Secondary Headlines
```css
.heading-h2 {
  font-family: "Helvetica Neue", sans-serif;
  font-size: 31px;
  font-weight: 700;
  line-height: 27.9px;             /* 90% of font size */
  text-transform: uppercase;       /* Often used */
  color: rgb(255, 255, 255);
}
```

#### H3 - Tertiary Headlines
```css
.heading-h3 {
  font-family: "Helvetica Neue", sans-serif;
  font-size: 31px;
  font-weight: 700;
  line-height: 27.9px;
  color: rgb(255, 255, 255);
}
```

#### H4 - FAQ / Section Headers
```css
.heading-h4 {
  font-family: "Helvetica Neue", sans-serif;
  font-size: 16px - 20px;          /* Varies */
  font-weight: 700;
  text-transform: uppercase;
  color: rgb(255, 255, 255);
}
```

### Body Text Styles (Exact Computed Values)

#### Paragraphs
```css
.text-body {
  font-family: "Apercu Pro Mono", mono;
  font-size: 11px;                 /* VERY small */
  font-weight: 700;
  line-height: 11px;               /* 1:1 ratio - super tight */
  letter-spacing: -0.22px;         /* Negative tracking */
  color: rgb(255, 255, 255);
}
```

#### Links
```css
.text-link {
  font-family: "Apercu Pro Mono", mono;
  color: rgb(255, 255, 255);
  text-decoration: underline;
  font-size: 11px;
  font-weight: 700;
}
```

#### System Body Text
```css
.text-system {
  font-family: system-ui, sans-serif;
  font-size: 16px;
  line-height: 24px;
  color: rgb(0, 0, 0);
}
```

### Typography Hierarchy Summary
| Element | Font Size | Line Height | Weight | Transform |
|---------|-----------|-------------|--------|-----------|
| H1      | 40px      | 36px        | 700    | UPPERCASE |
| H2      | 31px      | 27.9px      | 700    | UPPERCASE |
| H3      | 31px      | 27.9px      | 700    | -         |
| H4      | 16-20px   | ~18px       | 700    | UPPERCASE |
| Body    | 11px      | 11px        | 700    | -         |
| Links   | 11px      | 11px        | 700    | underline |

---

## 📐 Layout & Spacing (Exact Values)

### Container Widths
```css
/* Max Width */
--container-max: 1920px;             /* Absolute maximum */

/* Content is centered, no strict width constraint */
```

### Padding System
```css
/* Common Padding Values (from live site) */
--padding-xs: 0px 8px;
--padding-sm: 0px 22px;              /* Most common horizontal */
--padding-md: 40px 0px;
--padding-lg: 67px 0px 0px;
--padding-xl: 0px 0px 112px;

/* Specific Use Cases */
--nav-padding: 0px 22px;             /* Navigation horizontal */
--section-padding: 80px 0px;         /* Between sections */
```

### Margin System
```css
/* Common Margin Values (from live site) */
--margin-xs: 4px 0px 0px;
--margin-sm: 12px 0px 0px;
--margin-md: 16px 0px 0px;
--margin-lg: 24px 0px 0px;
--margin-xl: 80px 0px;
--margin-2xl: 100px 0px 0px;

/* Content Spacing */
--gap-elements: 16px 0px 0px;        /* Between paragraphs */
--gap-sections: 80px 0px;            /* Between major sections */
```

### Spacing Scale
| Size | Value | Use Case |
|------|-------|----------|
| 2xs  | 4px   | Micro spacing |
| xs   | 8px   | Small gaps |
| sm   | 12px  | Text spacing |
| md   | 16px  | Element spacing |
| lg   | 24px  | Section spacing |
| xl   | 40px  | Large spacing |
| 2xl  | 80px  | Major sections |
| 3xl  | 100px | Hero spacing |

---

## 🎭 Component Specifications

### Navigation
```css
.navigation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 80px - 100px;              /* Variable */
  padding: 0px 22px;
  background-color: rgb(17, 17, 17);
  z-index: 1000;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-link {
  font-family: "Apercu Pro Mono", mono;
  font-size: 11px;
  font-weight: 700;
  color: rgb(255, 255, 255);
  text-decoration: none;
}

.nav-link:hover {
  text-decoration: underline;
}
```

### Buttons (Bracket Notation)
```css
.button-primary {
  background-color: transparent;
  color: rgb(255, 255, 255);
  border: 1px solid rgb(255, 255, 255);
  padding: 10px 20px;
  font-family: "Apercu Pro Mono", mono;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.button-primary:hover {
  background-color: rgb(255, 255, 255);
  color: rgb(17, 17, 17);
}

/* Bracket UI Elements */
.button-bracket {
  /* Format: [ Button Text ] */
  /* Example: [ × ], [ Reject ], [ Accept ] */
}
```

### Logo
```css
.logo {
  height: 40px - 80px;               /* Varies by context */
  width: auto;
}
```

### Images
- **Full-width hero images**: Breaking up text sections
- **Ratio**: Various (portrait, landscape, square)
- **Treatment**: High contrast, often grayscale or minimal color

---

## 🏗️ Layout Patterns

### Grid System
- **Flexbox Primary**: All layouts use flexbox
- **Centered Content**: `align-items: center`, `justify-content: center`
- **Vertical Flow**: Primary direction is column-based
- **Responsive**: Scales from 1920px down to mobile

### Component Arrangement
1. **Fixed Navigation**: Top of page, always visible
2. **Hero Section**: Large headline + image
3. **Content Blocks**: Text sections with tight spacing
4. **Full-Width Images**: Breaking up content
5. **FAQ Sections**: Collapsible items with numbers (01, 02, etc.)
6. **Footer**: Links, copyright, social

### Section Structure
```css
.section {
  padding: 80px 0px;
  margin: 0px auto;
  max-width: 1920px;
}

.section-hero {
  padding: 100px 0px 0px;
  text-align: center;
}

.section-content {
  padding: 40px 22px;
}
```

---

## ⚡ Interactive Elements

### Hover States
```css
/* Links */
a:hover {
  text-decoration: underline;
  transition: all 0.2s;
}

/* Buttons */
button:hover {
  background-color: rgb(255, 255, 255);
  color: rgb(17, 17, 17);
  transition: all 0.2s;
}

/* Navigation */
nav a:hover {
  opacity: 0.7;
  transition: opacity 0.2s;
}
```

### Animation Philosophy
- **Minimal**: No complex animations
- **Subtle**: Opacity and color transitions only
- **Fast**: 0.2s duration for most transitions
- **Performance**: CSS-only, no JavaScript animations
- **GSAP**: Used for scroll-based animations (evident from console warnings)

---

## 📱 Responsive Considerations

### Breakpoint Strategy
```css
/* Desktop First Approach */
@media (max-width: 1920px) {
  /* Scale down from max width */
}

@media (max-width: 1280px) {
  /* Tablet adjustments */
}

@media (max-width: 768px) {
  /* Mobile layout */
  .heading-h1 { font-size: 32px; }
  .heading-h2 { font-size: 24px; }
  .text-body { font-size: 12px; line-height: 14px; }
}
```

### Mobile Considerations
- **Large Typography**: 40px headers need significant mobile scaling
- **Touch Targets**: 11px text needs careful mobile treatment
- **Spacing**: Reduce massive spacing on small screens
- **Images**: Stack vertically, maintain aspect ratios

---

## 🎯 Brand Personality

### Visual Language
- **Extreme Minimalism**: Only black, white, transparency
- **Bold Typography**: Massive headlines, tiny body text
- **Swiss/Brutalist**: Clean, systematic, functional
- **Monospace Technical**: Precision and attention to detail
- **High Contrast**: Dramatic black/white separation

### Content Approach
- **All Caps Headlines**: Bold, authoritative statements
- **Tight Letter Spacing**: Compressed, modern feel (negative tracking)
- **Minimal Copy**: Every word carefully chosen
- **Bracket Notation**: `[ × ]`, `[ Reject ]`, `[ Accept ]` for UI
- **Numbers**: FAQ items numbered (01, 02, 03...)

---

## 💡 Implementation Guidelines

### CSS Custom Properties (Complete Set)
```css
:root {
  /* Colors */
  --color-bg-primary: rgb(17, 17, 17);
  --color-bg-white: rgb(255, 255, 255);
  --color-text-primary: rgb(255, 255, 255);
  --color-text-secondary: rgb(0, 0, 0);

  /* Typography */
  --font-headline: "Helvetica Neue", sans-serif;
  --font-body: "Apercu Pro Mono", mono;
  --font-size-h1: 40px;
  --font-size-h2: 31px;
  --font-size-h3: 31px;
  --font-size-body: 11px;
  --line-height-h1: 36px;
  --line-height-h2: 27.9px;
  --line-height-body: 11px;
  --letter-spacing-body: -0.22px;
  --font-weight-bold: 700;

  /* Layout */
  --container-max: 1920px;
  --nav-height: 80px;
  --nav-padding: 22px;
  --section-padding: 80px;
  --content-gap: 16px;

  /* Transitions */
  --transition-fast: 0.2s;
  --transition-medium: 0.3s;
}
```

### Component Classes
```css
/* Base */
.hyam-container { max-width: var(--container-max); }
.hyam-section { padding: var(--section-padding) 0; }

/* Typography */
.hyam-h1 { /* H1 styles */ }
.hyam-h2 { /* H2 styles */ }
.hyam-h3 { /* H3 styles */ }
.hyam-body { /* Body text styles */ }
.hyam-link { /* Link styles */ }

/* Components */
.hyam-nav { /* Navigation styles */ }
.hyam-button { /* Button styles */ }
.hyam-button-bracket { /* Bracket notation button */ }
```

---

## 🔧 Technical Notes

### Font Loading
```css
/* Ensure proper font loading */
@font-face {
  font-family: "Apercu Pro Mono";
  src: url("path/to/font.woff2") format("woff2");
  font-weight: 700;
  font-display: swap;
}
```

### Performance
- **Minimal CSS**: Very small footprint
- **System Fonts**: Fallbacks for performance
- **No Heavy JS**: GSAP for scroll only
- **Fast Transitions**: 0.2s max
- **CSS-only Animations**: No performance impact

### Accessibility
- **High Contrast**: ✅ WCAG AAA compliant (white on #111111)
- **Focus States**: Needs implementation
- **Font Size**: ⚠️ 11px body text may be too small for some users
- **Touch Targets**: ⚠️ Need 44px minimum for mobile

---

## 📊 Key Design System Differentiators

1. **Extreme Minimalism**: Only black (#111111), white (#FFFFFF), transparency
2. **Typography Hierarchy**: HUGE headlines (40px) vs TINY body (11px) = 3.6:1 ratio
3. **Monospace Secondary**: Technical precision with Apercu Pro Mono
4. **Swiss/Brutalist**: Clean, systematic, functional, no decoration
5. **Bracket UI**: Distinctive `[ × ]` notation for all interactive elements
6. **Tight Line Height**: 90% ratio on headlines (36px / 40px)
7. **Negative Letter Spacing**: -0.22px on body text for compression
8. **All Caps Headlines**: Consistent uppercase treatment
9. **1:1 Line Height**: Body text at 11px / 11px for super-tight rendering

---

## 📸 Visual Reference Examples

### Navigation
- Fixed top, dark background
- Small monospace links (11px)
- Logo centered or left-aligned
- Burger menu: `[ × ]` notation

### Hero Section
- Large uppercase headline (40px)
- Tight line-height (36px / 40px = 90%)
- Full-width background image
- Minimal text, maximum impact

### Content Blocks
- Small monospace body text (11px)
- White text on dark background
- Generous section spacing (80px)
- Tight paragraph spacing (16px)

### FAQ Section
- Numbered items (01, 02, 03...)
- Collapsible headers
- Small body text with images
- Clean borders/dividers

### Buttons
- Bracket notation: `[ Button Text ]`
- Transparent background
- White border + white text
- Inverts on hover (white bg, black text)

---

## 🚀 Quick Start Implementation

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HY.AM Style</title>
  <style>
    :root {
      --color-bg: #111111;
      --color-text: #ffffff;
      --font-headline: "Helvetica Neue", sans-serif;
      --font-body: "Courier New", monospace;
    }

    body {
      background-color: var(--color-bg);
      color: var(--color-text);
      font-family: var(--font-body);
      font-size: 11px;
      line-height: 11px;
      letter-spacing: -0.22px;
      margin: 0;
      padding: 0;
    }

    h1 {
      font-family: var(--font-headline);
      font-size: 40px;
      font-weight: 700;
      line-height: 36px;
      text-transform: uppercase;
      letter-spacing: normal;
    }

    .button {
      background: transparent;
      color: var(--color-text);
      border: 1px solid var(--color-text);
      padding: 10px 20px;
      font-family: var(--font-body);
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s;
    }

    .button:hover {
      background: var(--color-text);
      color: var(--color-bg);
    }
  </style>
</head>
<body>
  <h1>HY.AM STUDIOS</h1>
  <p>A creative studio from Berlin</p>
  <button class="button">[ Let's Talk ]</button>
</body>
</html>
```

---

This design system captures every detail from the live HY.AM website, ready for implementation in your daily activity review page or any other project requiring this distinctive aesthetic.
