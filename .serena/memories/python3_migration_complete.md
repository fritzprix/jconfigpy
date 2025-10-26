# Python 3 Migration - Complete Issues List

## High Priority Issues (SyntaxError/RuntimeError)

### 1. Dictionary `.iteritems()` Method
**File**: `jconfigpy/VariableMonitor.py:31`
```python
for key, val in kwargs.iteritems():  # ❌ Python 2
```
**Fix**: Use `.items()` instead
```python
for key, val in kwargs.items():  # ✓ Python 3
```

### 2. Print Statements (No parentheses)
**Files**: 
- `jconfigpy/Config.py:105, 106, 141`
- Multiple locations in other files

**Issue**: Python 2 `print` is a statement, Python 3 uses function syntax
```python
print self._base_dir  # ❌ SyntaxError
print autogen_file   # ❌ SyntaxError
```
**Fix**:
```python
print(self._base_dir)  # ✓ Works in both Python 2.6+ and 3
print(autogen_file)
```

### 3. File Type Checking with `isinstance(fp, file)`
**Files**:
- `jconfigpy/Config.py:40, 48`
- `jconfigpy/VariableMonitor.py:68`

**Issue**: `file` type doesn't exist in Python 3
```python
if not isinstance(fp, file):  # ❌ NameError: name 'file' is not defined
```
**Fix**: Use `io.IOBase` or duck typing
```python
import io
if not isinstance(fp, io.IOBase):  # ✓ Works in Python 3
# OR
if not hasattr(fp, 'write'):  # ✓ Duck typing approach
```

### 4. JSON Encoding Parameter
**Files**:
- `jconfigpy/Config.py:71`
- `jconfigpy/Recipe.py:102`

**Issue**: `encoding` parameter removed from `json.load()` in Python 3
```python
config_json = json.load(fp, encoding='utf-8')  # ❌ TypeError
package_json = json.load(fp, encoding='utf-8')  # ❌ TypeError
```
**Fix**: Remove the parameter (Python 3 uses UTF-8 by default for text files)
```python
config_json = json.load(fp)  # ✓ Python 3
package_json = json.load(fp)  # ✓ Python 3
```

### 5. `raw_input()` Function
**Files**:
- `jconfigpy/Dialog.py:86, 112, 135, 168, 189, 215, 238`

**Issue**: `raw_input()` renamed to `input()` in Python 3
```python
val = raw_input('{0} (0 ~ {1}) : '.format(...))  # ❌ NameError
```
**Fix**: Use `input()` (or import compatibility shim)
```python
val = input('{0} (0 ~ {1}) : '.format(...))  # ✓ Python 3
```

## Medium Priority Issues (Logic Errors)

### 6. String Identity Comparison using `is`
**Files**:
- `jconfigpy/Dialog.py:37-46` - Comparing item_type with strings using `is`
- `jconfigpy/Dialog.py:88-89` - Comparing with empty string using `is not`

**Issue**: Should use `==` for value comparison, not `is` (identity check)
```python
if item_type is 'enum':      # ❌ Works sometimes due to string interning, unreliable
if val is not '':            # ❌ Should use !=
```
**Fix**:
```python
if item_type == 'enum':      # ✓ Correct value comparison
if val != '':               # ✓ Correct
```

### 7. Dict Constructor with `iterable` parameter
**File**: `jconfigpy/Config.py:122`
```python
self._var_map = dict(iterable=var_map)  # ❌ Invalid
```
**Fix**:
```python
self._var_map = dict(var_map) if var_map else {}  # ✓ Correct
```

### 8. Incorrect Exception Handling
**Files**:
- `jconfigpy/Config.py:132`
- `jconfigpy/__main__.py:63, 146`

**Issue**: Trying to catch exception class, not instance
```python
try:
    self._var_pub = Monitor()
except Monitor as var_pub:  # ❌ Wrong - Monitor is being caught as exception
    self._var_pub = var_pub
```
**Fix**: Should check if already initialized or use proper singleton pattern
```python
try:
    self._var_pub = Monitor()
except RuntimeError:  # Monitor raises RuntimeError if already instantiated
    self._var_pub = Monitor._SINGLE_OBJECT  # Get the existing instance
```

## Minor Issues (Code Quality)

### 9. Relative Imports
**All files**: Use relative imports for package imports
```python
from Config import JConfig           # ❌ Works in Python 2, may fail in Python 3 packages
from .Config import JConfig          # ✓ Proper relative import
```

### 10. Enumerate on Dictionary Keys
**Files**:
- `jconfigpy/Item.py:125` - `for var in enumerate(self._depend):`
- `jconfigpy/Item.py:139` - `for var in enumerate(self._depend):`
- `jconfigpy/Config.py:161-162` - `for upath in enumerate(self._unresolved_path):`
- `jconfigpy/Config.py:165` - `for var in enumerate(self._var_map):`

**Issue**: `enumerate()` returns tuples `(index, value)`, but code expects just the key
```python
for var in enumerate(self._depend):  # ❌ var is (0, 'KEY_NAME'), not 'KEY_NAME'
    self._var_pub.subscribe_variable_change(var, self)  # ❌ Passes tuple instead of key
```
**Fix**:
```python
for var in self._depend:  # ✓ Correct - iterate over dict keys
    self._var_pub.subscribe_variable_change(var, self)
```

### 11. Python 2.7 Shebang
**File**: `jconfigpy/__main__.py:1`
```python
#!/usr/bin/python  # ❌ Points to Python 2
```
**Fix**:
```python
#!/usr/bin/env python3  # ✓ Python 3 compatible
```

### 12. Setup.py Version Specification
**File**: `setup.py`
- Currently no `python_requires` specification
**Fix**: Add to setup.py
```python
python_requires='>=3.6',
```

## Summary Table

| Issue | Severity | Files | Count |
|-------|----------|-------|-------|
| `.iteritems()` | HIGH | 1 | 1 |
| Print statements | HIGH | 3 | 4 |
| `isinstance(fp, file)` | HIGH | 2 | 3 |
| JSON encoding param | HIGH | 2 | 2 |
| `raw_input()` | HIGH | 1 | 7 |
| String `is` comparison | MEDIUM | 1 | 6+ |
| Dict constructor | MEDIUM | 1 | 1 |
| Exception handling | MEDIUM | 2 | 3 |
| Relative imports | MINOR | 8 | Many |
| `enumerate()` on dict | MINOR | 3 | 4 |
| Shebang | MINOR | 1 | 1 |

**Total High Priority**: 18 issues
**Total Medium Priority**: 8 issues  
**Total Minor Priority**: 11+ issues
