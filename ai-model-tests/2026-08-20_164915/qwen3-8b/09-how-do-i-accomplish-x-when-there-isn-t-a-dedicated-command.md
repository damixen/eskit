--- Test ---
Model: qwen3:8b
Question: How do I accomplish X when there isn't a dedicated command?
Elapsed time: 18.353 seconds

--- Response ---
model: qwen3:8b
If there isn't a dedicated command for your task (X), you have a few options based on the available tool structure:

### 1. **Use the AI Command for General Guidance**
   - The `ai` command allows you to ask questions to an AI model. This is ideal for tasks not explicitly covered by existing commands.
   - Example:
     ```bash
     eskit ai --model "claude-sonnet-4-6" --question "How do I accomplish X?"
     ```
   - **Key Parameters**:
     - `--model`: Choose a model (e.g., `claude-sonnet-4-6` for detailed reasoning).
     - `--question`: Clearly describe your task (X).

### 2. **Leverage Existing Commands with Custom Arguments**
   - If your task involves data retrieval or configuration, use the `archive show` or `ilm show` commands with custom parameters:
     ```bash
     eskit archive show --fields "settings.index.provided_name" --name "your_archive_name"
     ```
   - **Parameters**:
     - `--fields`: Specify nested fields (e.g., `settings.index.provided_name`).
     - `--flat`: Flatten nested dictionaries for easier parsing.

### 3. **Combine Commands for Complex Workflows**
   - For multi-step tasks, chain commands using intermediate outputs (e.g., use `ilm show` to get lifecycle data, then pass it to `ai` for analysis).

### 4. **Customize Configuration Files**
   - Modify `.eskit/config.json` to define new behaviors or default values for existing commands.

### 5. **Debug or Verbose Output**
   - Use `--verbose` or `--debug` flags to troubleshoot why a command might not be working as expected.

If you provide more details about task X, I can refine the approach! 🚀
