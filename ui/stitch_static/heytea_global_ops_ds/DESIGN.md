---
name: HEYTEA Global Ops DS
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1b1b1b'
  on-surface-variant: '#4c4546'
  inverse-surface: '#303030'
  inverse-on-surface: '#f1f1f1'
  outline: '#7e7576'
  outline-variant: '#cfc4c5'
  surface-tint: '#5e5e5e'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1b1b1b'
  on-primary-container: '#848484'
  inverse-primary: '#c6c6c6'
  secondary: '#5d5f5f'
  on-secondary: '#ffffff'
  secondary-container: '#dfe0e0'
  on-secondary-container: '#616363'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1b1b1b'
  on-tertiary-container: '#848484'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c6'
  on-primary-fixed: '#1b1b1b'
  on-primary-fixed-variant: '#474747'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c7'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#454747'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c6'
  on-tertiary-fixed: '#1b1b1b'
  on-tertiary-fixed-variant: '#474747'
  background: '#f9f9f9'
  on-background: '#1b1b1b'
  surface-variant: '#e2e2e2'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
spacing:
  base: 4px
  container-padding: 24px
  gutter: 16px
  row-height-dense: 32px
  row-height-standard: 48px
---

## Brand & Style

The design system is engineered for high-stakes operational oversight, translating HEYTEA’s premium consumer identity into a rigorous B2B analytical environment. The aesthetic is **Corporate Minimalism**: a style that prioritizes data density and clarity over decorative elements.

The UI evokes a sense of **unshakable authority and precision**. By utilizing a monochromatic foundation punctuated by high-visibility functional accents, the platform directs the user's focus toward exceptions and risks. The emotional response is one of professional confidence—providing regional managers and technical leads with a "command center" feel that is both secure and highly efficient.

## Colors

The color strategy is binary and functional. **HEYTEA Black** is the primary driver for headers, primary actions, and successful status states, reinforcing the brand's premium positioning. The **Light Gray background** reduces eye strain during long-form data review sessions.

Accent colors are strictly reserved for semantic meaning:
- **Risk Red (#D9001B):** Critical failures, immediate action required.
- **Warning Orange (#F59A23):** Partial success or manual intervention pending.
- **Neutral Gray:** Inactive states, breadcrumbs, and secondary metadata.
- **Success Black:** Unlike traditional green-based systems, "Success" is represented by the primary brand black to maintain a sophisticated, monochromatic aesthetic.

## Typography

The typography system leverages **Inter** for its exceptional legibility in data-heavy interfaces. The hierarchy is tight, with small increments between levels to maximize vertical space.

For technical strings such as Store IDs, Transaction Hashes, or SKU codes, a monospaced font (JetBrains Mono) is introduced to ensure character alignment and prevent reading errors. **Label-caps** are used for table headers to create clear visual separation from row data.

## Layout & Spacing

This design system utilizes a **12-column fluid grid** with fixed margins of 24px. The rhythm is based on a **4px baseline grid**, ensuring tight alignment in high-density tables and forms.

Layout adapts as follows:
- **Desktop (1440px+):** Full sidebar navigation (fixed 240px) with fluid content area.
- **Tablet (1024px):** Sidebar collapses to icons; table columns prioritize "Status" and "Risk Level."
- **Mobile (375px):** Stacked cards replace tables; horizontal scrolling is strictly limited to data-essential grids.

## Elevation & Depth

To maintain a "Flat Corporate" aesthetic, shadows are largely avoided. Instead, the system uses **Tonal Layering** and **Low-Contrast Outlines**:
- **Level 0 (Background):** Light Gray (#F5F5F5).
- **Level 1 (Cards/Tables):** Pure White (#FFFFFF) with a 1px solid border (#E0E0E0).
- **Level 2 (Popovers/Modals):** Pure White with a subtle, sharp 4px shadow (Opacity 10%, No Blur) to maintain the geometric feel.

No glassmorphism or gradients are permitted. Depth is communicated solely through structural lines and value shifts between the background and foreground containers.

## Shapes

The shape language is **Sharp (0px)**. All containers, buttons, and input fields utilize 90-degree corners to reflect an architectural, authoritative tone. This reinforces the "technical tool" identity and differentiates the internal platform from HEYTEA’s consumer-facing app, which uses softer, more organic shapes.

The only exception is for circular status indicators (pills) used in tags, which may use a 2px radius to avoid appearing "jagged" at small scales.

## Components

### Buttons
- **Primary:** Solid HEYTEA Black, White text, 0px radius.
- **Secondary:** White background, 1px Black border, Black text.
- **Danger:** Solid Risk Red, White text.

### High-Density Tables
- **Header:** Gray #F5F5F5 background, Label-caps typography, 1px bottom border.
- **Rows:** Alternating zebra striping is prohibited; use 1px subtle dividers instead.
- **Cell Padding:** 8px vertical, 12px horizontal.

### Status Tags (Sharp Rectangles)
- **Success:** Black background / White text.
- **Partial:** Warning Orange background / Black text.
- **Failed:** Risk Red background / White text.
- **Pending:** Neutral Gray #E0E0E0 background / Black text.

### Metric Cards
White background, 1px solid border. Title is in `Label-caps`. The primary metric is in `Display-lg` font. If a metric represents a risk, the font color shifts to Risk Red.

### Input Fields
1px solid border (#E0E0E0). On focus, the border thickens to 2px HEYTEA Black. No glow or shadow effects. Labels are always top-aligned.
