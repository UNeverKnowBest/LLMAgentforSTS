# Slay the Spire LLM Agent

An intelligent agent for playing Slay the Spire using Large Language Models, designed to work with the CommunicationMod.

## Overview

This project implements an AI agent that can autonomously play Slay the Spire by:
- Reading game state from the CommunicationMod
- Using LLM reasoning to make strategic decisions
- Validating and executing commands
- Handling errors with intelligent fallback strategies

## Features

- **Robust Command Validation**: Validates all commands against CommunicationMod's expected format
- **Intelligent Decision Making**: Uses LLM prompts tailored to different game situations
- **Error Recovery**: Automatic fallback commands when validation fails
- **Comprehensive Logging**: Detailed logs for debugging and analysis
- **Modular Architecture**: Clean separation of concerns using LangGraph

## Requirements

### Software Dependencies
- Python 3.8+
- Slay the Spire (Steam version)
- CommunicationMod (included in this repository)
- Ollama (for local LLM) or Google AI API key (for Gemini)

### Python Dependencies
Install with: `pip install -r requirements.txt`

## Setup

### 1. Install CommunicationMod

1. Install ModTheSpire if you haven't already
2. Copy the `CommunicationMod-master` folder to your Slay the Spire mods directory
3. Enable CommunicationMod in ModTheSpire

### 2. Configure the Agent

Edit `src/config.py` to set your preferred model:

```python
# For local Ollama model
PRIMARY_MODEL_NAME = "qwen2.5:7b"  # or any Ollama model
PRIMARY_MODEL_TYPE = "local"

# For Google Gemini
PRIMARY_MODEL_NAME = "gemini-pro"
PRIMARY_MODEL_TYPE = "gemini"
```

### 3. Set Environment Variables (if using Gemini)

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

1. Start Slay the Spire with CommunicationMod enabled
2. In the mod settings, set the external command to: `python main.py`
3. Start a new game - the agent will automatically begin playing

### Manual Testing

Run the test suite to verify everything is working:

```bash
python test_agent.py
```

### Configuration Options

#### Character Selection
Edit `src/config.py` to change the starting character:
```python
PRIMARY_CHARACTER = "THE_SILENT"  # Options: THE_SILENT, IRONCLAD, DEFECT, WATCHER
```

#### LLM Settings
```python
PRIMARY_MODEL_TEMPERATURE = 0.0  # Controls randomness (0.0 = deterministic)
```

## Architecture

### Graph Structure
The agent uses LangGraph to define a state machine with the following flow:

```
START → initial_game → read_state → advice_on_command → validate_command
                         ↑              ↓                      ↓
                         └── ← ← ← execute_command    handle_validation_failure
                                      ↑                        ↓
                                      └── ← ← ← execute_fallback_command
```

### Key Components

- **`nodes.py`**: Core game logic and LLM interaction
- **`states.py`**: State definitions for the agent
- **`builder.py`**: Graph construction and workflow definition
- **`prompt_generator.py`**: Dynamic prompt generation based on game state
- **`config.py`**: Configuration settings

### Node Functions

1. **`initial_game`**: Sends handshake to start the game
2. **`read_state`**: Reads JSON game state from stdin
3. **`advice_on_command`**: Gets command from LLM or uses simple rules
4. **`validate_command`**: Validates command format and availability
5. **`handle_validation_failure`**: Analyzes errors and generates fallback
6. **`execute_command`**: Sends valid command to the game
7. **`execute_fallback_command`**: Executes safe fallback command

## Command Validation

The agent validates all commands against CommunicationMod's specification:

### Supported Commands
- `play [card_index] [target_index?]` - Play a card
- `end` - End turn
- `choose [choice]` - Make a choice (by index or text)
- `potion use/discard [index] [target?]` - Use or discard potion
- `confirm/proceed` - Confirm action
- `skip/cancel/return/leave` - Cancel/skip action
- `start [character] [ascension?] [seed?]` - Start new game
- `state` - Request current state
- `key [keyname] [timeout?]` - Press key
- `click left/right [x] [y] [timeout?]` - Mouse click
- `wait [time]` - Wait specified time

### Fallback Strategy
When validation fails, the agent chooses safe commands based on screen type:
- Combat: `state`
- Card Reward: `skip`
- Shop: `leave`
- Map: `state`
- etc.

## Troubleshooting

### Common Issues

1. **"No module named src"**
   - Ensure you're running from the project root directory
   - Try: `python -m main` instead of `python main.py`

2. **"Cannot connect to Ollama"**
   - Make sure Ollama is installed and running
   - Verify the model name in config.py matches an installed model

3. **"Agent not responding"**
   - Check `sts_agent.log` for error messages
   - Verify CommunicationMod is properly configured
   - Ensure the external command path is correct

### Debug Mode

Enable verbose logging by modifying the logging level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Development

### Adding New Commands
1. Update `validate_command()` in `nodes.py`
2. Add corresponding logic in `generate_fallback_command()`
3. Update test cases in `test_agent.py`

### Modifying LLM Prompts
Edit templates in `src/prompts/templates/` to customize the agent's reasoning.

### Extending Game Logic
Add new nodes in `nodes.py` and update the graph in `builder.py`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is open source. See the CommunicationMod license for mod-specific terms.

## Acknowledgments

- **CommunicationMod** by ForgottenArbiter - enables external AI control
- **Slay the Spire** by Mega Crit Games
- **LangChain/LangGraph** for the agent framework 