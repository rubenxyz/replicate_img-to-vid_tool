# Progress Bar Modes

The video generation tool now offers **THREE** progress modes:

## 1. Standard Mode (main.py)
- Basic Rich progress bar
- Suitable for simple use cases
- Minimal visual feedback

**Usage:**
```bash
python -m src.main
```

## 2. Epic Mode (main_verbose.py) - **DEFAULT**
- Rich progress with all epic features
- Panel wrapper, custom fields, cost tracking
- Professional appearance

**Usage:**
```bash
python run.py  # Uses this by default
python -m src.main_verbose
```

## 3. Hybrid Mode (main_hybrid.py) - **RECOMMENDED** 🌊
- **alive-progress WAVES animation** during API polling
- **Rich console logging** for detailed operations
- Maximum visual impact (manifesto recommended)

**Usage:**
```bash
python -m src.main_hybrid
```

## Recommendation

For the best experience with maximum visual appeal, use **Hybrid Mode**:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with WAVES animation
python -m src.main_hybrid
```

You'll see beautiful WAVES animations during video generation! 🌊
