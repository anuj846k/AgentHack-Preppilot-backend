# Meeting Documentation Generator

This directory contains tools for generating detailed markdown documentation from meeting data, including attendee information from LinkedIn and GitHub profiles.

## Files

- `create_docs_summary.py` - Original script with error handling and fallback
- `create_docs_summary_simple.py` - Simplified version that bypasses Portia planning

## Issue: StepsOrError Validation Error

### Problem
The original script encounters a `StepsOrError` validation error in the Portia library:

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for StepsOrError
  Input should be a valid dictionary or instance of StepsOrError [type=model_type, input_value=None, input_type=NoneType]
```

This error occurs in the Portia planning agent when it tries to validate the response from the LLM. The model is returning `None` instead of a valid dictionary for the `StepsOrError` schema.

### Root Cause
This appears to be a bug in the Portia library (version 0.7.2+) where the planning agent's `generate_steps_or_error` method is not properly handling the LLM response validation.

### Solutions

#### 1. Error Handling with Fallback (create_docs_summary.py)
The modified version includes:
- Try-catch block around Portia's `run()` method
- Fallback to direct LLM calls using Portia's model interface
- Graceful error handling and user feedback

#### 2. Simplified Approach (create_docs_summary_simple.py)
A completely separate implementation that:
- Bypasses Portia's planning system entirely
- Uses direct LLM calls through Portia's model interface
- Maintains the same functionality without the planning overhead

## Usage

### Option 1: Try the original with fallback
```bash
python create_docs_summary.py
```

### Option 2: Use the simplified version
```bash
python create_docs_summary_simple.py
```

## Requirements

- Portia SDK Python >= 0.7.2
- Google API key configured in environment variables
- Python 3.13+

## Environment Variables

Make sure you have the following environment variables set:
- `GOOGLE_API_KEY` - Your Google AI API key

## Output

Both scripts generate a detailed markdown document containing:
- Meeting overview
- Attendee profiles with LinkedIn data
- GitHub insights
- Comparison tables
- Relevant insights from Perplexity

## Troubleshooting

If you encounter the StepsOrError validation error:
1. Try the simplified version (`create_docs_summary_simple.py`)
2. Check your API keys are properly configured
3. Ensure you have the latest version of the Portia SDK
4. Consider reporting the issue to the Portia team as it appears to be a library bug

