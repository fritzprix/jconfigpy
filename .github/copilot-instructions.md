# jconfigpy AI Coding Guidelines

## Project Overview
jconfigpy is a JSON-based configuration system inspired by Linux kernel's kconfig. It manages hierarchical build configurations for C/C++ projects using GNU Make, enabling distributed configuration files and dependency resolution.

## Core Architecture

### Configuration Hierarchy
- **Entry Point**: Root `config.json` files define configuration schemas
- **Nested Configs**: `"type": "config"` entries create hierarchical structures via `path` property
- **Variable Substitution**: Paths use `$VARIABLE` syntax (e.g., `"./$ARCH/config.json"`)
- **Dependencies**: Items can depend on other configuration values for conditional visibility

### Key Classes & Responsibilities
- `JConfig`: Main configuration parser and container, handles nested config loading
- `JConfigItem` subclasses: Type-specific configuration items (enum, bool, int, hex, string, tristate)
- `Monitor`: Singleton variable tracker with pub/sub for dependency updates
- `JConfigRecipe`: Manages Makefile inclusion paths with variable resolution
- `Dialog/CMDDialog`: Interactive configuration interfaces

### Configuration Item Types
```python
# Supported types in config.json:
"type": "enum"      # Multiple choice selection
"type": "bool"      # y/n boolean values  
"type": "int"       # Integer with optional range
"type": "hex"       # Hexadecimal values
"type": "string"    # String values
"type": "tristate"  # y/n/m (yes/no/module) 
"type": "config"    # Nested configuration reference
"type": "recipe"    # Makefile inclusion
"type": "repo"      # Git repository dependency
```

## Development Patterns

### Configuration Schema Structure
Every `config.json` follows this pattern:
```json
{
  "CONFIG_NAME": {
    "type": "enum|bool|int|hex|string|tristate|config|recipe",
    "default": "default_value",
    "prompt": "User-facing description",
    "help": ["Help text lines"],
    "depends": {"OTHER_CONFIG": "required_value"},
    "gen-list": {"MACRO_NAME": "to_string(this)"}
  }
}
```

### File Generation
- **Header Generation**: `gen-list` creates C preprocessor macros via `write_genlist()`
- **Recipe Generation**: Recipe items generate Makefile includes via `write_recipe()`  
- **Config Output**: Variables saved in Make-compatible format (`CONFIG_VAR=value`)

### Variable Resolution System
- All config items use `Monitor` singleton for variable tracking
- Path resolution happens via `resolve_path()` replacing `$VAR` with actual values
- Dependencies trigger visibility recalculation through pub/sub notifications

## Build & Usage Workflows

### Interactive Configuration
```bash
# Start configuration from root config.json
python jconfigpy -c -i config.json -o .config

# Load existing configuration  
python jconfigpy -s -i .config -t config.json -g autogen.h
```

### Makefile Integration
Projects include generated files:
```makefile
-include .config          # Load configuration variables
include $(recipe_files)   # Include recipe.mk files
```

## Key Implementation Details

### Error Handling
- `FileNotExistError`: Custom exception for missing config files
- Path validation occurs before file operations
- Graceful fallbacks to default values when user values unavailable

### Variable Scoping
- All variables are global via `Monitor` singleton
- Child configurations inherit parent variable context
- Variable updates propagate to dependent items automatically

### Code Organization
- Main module entry via `__main__.py` with CLI argument parsing
- Item types separated into individual classes in `Item.py`
- Configuration parsing centralized in `Config.py`
- UI abstraction through `Dialog` base class

## Testing & Examples
- `example/` directory contains complete project structure demonstration
- Hierarchical configs show arch -> vendor -> SoC selection pattern
- Makefile demonstrates integration with generated variables and recipes

## Common Pitfalls
- Ensure proper variable names in `$VARIABLE` path references
- Recipe paths must be resolvable after variable substitution  
- Monitor singleton pattern requires careful initialization
- Python 2.7 compatibility constraints (legacy codebase)