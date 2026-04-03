# Design System Specification: Editorial Fintech for Delivery Partners

## 1. Overview & Creative North Star
**Creative North Star: The Resilient Architect**

This design system moves away from the "disruptive startup" aesthetic toward a feeling of permanent, institutional strength tailored for the modern gig economy. For a delivery partner, their phone is their office; the UI must feel like a high-end, architectural space—quiet, organized, and premium.

We break the "template" look through **Intentional Asymmetry** and **Tonal Depth**. Instead of rigid, centered grids, we utilize generous white space and off-center focal points to guide the eye. We don't use lines to separate ideas; we use the logic of light and layers.

---

## 2. Colors & Surface Logic
Our palette transitions from the stability of Deep Navy (`primary`) to the energetic utility of Amber (`secondary`). 

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning or containment. Traditional "lines" create visual noise that degrades the premium feel. 
- **The Solution:** Boundaries must be defined solely through background color shifts. For example, a `surface-container-low` section sitting on a `surface` background creates a clear but sophisticated boundary.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of fine paper or frosted glass. Use the `surface-container` tiers to create depth:
- **Level 0 (Base):** `surface` (#f7f9fc) - The canvas.
- **Level 1 (Sections):** `surface-container-low` (#f2f4f7) - Grouping large content areas.
- **Level 2 (Priority Cards):** `surface-container-lowest` (#ffffff) - High-priority interactive elements.
- **Level 3 (Overlays):** `surface-container-high` (#e6e8eb) - Active states or contextual menus.

### The "Glass & Gradient" Rule
To elevate the "Modern Banking" aesthetic, use **Glassmorphism** for floating action buttons or sticky headers. 
- **Formula:** `surface-container-lowest` at 80% opacity + `backdrop-blur` (12px-20px).
- **Signature Textures:** Apply a subtle linear gradient (Top-Left: `primary` #002653 to Bottom-Right: `primary-container` #1a3c6e) for main CTAs. This creates a "sheen" that feels metallic and high-value.

---

## 3. Typography: Editorial Authority
We pair **Manrope** (Display/Headlines) with **Inter** (Body/Labels) to balance character with legibility.

- **Display & Headlines (Manrope):** These are your "anchors." Use `display-md` for account balances and `headline-sm` for section titles. The bold weights of Manrope provide the "Trustworthy" weight requested.
- **Body & Labels (Inter):** Inter is a workhorse. Use `body-md` for all standard delivery details. Its neutral tone ensures that the "Professional" aesthetic remains intact without competing with the headlines.
- **The Contrast Rule:** Use `on-surface-variant` (#43474f) for secondary metadata to create a clear "read-first/read-second" hierarchy.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are often "dirty." We use **Ambient Shadows** and **Layering Principles** to achieve height.

- **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` background. This "Soft Lift" is the primary method of elevation.
- **Ambient Shadows:** For floating elements (Modals/FABs), use a multi-layered shadow:
  - `box-shadow: 0 12px 32px -4px rgba(25, 28, 30, 0.08);`
  - The shadow color is a tinted version of `on-surface`, never pure black.
- **The "Ghost Border" Fallback:** If a border is required for high-glare environments (delivery outdoors), use the `outline-variant` token at **15% opacity**. 100% opaque borders are strictly forbidden.

---

## 5. Components

### Buttons
- **Primary:** Gradient fill (`primary` to `primary-container`). Corner radius: `md` (0.75rem). No shadow; the color weight provides the prominence.
- **Secondary:** `secondary-fixed` background with `on-secondary-fixed` text. Used for "Add Coverage" or "Renew."
- **Tertiary:** Text-only using `primary` color. High-padding (12px/24px) to ensure a large touch target for partners on the move.

### Input Fields
- **Container:** `surface-container-highest` background.
- **State:** No bottom line. On focus, use a 2px "Ghost Border" of `primary` at 40% opacity. 
- **Typography:** Labels use `label-md` in `on-surface-variant`.

### Cards & Lists
- **The Rule of Zero Dividers:** Never use a horizontal line to separate list items. Use 16px (`spacing-4`) of vertical whitespace or a subtle background toggle between `surface-container-lowest` and `surface-container-low`.
- **Card Styling:** Use `rounded-lg` (1rem) for all main dashboard cards to evoke a "friendly-modern" professional feel.

### Specialized Component: The "Active Shield" Chip
For insurance apps, status is everything.
- **Status Chips:** Use `success` or `error` containers with 10% opacity, paired with high-contrast text. Example: A "Policy Active" chip uses `on-tertiary-container` text on a semi-transparent `tertiary_container` base.

---

## 6. Do’s and Don’ts

### Do
- **Do** use `spacing-8` (2rem) between major sections to let the UI breathe.
- **Do** use `on-surface-variant` for "label" text to ensure it doesn't compete with the data.
- **Do** rely on the `surface-container` tiers for all grouping logic.
- **Do** use `manrope` bold for all numerical data (balances, dates, claim numbers).

### Don't
- **Don't** use 1px solid #CCCCCC borders.
- **Don't** use pure black (#000000) for text or shadows; use `on-surface` (#191c1e).
- **Don't** use sharp corners. The minimum radius is `sm` (0.25rem) for small chips; cards must be `lg` (1rem).
- **Don't** use standard "drop shadow" presets. Use the Ambient Shadow formula specified in Section 4.