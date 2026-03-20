## Prompt JSON Configuration File
Version 9.1
##### 1. Global (Root) Configuration Properties

These keywords are placed at the very top level of your JSON file to control the window and default behaviors.

- **title**: (String) The main, bold text displayed at the top left of the prompt window.
- **message**: (String) The lighter, secondary text displayed next to the title.
- **prompt**: (String) The name of your configuration (displayed in the top right corner).
- **version**: (String) Your personal version tracking number (displayed in the top right corner).
- **color**: (String) The background color of the entire window. Accepts standard HTML colors (e.g., "AliceBlue", "#f2f2f2", "rgb(255,0,0)"). If omitted, it attempts to use the Keyboard Maestro variable %localColor% or defaults to light gray.
- **default**: (String) The name of the button that should be triggered when you press the standard **Return/Enter** key.
- **cancel**: (String) The name of the button that should be triggered when you press **Escape**. (If omitted, Escape simply cancels and closes the prompt natively).
- **rows**: (Array) A list of row objects. This contains all your UI elements.

---
##### 2. Row Properties

Each object inside the "rows" array represents a horizontal line in the dialog.

- **label**: (String) Text that appears in the left-hand column to describe the row. If any row has a label, the left column is automatically created for all rows.
- **buttons**: (Array) A list of item objects (buttons, phrases, inputs, or hidden elements) to display in this row.
- **line-before**: (String) Draws a horizontal separator _above_ the row. Accepts: "thin", "thick", or "dotted".
- **line-after**: (String) Draws a horizontal separator _below_ the row. Accepts: "thin", "thick", or "dotted".
- **line-color**: (String) Defines the color of the line-before or line-after separators (e.g., "Red", "#7A90F3").
---
##### 3. Item Properties (Buttons, Inputs, Phrases)

These are placed inside the "buttons" array of a row.

- **name**: (String) Required. The unique identifier for this item.
	- _For buttons_: This is the main value passed back to Keyboard Maestro.
	- _For inputs_: This becomes the exact Keyboard Maestro variable name where the typed text is saved.
- **label**: (String) The visible text displayed on the button or phrase. (Defaults to the name if omitted).
- **type**: (String) Defines how the item behaves. Defaults to "button".
	- "button": A standard clickable/typable button.
	- "input": A text entry field.
	- "phrase": Plain text displayed in the row (cannot be clicked or triggered).
	- "hidden": An invisible placeholder that takes up exactly one button's worth of space to help align columns. Can still be triggered via keyboard shortcut.
- **key**: (String) The keyboard shortcut(s) assigned to trigger this button. (See Key Mapping Rules below).
- **param**: (String) An optional secondary value passed back to Keyboard Maestro when this button is triggered (e.g., routing multiple buttons to one macro but passing different destination parameters).
- **color**: (String) The color of the button's border.
- **font**: (String) Applies styling to the item text. Accepts: "bold", "italics", or "both".
- **default**: (String) _For_ _type: "input"_ _only._ The initial placeholder text populated in the text field.
- **width**: (Number) _For_ _type: "input"_ _only._ The custom width of the text field in pixels (e.g., 150).
---
##### 4. Key Mapping Syntax & Rules

The "key" attribute handles how keyboard shortcuts are defined, supporting modifiers, lists, and ranges.

**Modifiers & Aliases**

You can prepend modifiers to any key. They can be combined (e.g., "cmd-opt-x"). The parser is case-insensitive and accepts the following aliases:

- **Command**: command, cmd, ⌘
- **Option**: option, opt, alt, ⌥
- **Control**: control, ctrl, ⌃
- _(Note: Shift_ ⇧ _is handled natively by typing the capital version of a letter, e.g.,_ _"A"_ _instead of_ _"a"__)._

**Lists (Multiple Triggers)**

You can assign multiple different keys to the same button by separating them with commas. Spaces around the commas are ignored.

- "key": "m, M" (Triggers on lowercase or uppercase M)
- "key": "1, f1, num1" (Triggers on standard 1, Function 1, or Numpad 1)

**Sequences / Ranges**

You can define a range of single alphanumeric characters using a hyphen (-).

- **Valid Ranges:** "a-z", "A-Z", "0-9"
- **Combined with prefixes:** "num0-num9" or "num0-9"
- **Combined in lists:** "a-f, x-z, 1-3"
- ⚠️ **Rule / Limitation:** Ranges _only_ work for single characters. You **cannot** use ranges for multi-character special keys (e.g., "f1-f12" is invalid and must be written out as "f1, f2, f3...").
---
##### 5. Special Keys Dictionary

When mapping non-alphanumeric keys, you must use their browser-standard event names.

- **escape** (Esc)
- **enter** (Standard Return/Enter)
- **backspace** (The standard Mac "Delete" key that erases backwards)
- **delete** (The Mac "Forward Delete" key, or fn+delete)
- **tab** (Tab key)
- **arrowup**, **arrowdown**, **arrowleft**, **arrowright** (Arrow keys)
- or **space** (Spacebar)

**Function Keys**

Function keys must be defined individually (no ranges). They are case-insensitive.

- f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, etc.

**Numpad (Keypad) Keys**

Numpad keys require a specific prefix to distinguish them from the standard number row.

- **Prefix Aliases**: num, numpad, keypad (e.g., "num1", "keypad1")
- **Numpad Numbers**: "num0" through "num9" _(Ranges allowed:_ _"num0-9"__)_
- **Numpad Operators**: "numDecimal", "numEnter", "numAdd", "numSubtract", "numMultiply", "numDivide", "numEqual", "numClear"
---
##### 6. General Rules

**Comments**

You can add comments directly into the JSON file to organize your configuration.

- A comment is created by starting a line with either // or ;.
- Any empty spaces or tabs before the // or ; are perfectly fine (they will still be ignored).
-  **Limitation:** Comments must be on their own line. You cannot place a comment at the very end of a line of valid JSON data.

**Keyboard Maestro Variables**

You can inject Keyboard Maestro variables dynamically into any string in your JSON file (titles, labels, button names, default input values, etc.). The script pulls the current variable value right as the prompt opens. The parser accepts three formats:

- `%Variable%MyVarName%` (Strict KM standard)
- `%MyVarName%` (Shorthand enclosed)
- `%MyVarName` (Shorthand open)