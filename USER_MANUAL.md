# jconfigpy User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Configuration File Format](#configuration-file-format)
5. [Configuration Types](#configuration-types)
6. [Hierarchical Configuration](#hierarchical-configuration)
7. [CLI Usage](#cli-usage)
8. [Integration with GNU Make](#integration-with-gnu-make)
9. [Advanced Features](#advanced-features)
10. [Examples](#examples)
11. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is jconfigpy?

jconfigpy is a **JSON-based configuration utility** for C/C++ projects using GNU Make as the build system. It provides a way to manage complex build configurations through distributed, hierarchical configuration files instead of scattered macro definitions.

### Why jconfigpy?

**Problem with traditional macro-based configuration:**
```c
// Many scattered #define statements make code hard to read
#ifdef CONFIG_USE_MMU
  // ...
#endif
#ifdef CONFIG_USE_DMA
  // ...
#endif
// Becomes unmaintainable with many configs...
```

**jconfigpy Solution:**
- ✅ Centralized configuration management
- ✅ Distributed config files (one per directory)
- ✅ JSON format (human-readable and familiar)
- ✅ Automatic dependency resolution
- ✅ Generates preprocessor macros and Makefiles
- ✅ Interactive or automated configuration

### Key Features

1. **JSON-Based**: Easy to read and write configuration schemas
2. **Hierarchical**: Nested configurations for complex projects
3. **Distributed**: Configuration files in relevant directories
4. **Dependency Resolution**: Automatic handling of configuration dependencies
5. **Git Integration**: Support for git-based module dependencies
6. **Make-Compatible**: Seamless integration with GNU Make
7. **Python 3.6+**: Modern Python implementation

---

## Installation

### From PyPI (Recommended)

```bash
pip install jconfigpy
```

### From Source

```bash
git clone https://github.com/fritzprix/jconfigpy.git
cd jconfigpy
pip install -e .
```

### Verify Installation

```bash
python3 -m jconfigpy --help
```

---

## Quick Start

### 1. Create a Basic Configuration File

Create `config.json` in your project root:

```json
{
  "ARCH": {
    "type": "enum",
    "default": 0,
    "enum": ["ARM", "x86"],
    "prompt": "Select target architecture",
    "help": ["Choose the CPU architecture for your project"]
  },
  "ENABLE_DEBUG": {
    "type": "bool",
    "default": "y",
    "prompt": "Enable debug mode",
    "help": ["Enables debug symbols and logging"]
  }
}
```

### 2. Interactive Configuration

```bash
python3 -m jconfigpy -c -i config.json -o .config
```

This will:
- Present each configuration option interactively
- Save selections to `.config` file
- Generate `autogen.h` with macro definitions

### 3. Load Existing Configuration

```bash
python3 -m jconfigpy -s -i .config -t config.json -o .config -g autogen.h
```

### 4. Use in Makefile

```makefile
# Include generated configuration
include .config

# Include recipes (build rules for modules)
include $(RECIPES)

# Use configuration variables
ifeq ($(CONFIG_ENABLE_DEBUG), y)
  CFLAGS += -g -O0
else
  CFLAGS += -O2
endif
```

---

## Configuration File Format

### File Structure

Each `config.json` contains a JSON object with configuration items as properties:

```json
{
  "CONFIG_ITEM_NAME": {
    "type": "enum|bool|int|hex|string|tristate|config|recipe|repo",
    "default": "default_value",
    "prompt": "User-facing description",
    "help": ["Help text line 1", "Help text line 2"],
    "depends": {"OTHER_CONFIG": "required_value"},
    "gen-list": {"MACRO_NAME": "to_string(this)"}
  }
}
```

### Common Properties

| Property | Type | Description |
|----------|------|-------------|
| `type` | string | Configuration item type (required) |
| `default` | varies | Default value (0-based index for enum, y/n for bool, etc.) |
| `prompt` | string | User-facing description shown during configuration |
| `help` | array | Help text lines explaining the option |
| `depends` | object | Dependency constraints (only show if conditions met) |
| `gen-list` | object | Mapping of generated macro names to values |
| `import` | boolean | Whether to load nested configs from subdirectories |

---

## Configuration Types

### 1. Boolean (`bool`)

Binary choice: yes/no (y/n)

```json
{
  "CONFIG_USE_MMU": {
    "type": "bool",
    "default": "y",
    "prompt": "Use Memory Management Unit",
    "help": ["Enable MMU for virtual memory support"]
  }
}
```

**Generated macro**: `CONFIG_USE_MMU=y` or `CONFIG_USE_MMU=n`

### 2. Enumeration (`enum`)

Multiple choice selection

```json
{
  "ARCH": {
    "type": "enum",
    "default": 0,
    "enum": ["ARM", "x86", "MIPS"],
    "prompt": "Target Architecture",
    "help": ["Select the CPU architecture"]
  }
}
```

**Generated macro**: `CONFIG_ARCH=ARM` (selected choice)

### 3. Integer (`int`)

Numeric value with optional range

```json
{
  "CONFIG_PAGE_SIZE": {
    "type": "int",
    "default": 4096,
    "prompt": "Memory page size in bytes",
    "help": ["Typical values: 4096 (4KB) or 8192 (8KB)"]
  }
}
```

**Generated macro**: `CONFIG_PAGE_SIZE=4096`

### 4. Hexadecimal (`hex`)

Hexadecimal numeric value

```json
{
  "CONFIG_STACK_LIMIT": {
    "type": "hex",
    "default": "0x2000000",
    "prompt": "Stack memory limit",
    "help": ["Hexadecimal address or size"]
  }
}
```

**Generated macro**: `CONFIG_STACK_LIMIT=0x2000000`

### 5. String (`string`)

Arbitrary text value

```json
{
  "CONFIG_PROJECT_NAME": {
    "type": "string",
    "default": "MyProject",
    "prompt": "Project name",
    "help": ["Displayed in output and logs"]
  }
}
```

**Generated macro**: `CONFIG_PROJECT_NAME=MyProject`

### 6. Tristate (`tristate`)

Three-state choice: yes/no/module (y/n/m)

```json
{
  "CONFIG_DRIVER_USB": {
    "type": "tristate",
    "default": "n",
    "prompt": "USB Driver support",
    "help": ["y=built-in, n=disabled, m=module"]
  }
}
```

**Generated macro**: `CONFIG_DRIVER_USB=y|n|m`

### 7. Nested Configuration (`config`)

Include configuration from another file

```json
{
  "SOC_VENDOR": {
    "type": "config",
    "prompt": "Select SOC vendor",
    "path": "./hal/$SOC_VENDOR/config.json"
  }
}
```

**Features:**
- `path` can contain variables like `$ARCH`, `$SOC_VENDOR`
- Allows hierarchical configuration organization
- Path resolved based on parent configuration values

### 8. Recipe (`recipe`)

Makefile generation for module-specific build rules

```json
{
  "CDSL": {
    "type": "recipe",
    "path": "./cdsl/recipe.mk"
  }
}
```

**Generated file**: `.config` will include `-include ./cdsl/recipe.mk`

### 9. Repository (`repo`)

Git repository dependency

```json
{
  "EXAMPLE_MODULE": {
    "type": "repo",
    "prompt": "Example Module",
    "url": "https://github.com/user/example-module.git",
    "path": "./modules/example",
    "depends": {"CONFIG_ENABLE_MODULES": "y"}
  }
}
```

---

## Hierarchical Configuration

### Directory Structure Example

```
project/
├── config.json                 # Root configuration
├── .config                     # Generated configuration
├── Makefile
├── arch/
│   ├── config.json            # Architecture selection
│   ├── ARM/
│   │   ├── config.json        # ARM-specific options
│   │   ├── cortex-m4/
│   │   │   └── config.json    # Cortex-M4 specific
│   │   └── module/
│   │       ├── config.json    # Module configuration
│   │       └── recipe.mk      # Module build rules
│   └── x86/
│       └── config.json
├── hal/
│   ├── config.json            # HAL selection
│   └── ST_Micro/
│       ├── config.json
│       ├── STM32F401/
│       │   ├── config.json
│       │   └── recipe.mk
│       └── STM32F201/
│           ├── config.json
│           └── recipe.mk
└── kernel/
    ├── config.json
    ├── mm/
    │   ├── config.json
    │   ├── mmu/
    │   │   └── config.json
    │   └── nommu/
    │       └── config.json
```

### Variable Substitution

Variables in paths are resolved dynamically:

**Root config.json:**
```json
{
  "ARCH": {
    "type": "enum",
    "default": 0,
    "enum": ["ARM", "x86"],
    "import": true
  }
}
```

**arch/config.json:**
```json
{
  "SUB_ARCH": {
    "type": "config",
    "path": "./$ARCH/config.json"
  }
}
```

When `ARCH=ARM` is selected, it loads `./ARM/config.json`

### Dependency Resolution

**Example: Show option only if condition is met**

```json
{
  "SOC_NAME": {
    "type": "config",
    "prompt": "Select SOC",
    "path": "./$SOC_VENDOR/$SOC_NAME/config.json",
    "depends": {"SOC_VENDOR": "ST_Micro"}
  }
}
```

The `SOC_NAME` option only appears if `SOC_VENDOR` is set to `ST_Micro`

---

## CLI Usage

### Command Syntax

```bash
python3 -m jconfigpy [OPTIONS]
```

### Options

| Option | Argument | Description |
|--------|----------|-------------|
| `-c` | none | Create new configuration (interactive) |
| `-s` | none | Load/update existing configuration |
| `-i` | file | Input file (config source or saved config) |
| `-o` | file | Output file (default: `.config`) |
| `-t` | file | Template/target config file |
| `-g` | file | Generate C header file with macros |
| `-u` | t/g | UI type: `t` for text (default), `g` for GUI |

### Examples

**Interactive configuration creation:**
```bash
python3 -m jconfigpy -c -i config.json -o .config -g autogen.h
```

**Load and update existing configuration:**
```bash
python3 -m jconfigpy -s -i .config -t config.json -o .config -g autogen.h
```

**Configuration only without header generation:**
```bash
python3 -m jconfigpy -c -i config.json -o .config
```

**Update configuration without overwriting:**
```bash
python3 -m jconfigpy -s -i .config -t config.json -o .config.updated
```

---

## Integration with GNU Make

### Basic Makefile Integration

```makefile
# Configuration target
.config:
	python3 -m jconfigpy -c -i config.json -o .config -g autogen.h

# Include configuration
-include .config

# Use configuration variables
ifdef CONFIG_USE_MMU
  CFLAGS += -DUSE_MMU
endif

# Conditional compilation
ifeq ($(CONFIG_ARCH), ARM)
  ARCH_SRC = arch/arm.c
else
  ARCH_SRC = arch/x86.c
endif

build: .config
	gcc $(CFLAGS) -c $(ARCH_SRC)
	gcc $(CFLAGS) -c main.c
```

### Advanced Makefile Integration

```makefile
# Generate configuration if .config doesn't exist
.config: config.json
	python3 -m jconfigpy -c -i config.json -o .config -g autogen.h

# Recipe files from subdirectories
RECIPES := $(shell grep -r "recipe.mk" . | cut -d: -f1 | sort -u)

# Include generated configuration and recipes
-include .config
-include $(RECIPES)

# Build target dependencies based on config
ifdef CONFIG_ENABLE_DEBUG
  DEBUG_OBJS = debug/symbols.o debug/trace.o
  CFLAGS += -g -O0
endif

# Architecture-specific targets
TARGET_ARCH = $(subst CONFIG_ARCH_,,$(filter CONFIG_ARCH_%,$(.VARIABLES)))
ARCH_OBJS = arch/$(TARGET_ARCH)/startup.o

# Build rule
all: $(ARCH_OBJS) $(DEBUG_OBJS) main.o
	gcc -o application $^
```

### Recipe.mk Example

**hal/ST_Micro/STM32F401/recipe.mk:**
```makefile
# STM32F401 HAL build rules
STM32F401_OBJS = \
  hal/ST_Micro/STM32F401/startup.o \
  hal/ST_Micro/STM32F401/clock.o \
  hal/ST_Micro/STM32F401/uart.o

STM32F401_CFLAGS = -DSTM32F401 -march=armv7e-m

# Generated configuration includes this file
ifdef CONFIG_SOC_STM32F401
  OBJS += $(STM32F401_OBJS)
  CFLAGS += $(STM32F401_CFLAGS)
endif
```

---

## Advanced Features

### 1. Automatic Macro Generation

**Configuration:**
```json
{
  "CONFIG_PAGE_SIZE": {
    "type": "int",
    "default": 4096,
    "gen-list": {
      "PAGE_SIZE": "to_int(this)",
      "PAGE_SIZE_SHIFTED": "to_int(this) >> 12"
    }
  }
}
```

**Generated header (autogen.h):**
```c
#define PAGE_SIZE 4096
#define PAGE_SIZE_SHIFTED 1
```

### 2. Conditional Visibility

Options can be shown/hidden based on other selections:

```json
{
  "ARCH": {
    "type": "enum",
    "default": 0,
    "enum": ["ARM", "x86"]
  },
  "ARM_CORTEX_VERSION": {
    "type": "enum",
    "prompt": "ARM Cortex Version",
    "enum": ["M0", "M3", "M4"],
    "depends": {"ARCH": "ARM"}
  },
  "X86_FAMILY": {
    "type": "enum",
    "prompt": "x86 Family",
    "enum": ["i386", "i586", "i686"],
    "depends": {"ARCH": "x86"}
  }
}
```

### 3. Git Repository Dependencies

```json
{
  "CDSL_MODULE": {
    "type": "repo",
    "prompt": "Include CDSL Library",
    "url": "https://github.com/fritzprix/cdsl.git",
    "path": "./libs/cdsl"
  }
}
```

jconfigpy will automatically:
- Clone the repository if not present
- Keep it updated on configuration reload

### 4. Variable Substitution in Paths

Paths can reference configuration values:

```json
{
  "ARCH": {
    "type": "enum",
    "enum": ["ARM", "x86"]
  },
  "VENDOR": {
    "type": "config",
    "path": "./$ARCH/vendor/config.json"
  }
}
```

Supported variables: Any `CONFIG_*` item in current or parent configs

---

## Examples

### Example 1: Simple Embedded System

**config.json:**
```json
{
  "CPU_ARCH": {
    "type": "enum",
    "default": 0,
    "enum": ["ARM", "MIPS"],
    "prompt": "Select CPU Architecture",
    "help": ["Choose the target processor architecture"]
  },
  "ENABLE_FPU": {
    "type": "bool",
    "default": "y",
    "prompt": "Enable Floating Point Unit",
    "help": ["Enables hardware floating point support"],
    "gen-list": {"FPU_SUPPORT": "to_bool(this)"}
  },
  "HEAP_SIZE": {
    "type": "hex",
    "default": "0x10000",
    "prompt": "Heap Size",
    "help": ["Initial heap memory size in bytes"]
  }
}
```

**Makefile:**
```makefile
.config: config.json
	python3 -m jconfigpy -c -i config.json -o .config -g autogen.h

-include .config

CFLAGS = -Wall -Werror

ifeq ($(CONFIG_CPU_ARCH), ARM)
  CFLAGS += -mcpu=cortex-m4
else ifeq ($(CONFIG_CPU_ARCH), MIPS)
  CFLAGS += -march=mips32
endif

all: .config main.o
	gcc $(CFLAGS) -o app main.o
```

### Example 2: Hierarchical SOC Selection

**config.json:**
```json
{
  "ARCH": {
    "type": "enum",
    "enum": ["ARM", "x86"],
    "default": 0,
    "import": true
  }
}
```

**arch/config.json:**
```json
{
  "VENDOR": {
    "type": "enum",
    "enum": ["ST_Micro", "NXP", "TI"],
    "prompt": "Select vendor"
  },
  "SOC_MODEL": {
    "type": "config",
    "path": "./$VENDOR/config.json"
  }
}
```

**arch/ST_Micro/config.json:**
```json
{
  "CHIP": {
    "type": "enum",
    "enum": ["STM32F401", "STM32H743"],
    "prompt": "Select STM32 chip"
  }
}
```

### Example 3: Using Recipes for Module Build Rules

**Makefile:**
```makefile
RECIPES := $(shell find . -name "recipe.mk" -type f)

.config: config.json
	python3 -m jconfigpy -c -i config.json -o .config

-include .config
-include $(RECIPES)

all: application

application: $(CONFIG_OBJS)
	gcc -o application $^
```

**subdirectory/config.json:**
```json
{
  "ENABLE_MODULE": {
    "type": "bool",
    "default": "y",
    "prompt": "Include this module",
    "gen-list": {"MODULE_ENABLED": "to_bool(this)"}
  },
  "MODULE_RECIPE": {
    "type": "recipe",
    "path": "./recipe.mk"
  }
}
```

**subdirectory/recipe.mk:**
```makefile
ifdef CONFIG_ENABLE_MODULE
  MODULE_OBJS = subdirectory/module.o subdirectory/helper.o
  CONFIG_OBJS += $(MODULE_OBJS)
  CFLAGS += -DMODULE_ENABLED
endif
```

---

## Troubleshooting

### Issue 1: "ImportError: No module named jconfigpy"

**Solution:**
```bash
# Install the package
pip install jconfigpy

# Or use development version
export PYTHONPATH=/path/to/jconfigpy:$PYTHONPATH
python3 -m jconfigpy ...
```

### Issue 2: "config.json doesn't exist"

**Solution:**
- Verify the path: `ls -la config.json`
- Use absolute paths: `python3 -m jconfigpy -i /absolute/path/config.json`
- Check current working directory: `pwd`

### Issue 3: Configuration file has invalid JSON

**Solution:**
```bash
# Validate JSON
python3 -m json.tool config.json
```

### Issue 4: Variables not resolving in paths

**Solution:**
- Variable names must match exactly (case-sensitive)
- Variables must be defined in current or parent config
- Use `$VARIABLE_NAME` syntax (with $)

Example:
```json
{
  "ARCH": {
    "type": "enum",
    "enum": ["ARM", "x86"]
  },
  "HAL": {
    "type": "config",
    "path": "./hal/$ARCH/config.json"  // ✅ Correct
  }
}
```

### Issue 5: Module appears selected but generation fails

**Possible causes:**
1. Recipe file path is incorrect
2. Recipe file doesn't exist
3. JSON syntax error in config

**Solution:**
```bash
# Check recipe file exists
ls -la path/to/recipe.mk

# Validate JSON structure
python3 -c "import json; json.load(open('config.json'))"
```

### Issue 6: Test failures when running test_jconfigpy.sh

**Solution:**
```bash
# Run development version test
cd /path/to/jconfigpy
./test_jconfigpy.sh

# Run with installed version
./test_jconfigpy.sh --use-installed

# Cleanup test files
./test_jconfigpy.sh --cleanup-only
```

---

## Configuration Best Practices

### 1. Use Descriptive Names

```json
{
  "CONFIG_USE_MMU": {
    "prompt": "Enable Memory Management Unit",
    "help": ["Required for virtual memory and process isolation"]
  }
}
```

### 2. Organize by Directory

Each subdirectory should have its own `config.json`:
```
project/
├── arch/config.json          # Architecture selection
├── hal/config.json           # Hardware abstraction layer
├── kernel/config.json        # Kernel options
├── driver/config.json        # Driver options
└── app/config.json           # Application options
```

### 3. Use Dependencies

```json
{
  "DRIVER_UART": {
    "type": "tristate",
    "prompt": "UART Driver"
  },
  "UART_BAUDRATE": {
    "type": "enum",
    "enum": [9600, 19200, 115200],
    "prompt": "UART Baudrate",
    "depends": {"DRIVER_UART": "y"}
  }
}
```

### 4. Document Options

```json
{
  "CONFIG_STACK_SIZE": {
    "type": "int",
    "default": 8192,
    "prompt": "Stack size in bytes",
    "help": [
      "Size of the main stack.",
      "Typical values:",
      "  - 4096: Minimal systems",
      "  - 8192: Standard systems",
      "  - 16384: Complex systems"
    ]
  }
}
```

### 5. Use Meaningful Defaults

```json
{
  "CONFIG_DEBUG": {
    "type": "bool",
    "default": "n",
    "prompt": "Enable debug mode",
    "help": ["Adds debug symbols and logging"]
  },
  "CONFIG_OPTIMIZE": {
    "type": "enum",
    "default": 1,
    "enum": ["O0", "O1", "O2", "O3"],
    "prompt": "Optimization level",
    "depends": {"CONFIG_DEBUG": "n"}
  }
}
```

---

## Further Reading

- **Linux Kconfig**: https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html
- **GNU Make**: https://www.gnu.org/software/make/manual/
- **JSON Format**: https://www.json.org/

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `./test_jconfigpy.sh` to verify
5. Submit a pull request

**GitHub**: https://github.com/fritzprix/jconfigpy

---

## License

MIT License - See LICENSE file for details

Copyright (c) 2015-2025 DooWoong Lee

---

## Support

- **Issues**: https://github.com/fritzprix/jconfigpy/issues
- **Email**: innocentevil0914@gmail.com
