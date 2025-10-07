# Smart Source Tracking - Visual Guide

## 🎨 **What Users Will See**

### **1. Message with Inline Citations**

**Before** (old behavior):
```
┌─────────────────────────────────────────────────┐
│ 🤖 AI Assistant                                 │
│                                                 │
│ Based on our Q4 report, revenue was $5.2M...   │
│                                                 │
│ 3:45 PM   📚 15 sources                         │
└─────────────────────────────────────────────────┘
```

**After** (new behavior):
```
┌─────────────────────────────────────────────────┐
│ 🤖 AI Assistant                                 │
│                                                 │
│ Based on our Q4 report, revenue was $5.2M...   │
│ ─────────────────────────────────────────────   │
│ Sources used in this response:                  │
│  [1] Q4_Report.pdf   [3] Budget_2024.xlsx      │
│                                                 │
│ 3:45 PM   📚 3 used / 15 total                  │
└─────────────────────────────────────────────────┘
```

---

### **2. Sources Modal - Default View (Used Only)**

```
╔═══════════════════════════════════════════════════════════╗
║ Sources & Citations                                    [X]║
╠═══════════════════════════════════════════════════════════╣
║ Response:                                                 ║
║ Based on our Q4 report, revenue was $5.2M...             ║
╟───────────────────────────────────────────────────────────╢
║ ✓ 3 Used / 15 Total          Show all sources [  ]       ║
╟───────────────────────────────────────────────────────────╢
║ 3 sources displayed:                                      ║
║                                                           ║
║ ┌─────────────────────────────────────────────────────┐  ║
║ │ 📄 Q4_Report.pdf                    ✓ Used    92%   │  ║
║ │    Page 3                                           │  ║
║ │    ┌─────────────────────────────────────────────┐ │  ║
║ │    │ Why this source was used:                   │ │  ║
║ │    │ Contains Q4 sales target figures            │ │  ║
║ │    └─────────────────────────────────────────────┘ │  ║
║ │    "The Q4 sales targets were set at..."           │  ║
║ │    🔗 Source 1                                      │  ║
║ └─────────────────────────────────────────────────────┘  ║
║                                                           ║
║ ┌─────────────────────────────────────────────────────┐  ║
║ │ 📄 Budget_2024.xlsx                 ✓ Used    87%   │  ║
║ │    Page 1                                           │  ║
║ │    ┌─────────────────────────────────────────────┐ │  ║
║ │    │ Why this source was used:                   │ │  ║
║ │    │ Provides departmental budget breakdown      │ │  ║
║ │    └─────────────────────────────────────────────┘ │  ║
║ │    "Engineering: $2.1M, Sales: $1.8M..."           │  ║
║ │    🔗 Source 3                                      │  ║
║ └─────────────────────────────────────────────────────┘  ║
║                                                           ║
║ ┌─────────────────────────────────────────────────────┐  ║
║ │ 📄 Historical_Data.csv              ✓ Used    78%   │  ║
║ │    ┌─────────────────────────────────────────────┐ │  ║
║ │    │ Why this source was used:                   │ │  ║
║ │    │ Historical context for comparison           │ │  ║
║ │    └─────────────────────────────────────────────┘ │  ║
║ │    "Q4 2023: $4.8M, Q4 2022: $4.2M..."             │  ║
║ │    🔗 Source 7                                      │  ║
║ └─────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════╝
```

---

### **3. Sources Modal - Show All Enabled**

```
╔═══════════════════════════════════════════════════════════╗
║ Sources & Citations                                    [X]║
╠═══════════════════════════════════════════════════════════╣
║ Response:                                                 ║
║ Based on our Q4 report, revenue was $5.2M...             ║
╟───────────────────────────────────────────────────────────╢
║ ✓ 3 Used / 15 Total          Show all sources [✓]        ║
╟───────────────────────────────────────────────────────────╢
║ 15 sources displayed:                                     ║
║                                                           ║
║ ┌─────────────────────────────────────────────────────┐  ║
║ │ 📄 Q4_Report.pdf                    ✓ Used    92%   │  ║
║ │    [Green border - USED SOURCE]                     │  ║
║ │    [Shows usage reason as before]                   │  ║
║ └─────────────────────────────────────────────────────┘  ║
║                                                           ║
║ ┌─────────────────────────────────────────────────────┐  ║
║ │ 📄 Company_Overview.pdf                        85%   │  ║
║ │    [Blue border - NOT USED]                         │  ║
║ │    "Our company was founded in..."                  │  ║
║ │    🔗 Source 2                                       │  ║
║ └─────────────────────────────────────────────────────┘  ║
║                                                           ║
║ ┌─────────────────────────────────────────────────────┐  ║
║ │ 📄 Budget_2024.xlsx                 ✓ Used    87%   │  ║
║ │    [Green border - USED SOURCE]                     │  ║
║ └─────────────────────────────────────────────────────┘  ║
║                                                           ║
║ [... 12 more sources ...]                                ║
╚═══════════════════════════════════════════════════════════╝
```

---

### **4. Legacy Message Detection**

```
╔═══════════════════════════════════════════════════════════╗
║ Sources & Citations                                    [X]║
╠═══════════════════════════════════════════════════════════╣
║ Response:                                                 ║
║ Based on our Q4 report, revenue was $5.2M...             ║
╟───────────────────────────────────────────────────────────╢
║ ⓘ Legacy message: All sources shown. Source usage        ║
║   tracking was not available when this message was        ║
║   generated.                                              ║
╟───────────────────────────────────────────────────────────╢
║ 15 sources displayed:                                     ║
║                                                           ║
║ [Shows all sources without "Used" badges]                ║
║ [No "Show All" toggle]                                    ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 🎯 **Key Visual Elements**

### **Color Coding**
- **Green**: Used sources (primary focus)
  - Border: `border-l-green-500`
  - Badge: `bg-green-500`
  - Text: `text-green-700`

- **Blue**: Unused sources (secondary)
  - Border: `border-l-primary/50`
  - Badge: `bg-blue-500`
  - Text: `text-muted-foreground`

### **Badges**
```
┌──────────────┐
│ ✓ Used       │  <- Green badge on used sources
└──────────────┘

┌──────────────┐
│ 92%          │  <- Relevance score (green if >80%)
└──────────────┘
```

### **Inline Citations**
```
[1] Q4_Report.pdf
└─┘ └──────────┘
 │      │
 │      └─ Document name (clickable)
 └─ Source number (matches retrieval order)
```

### **Usage Reason Box**
```
┌─────────────────────────────────────────────┐
│ Why this source was used:                   │
│ Contains Q4 sales target figures            │
└─────────────────────────────────────────────┘
  ▲ Green background with rounded corners
```

---

## 🔄 **User Interactions**

### **1. View Message → See Inline Citations**
```
User sees message
    ↓
Inline citations displayed below
    ↓
Click [1] Q4_Report.pdf
    ↓
Sources modal opens to that source
```

### **2. Open Sources Modal → Toggle View**
```
User clicks "📚 3 used / 15 total"
    ↓
Modal opens (default: used only)
    ↓
User toggles "Show all sources"
    ↓
Modal shows all 15 sources (used ones highlighted)
    ↓
User can toggle back to used only
```

### **3. Expand Source Details**
```
User sees source card
    ↓
Preview text is truncated (line-clamp-2)
    ↓
Click "Show more ▼"
    ↓
Full text expands
    ↓
Click "Show less ▲"
    ↓
Text collapses back
```

---

## 📱 **Responsive Design**

### **Desktop (>768px)**
- Source cards: Full width
- Inline citations: Multi-line wrap
- Modal: 4xl width (max-w-4xl)

### **Tablet (768px)**
- Source cards: Slightly narrower
- Inline citations: 2-3 per row
- Modal: Full width with padding

### **Mobile (<768px)**
- Source cards: Stack vertically
- Inline citations: 1-2 per row
- Modal: Full screen height

---

## 🎨 **Dark Mode Support**

All components support dark mode:

### **Light Mode**
- Background: `bg-white`
- Text: `text-gray-900`
- Border: `border-gray-200`
- Used badge: `bg-green-500`

### **Dark Mode**
- Background: `bg-gray-800`
- Text: `text-white`
- Border: `border-gray-700`
- Used badge: `bg-green-600`

---

## ✨ **Animation & Transitions**

### **Hover Effects**
```css
hover:border-l-green-600   /* Border darkens on hover */
hover:bg-green-100         /* Background lightens */
transition-colors          /* Smooth 150ms transition */
```

### **Expand/Collapse**
```css
line-clamp-2              /* Initially show 2 lines */
(no clamp on expand)      /* Show full text */
```

### **Modal Open/Close**
```typescript
Dialog component handles:
- Fade in/out
- Scale animation
- Backdrop blur
```

---

## 🎯 **Accessibility**

### **Keyboard Navigation**
- `Tab`: Navigate between sources
- `Enter/Space`: Open source modal
- `Escape`: Close modal

### **Screen Readers**
```tsx
<button aria-label="View source details">
<div role="dialog" aria-modal="true">
<Badge aria-label="Source used in response">
```

### **Focus States**
```css
focus:ring-2 focus:ring-primary
focus-visible:outline-none
```

---

## 📊 **State Indicators**

### **Loading**
```
┌─────────────────────────────────────────────────┐
│ 🤖 AI Assistant                                 │
│                                                 │
│ ⏳ Thinking...                                  │
└─────────────────────────────────────────────────┘
```

### **Error**
```
┌─────────────────────────────────────────────────┐
│ 🤖 AI Assistant                                 │
│                                                 │
│ ⚠️ I encountered an error processing your       │
│    question.                                    │
│                                                 │
│ [Retry]                                         │
└─────────────────────────────────────────────────┘
```

### **Empty State**
```
╔═══════════════════════════════════════════════════════════╗
║ Sources & Citations                                       ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║           No sources were directly used in                ║
║           this response.                                  ║
║                                                           ║
║           Toggle "Show all sources" to see all            ║
║           retrieved sources.                              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

**Status**: ✅ **VISUAL DESIGN COMPLETE**

*Last updated: October 7, 2025*
