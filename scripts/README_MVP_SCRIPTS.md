# MVP Preparation Scripts

This set of scripts automates the process of preparing the codebase for an MVP by removing custom exceptions and simplifying error handling.

## Overview

The MVP preparation process involves:

1. Removing custom exception imports from repository files
2. Replacing exception raising with logging and appropriate default returns
3. Simplifying try/except blocks that use custom exceptions
4. Adding `extend_existing=True` to all SQLAlchemy models to prevent redefinition errors

## Scripts

The repository contains the following scripts for MVP preparation:

- `prepare_mvp.py`: Main orchestration script that runs all other scripts in sequence
- `remove_exceptions_for_mvp.py`: Removes exception imports and basic raises
- `fix_remaining_exceptions.py`: Fixes more complex exception raise patterns
- `fix_try_except_blocks.py`: Fixes try/except blocks with custom exceptions

## Prerequisites

Before running the scripts, ensure you have the required package:

```bash
pip install astunparse
```

This package is used for parsing and analyzing Python code to accurately detect and replace exception patterns.

## Usage

Run the main script to automate the entire MVP preparation process:

```bash
python scripts/prepare_mvp.py
```

This will:
1. Install required packages (if needed)
2. Run all the exception removal scripts in sequence
3. Check for any remaining exceptions in the codebase
4. Log the entire process to `mvp_preparation.log`

### Running Individual Scripts

You can also run individual scripts if needed:

```bash
python scripts/remove_exceptions_for_mvp.py
python scripts/fix_remaining_exceptions.py
python scripts/fix_try_except_blocks.py
```

## What the Scripts Do

### remove_exceptions_for_mvp.py

- Removes custom exception imports from repository files
- Adds logging imports and setup
- Replaces basic exception raises with logging and appropriate returns
- Adds `extend_existing=True` to all SQLAlchemy models

### fix_remaining_exceptions.py

- Uses AST parsing to find complex exception raise patterns
- Analyzes method return types to determine appropriate default values
- Replaces exception raises with logging and appropriate returns

### fix_try_except_blocks.py

- Finds try/except blocks that catch custom exceptions
- Replaces them with generic exception handling
- Adds appropriate logging and return statements

## Logging

All scripts write detailed logs to help track the changes made to the codebase. The main script logs to both the console and `mvp_preparation.log`.

## After Running

After running the scripts, check the log files for any warnings or errors. Some manual cleanup may still be required for complex edge cases.

## Manual Verification

It's recommended to manually verify the changes, especially for:

1. Methods with complex return logic
2. Nested try/except blocks
3. Areas where the script indicates warnings or potential issues

## Reverting Changes

If needed, you can revert the changes using git:

```bash
git checkout -- app/repositories/
git checkout -- app/models/
```
