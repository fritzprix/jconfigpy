# Python 3 Migration Issues Found

## Summary
jconfigpy is a Python 2.7 codebase that requires migration to Python 3. Multiple compatibility issues have been identified across all core modules.

## Critical Issues by Category

### 1. Dictionary Methods (`.iteritems()`, `.iterkeys()`, `.itervalues()`)
**Location**: `jconfigpy/VariableMonitor.py:31`
- **Issue**: `kwargs.iteritems()` - In Python 3, only `.items()` works
- **Impact**: HIGH - Core variable iteration breaks

### 2. Print Statements (Python 2 syntax)
**Locations**:
- `jconfigpy/Config.py:105-106` - `print self._base_dir` and `print self._root`
- `jconfigpy/Config.py:141` - `print autogen_file`
- **Issue**: Python 2 print statements without parentheses
- **Impact**: HIGH - SyntaxError in Python 3

### 3. File Type Checking
**Locations**:
- `jconfigpy/Config.py:40, 48` - `isinstance(fp, file)`
- `jconfigpy/VariableMonitor.py:68` - `isinstance(fp, file)`
- **Issue**: `file` type doesn't exist in Python 3; use `io.IOBase` or check `hasattr(fp, 'write')`
- **Impact**: HIGH - Type checking fails

### 4. String Encoding in json.load()
**Location**: `jconfigpy/Config.py:71`
- **Issue**: `json.load(fp, encoding='utf-8')` - Python 3's json.load() doesn't accept encoding parameter
- **Impact**: MEDIUM - Will raise TypeError

### 5. raw_input() Function
**Locations**:
- `jconfigpy/Dialog.py:86` - `raw_input(...)`
- `jconfigpy/Dialog.py:112` - `raw_input(...)`
- `jconfigpy/Dialog.py:135` - `raw_input(...)`
- `jconfigpy/Dialog.py:168` - `raw_input(...)`
- **Issue**: `raw_input()` renamed to `input()` in Python 3
- **Impact**: HIGH - NameError in interactive mode

### 6. String Comparison using `is` operator
**Locations**:
- `jconfigpy/Dialog.py:37-46` - `if item_type is 'enum'`, etc.
- `jconfigpy/Dialog.py:88-89` - `if val is not ''`
- **Issue**: Should use `==` for string comparison, not `is` (identity check)
- **Impact**: MEDIUM - Logic errors (may work sometimes due to string interning)

### 7. Dict.keys() Iteration
**Locations**:
- `jconfigpy/Config.py:72` - `for key in config_json:`
- Multiple other locations
- **Issue**: Python 3 dict.keys() returns a view, not a list; may need list() wrapping in some contexts
- **Impact**: LOW-MEDIUM - Usually works but can cause issues with certain operations

### 8. Dict Constructor with iterable parameter
**Location**: `jconfigpy/Config.py:122`
- **Issue**: `dict(iterable=var_map)` - should be `dict(var_map)` or create new dict properly
- **Impact**: MEDIUM - May not initialize correctly

### 9. Exception Syntax (except as syntax)
**Locations**:
- `jconfigpy/Config.py:132` - `except Monitor as var_pub:`
- `jconfigpy/__main__.py:63` - `except Monitor as single_instance:`
- **Issue**: These try/except blocks are using exception classes incorrectly; should use instance checking
- **Impact**: MEDIUM - Logic error; exception handler won't work as intended

## File-by-File Breakdown

### `jconfigpy/VariableMonitor.py`
- ✗ Line 31: `.iteritems()` → `.items()`
- ✗ Line 68: `isinstance(fp, file)` → `isinstance(fp, io.IOBase)` or check `hasattr(fp, 'write')`

### `jconfigpy/Config.py`
- ✗ Line 40, 48: `isinstance(fp, file)` → fix file type check
- ✗ Line 71: `json.load(fp, encoding='utf-8')` → remove encoding parameter
- ✗ Line 105-106, 141: `print x` statements → `print(x)` function calls
- ✗ Line 122: `dict(iterable=var_map)` → `dict(var_map)` or fix initialization

### `jconfigpy/Dialog.py`
- ✗ Lines 37-46: `is 'string'` comparisons → `== 'string'`
- ✗ Lines 86, 112, 135, 168: `raw_input()` → `input()`
- ✗ Lines 88-89: `if val is not ''` → `if val != ''`

### `jconfigpy/__main__.py`
- ✗ Line 63: `except Monitor as single_instance:` → fix exception handling logic

### `jconfigpy/Item.py`
- Status: No obvious syntax issues found, but needs testing

### `jconfigpy/Recipe.py`
- Status: No obvious syntax issues found, but needs testing

### `jconfigpy/ErrorType.py`
- Status: Not reviewed yet

## Additional Considerations
1. **Relative Imports**: Code uses `from Config import JConfig` which should work with Python 3 but may need `from .Config import JConfig` if used as a package
2. **Python 2.7 shebang**: Line 1 of `__main__.py` uses `#!/usr/bin/python` - should be `#!/usr/bin/env python3`
3. **setup.py**: Likely needs update to specify python_requires='>=3.6'
