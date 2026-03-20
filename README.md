## System Overview

This system is designed to completely replace Keyboard Maestro’s native "Prompt for User Input" action, offering significantly greater formatting flexibility, faster rendering, and much richer data processing capabilities.

The system relies on a clean, modular architecture:

1. **Configuration:** You define your prompt's layout, buttons, text fields, and hotkeys using a simple, human-readable JSON file.
2. **Compilation:** A Python-based rendering engine converts that JSON file into a highly styled, responsive HTML interface. Because this compilation can happen _before_ run-time, the prompt appears on screen instantly when called.
3. **Execution:** A a Prompt via HTML Action displays the compiled HTML file.
4. **Data Return:** Upon user interaction, the prompt natively updates any specified Keyboard Maestro text variables, closes, and returns a rich string containing: the id of the selected button, a string of any keyboard modifiers held, the specific key pressed, and an optional custom param value.
## Features 

##### UI & Formatting Setup

- **Multi-Row Layouts:** Organize elements into horizontal rows, with optional left-aligned descriptive labels for clean, grid-like alignment.
- **Visual Grouping:** Add customizable horizontal line separators (thin, thick, dotted, and colored) above or below any row.
- **Item Types:** Supports clickable buttons, passive text phrases, invisible structural placeholders, and interactive text input fields.
- **Custom Styling:** Highlight specific buttons with colored borders, apply font styles (bold/italics), and set custom background colors for the entire window.
- **Configuration Metadata:** Built-in display for the configuration name and version number to easily track your UI iterations.

##### Interaction & Key Handling

- **Rich Data Return:** Upon submission, passes four distinct variables back to Keyboard Maestro for routing: the button id, the modifiers held, the specific key pressed, and an optional custom param.
- **Advanced Key Mapping:** Assign multiple distinct triggers to a single button using comma-separated lists (e.g., m, M, f1) or ranges (e.g., 1-9, a-z).
- **Smart Modifier Fallbacks:** Any button can accept any modifier natively. For example, pressing ⌘R will successfully trigger the r button while passing the ⌘ modifier back to Keyboard Maestro, _unless_ a dedicated ⌘R button explicitly exists to intercept it.
- **Hybrid Input System:** Seamlessly mixes single-key command triggers with standard text input fields. The script automatically pauses hotkeys when an input field is focused (Edit Mode) and restores them the moment you click away or press Enter/Escape (Command Mode).
- **Standard Dialog Behaviors:** Supports UI standards like designated Default (Enter) and Cancel (Escape) buttons, Tab-cycling between input fields, and native focus highlighting.
- **Integrated debugging****:** Ability to toggle Debug mode and view Prompt results. 

##### Architecture & Workflow

- **Frictionless JSON:** Easy-to-read, easily editable JSON architecture makes reordering rows or regrouping keys a matter of simple copy-and-pasting.
- **Comment Support:** Allows standard // or ; comments on their own lines within the JSON file for personal notes and documentation.
- **Pre-Compiled Performance:** HTML generation is processed independently of the display. This means the HTML file is built in advance, resulting in instantaneous loading when Keyboard Maestro calls the prompt.
- **Dynamic Variable Injection:** Automatically pulls values from Keyboard Maestro variables directly into the JSON to dynamically set titles, labels, or input placeholder text.
- **Visual Error Handling:** If a JSON syntax error occurs, the script catches it and generates a custom HTML error screen detailing the typo, rather than failing silently.

##### Known Limitations

- **Modifier Whitelisting:** The UI cannot natively restrict or "block" specific modifiers from being passed through. For example, you cannot prevent ⇧R from successfully triggering the r button. If strict modifier blocking is required, it must be handled via Switch/Case logic inside the resulting Keyboard Maestro macro.

  
## System Manifest

##### Keyboard Maestro Assets

- **Subroutine: Prompt Initialization** Contains the Python engine. Reads your .json configuration files and generates the corresponding .html interface files. Can be run globally (for all files) or targeted at a single prompt.
- **Sample Macros:** **meta**, **keypad**, **test-input** macros demonstrating how to call the prompt and process its results.

##### Local Files

- **meta.json**: A sample prompt configuration file demonstrating layout, styling, and key mapping rules.
- **keypad.json**: A keypad layout example.
* **test-input.json**: A test input example.
- **info.rtf**: This system overview and setup guide.
- **json.rtf**: The technical documentation detailing JSON keywords, syntax, and key mapping rules.

## Conventions

##### Global Variables

- MyPromptsPath: The absolute path to the directory where all of your prompt files (both JSON and HTML) are stored. Keyboard Maestro must have this variable set to locate your configurations.
- MyPromptDebug: Set automatically to stay in debug mode between Prompt invocations.

##### Naming Conventions (Strict)

- Every prompt must have a unique base **name**
- The configuration file must be named **name**.json
- The generated html file will be named  **name**.html.

##### Design Best Practices (Recommended)

- **The "Settings" Row:** For complex prompts, it is highly recommended to include a standardized "Settings ⌥" row at the bottom of your JSON layout (see meta.json for an example). This row should include buttons bound to standard shortcuts to instantly open the JSON file for editing (⌥e) or trigger the Prompt Initialization subroutine to refresh the HTML (⌥r).
- Prior to calling the Prompt via HTML Action, option to generate the **name**.html file in the same directory.

##### HTML Button Return Specification

When an action is triggered within the Custom HTML Prompt, the script passes a single, colon-delimited string back to Keyboard Maestro in the HTML Result Button variable.

The string is formatted as four distinct parts separated by colons: BaseID:Modifiers:Key:Parameter

##### Component Breakdown

| **Position** | **Component** | **Description**                                                                                                                                                                                                 | **Example**       |
| ------------ | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| **1**        | BaseID        | The id of the matched button defined in your JSON config. If triggered by default or cancel, it returns those respective IDs. <br><br>If an unmapped key is pressed while in Debug Mode, this returns NO MATCH. | btn_ok, NO MATCH  |
| **2**        | Modifiers     | The modifier keys held down when the key was pressed or the button was clicked. Returned as Apple symbols. Empty if no modifiers were pressed.                                                                  | ⌘⇧, ⌃⌥, (empty)   |
| **3**        | Key           | The actual physical keystroke that triggered the action. If the user clicked the button with a mouse instead of using a keyboard shortcut, this will be empty.                                                  | a, enter, escape  |
| **4**        | Parameter     | The optional string passed from the "param" field in your JSON configuration for that specific button. Empty if not defined.                                                                                    | save_doc, (empty) |

##### Output Examples

- **Standard Key Match:** btn_save:⌘:s:action_save   _(User pressed Command+S, triggering the button with ID "btn_save" which has a param of "action_save")_
- **Mouse Click:** btn_cancel:::   _(User clicked the button with ID "btn_cancel" using the mouse without any modifiers. Key and Param are empty)_
- **Debug Mode Catch:** NO MATCH:⇧:x:   _(Debug mode is ON. The user pressed Shift+X, which is not mapped in the JSON. Base ID becomes "NO MATCH", Key becomes "x", Modifiers become "_⇧_")_

##### Parsing in Keyboard Maestro

Because the output is predictably separated by colons, you can easily extract these values in Keyboard Maestro using a **Search using Regular Expression** action on the HTML Result Button variable.

A standard regex pattern to split these into your local variables would look like this:

^([^:]*):([^:]*):([^:]*):(.*)$

##### HTML Input String Return Specification

Unlike the HTML Result Button—which returns a single parsed string of the event that closed the prompt—text entered into input fields is pushed **directly** to Keyboard Maestro variables immediately before the prompt submits and closes.

##### Mapping Inputs to Keyboard Maestro Variables

The name of the Keyboard Maestro variable that gets populated is dictated entirely by the id you assign to the input in your JSON configuration.

##### JSON Configuration Example

{
  "type": "input",
  "id": “MyUserInput",
  "default": "Type here..."
}

##### Result upon Submission

Keyboard Maestro will now contain a variable named exactly MyUserInput, containing whatever text the user typed into that specific box.

| **JSON Property**  | **Keyboard Maestro Impact** | **Description**                                                                                  |
| ------------------ | --------------------------- | ------------------------------------------------------------------------------------------------ |
| id                 | **Variable Name**           | The exact name of the Keyboard Maestro variable to be created or overwritten.                    |
| value (User Typed) | **Variable Value**          | The literal string of text residing in the text box at the exact moment the prompt is submitted. |
| default            | **Fallback Value**          | If the user does not alter the text, the variable is populated with this default string.         |

##### Debug Mode Input Tracking

If Debug Mode is active (Local_PromptDebug is set to Y), the script performs an additional step to help you troubleshoot your inputs.

It compiles a list of every active input field's id and its current value, formats them line-by-line, and saves that combined string into a single Keyboard Maestro variable called: 

This allows you to verify exactly what data the HTML prompt attempted to pass back to the engine without having to check each variable individually.

##### Setup & Workflow

This prompt system expects all JSON configuration files to live in a single, dedicated folder. By default, the initialization subroutine processes all JSON files in this directory at once, but you can also configure it to regenerate specific files on demand.

**1. Initial System Setup**

1. Create a dedicated directory on your Mac to hold your prompt files (e.g., ~/Documents/KM_Prompts/).
2. Move your .json templates and documentation files into this directory.
3. In Keyboard Maestro, create a macro that runs on startup (or run it manually once) to set the global variable MyPromptsPath to this directory's exact path.

**2. Creating a New Prompt**

1. Choose a unique name for your prompt (e.g., workspace).
2. Duplicate a template JSON file, rename it to workspace.json, and place it in your prompts directory.
3. Run the **Prompt Initialization** subroutine to generate workspace.html.
4. In your new macro, call the Prompt via HTML Action and pass it the parameter "workspace.html” to display the interface.

**3. Modifying an Existing Prompt**

1. Open the prompt's .json file in your preferred text editor.
2. Adjust your rows, buttons, or shortcuts, and save the file.
3. Run the **Prompt Initialization** subroutine to read the updated JSON and overwrite the .html file. _(Tip: If you use the recommended "Settings" row, you can do this by simply pressing_ ⌥_r_ _while the prompt is open!)_
4. Update your Keyboard Maestro macro's Switch/Case actions to handle any new button IDs or parameters you created.

**4. Debugging Prompt inputs**

1. Use “id = debug” button in json file to toggle debug mode.
2. When “debug mode” is toggled on, input results will be displayed

**5. Upgrading the Engine**

If you need to update the Python rendering script to support new UI features or fix bugs:

1. Open the **Prompt Initialization** subroutine in Keyboard Maestro.
2. Locate the "Execute Shell Script" action that contains the Python 3 script.
3. Replace the script text with the newer version.
4. Run the **Prompt Initialization** subroutine across your entire prompts directory to instantly upgrade all of your .html interfaces with the new code logic.
