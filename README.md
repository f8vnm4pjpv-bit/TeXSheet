# TeXSheet

A spreadsheet and graphing tool designed for scientific reports. TeXSheet combines Excel-like data editing, formula-based calculations, graph generation, and seamless LaTeX integration—enabling efficient creation of professional scientific documents.

## Overview

TeXSheet provides a unified environment for:
- **Spreadsheet editing** with formula support
- **Data visualization** with interactive graph configuration
- **LaTeX document generation** with automatic table and figure export

Perfect for researchers, scientists, and technical writers who need to maintain data integrity while producing publication-ready documents.

## Features

### 📊 Spreadsheet Editor
- **Excel-like interface** with intuitive tab-based multi-table support
- **Dynamic table management**: insert/delete/reorder rows and columns
- **Cell editing** with real-time updates
- **Column metadata**: customizable display names and internal names for formulas
- **Undo/Redo** support (50-level history)

### 🧮 Formula System
- **Formula-based calculations** with intelligent completion
- **Mathematical operators**: `+`, `-`, `*`, `/`, `^` (exponentiation), `**`
- **Column references**: use column names in formulas
- **Cross-table references**: reference data from other tables
- **Constants**: define reusable values across your project
- **Error handling**: robust evaluation with detailed error reporting

### 📈 Graph Generation
- **Interactive graph configuration** with preview
- **Multiple graph types**: line, scatter, bar, and more (via Matplotlib)
- **Series customization**: add/edit/remove data series
- **Axis control**: manual range, logarithmic scale, custom labels
- **Trend lines**: add approximation curves to series
- **PDF export**: generate publication-ready graph images

### 📄 LaTeX Integration
- **Direct LaTeX export**: convert tables to `.tex` files
- **Configurable table styling**: booktabs and other border styles
- **Captions and labels**: full LaTeX referencing support
- **Automatic compilation** (optional): generate final PDF documents
- **Project organization**: automatic directory structure for tables and figures

### 💾 Data Management
- **CSV import**: load data from standard spreadsheet formats
- **YAML configuration**: all settings in version-controllable text files
- **Project persistence**: automatic save and recovery
- **Configuration normalization**: handles missing or invalid settings gracefully

## Installation

### Requirements
- Python 3.8+
- Dependencies: `pandas`, `matplotlib`, `PySide6`, `pyyaml`

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/f8vnm4pjpv-bit/TeXSheet.git
   cd TeXSheet
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run TeXSheet:
   ```bash
   python app.py
   ```

## Quick Start

### Basic Workflow

1. **Import your data**
   - Place CSV files in the `tables_data/` directory
   - Configure input paths in `config.yaml`

2. **Edit and enhance**
   - Open TeXSheet and edit table data
   - Add formulas to calculate derived values
   - Create visualization configurations

3. **Generate outputs**
   - Export tables as LaTeX `.tex` files
   - Generate graphs as PDF images
   - Optionally compile full LaTeX documents

### Project Structure

```
project/
├── config.yaml              # Main configuration file
├── tables_data/             # CSV input files
│   └── table1.csv
├── tables/                  # Generated LaTeX table files
│   └── table1.tex
└── figures/                 # Generated graph PDFs
    └── result_graph.pdf
```

### Configuration Example

```yaml
tables:
  - id: table1
    name: "Experiment Results"
    input_csv: "tables_data/table1.csv"
    output_tex: "tables/table1.tex"
    caption: "Results from experiment A"
    label: "tab:exp-a"
    border_style: "booktabs"
    columns:
      - display_name: "Time (s)"
        internal_name: "time"
      - display_name: "Temperature (°C)"
        internal_name: "temp"
    formulas:
      temp_fahrenheit: "temp * 9/5 + 32"
    graph_configs:
      - enabled: true
        x_column: "time"
        series:
          - y_column: "temp"
            label: "Temperature"
            type: "line"
```

## Usage Guide

### Editing Tables

- **Select cells**: click to select single cells, drag to select ranges
- **Edit cells**: double-click or press F2 to edit
- **Insert rows/columns**: right-click to access context menu
- **Reorder**: use arrow buttons or drag from context menu
- **Undo/Redo**: Ctrl+Z / Ctrl+Y

### Working with Formulas

1. Select a column header
2. Go to **Formulas → Set Formula for Column**
3. Enter a formula using column internal names:
   ```
   time * 2 + 5
   temperature^2 / 100
   10^(-3)
   ```
4. Formula applies to all rows automatically
5. Use **Formulas → Clear Formula** to remove

### Creating Graphs

1. Select a table
2. Go to **Graph → Configure Graph**
3. In the **Basic** tab:
   - Select X-axis column
   - Choose graph type
4. In the **Series** tab:
   - Add Y-axis series
   - Configure trend lines if needed
5. Adjust axis ranges and labels as needed
6. Click **OK** to save configuration

### Generating Output

1. Edit all tables and formulas
2. Go to **Output → Generate**
3. Select output options:
   - Generate LaTeX tables
   - Generate graphs
   - Optionally compile LaTeX to PDF
4. Check the log for completion status
5. Find outputs in `tables/` and `figures/` directories

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pandas` | Latest | Data manipulation and CSV handling |
| `matplotlib` | Latest | Graph rendering and PDF export |
| `PySide6` | Latest | GUI framework |
| `pyyaml` | Latest | Configuration file parsing |

See `requirements.txt` for pinned versions.

## Architecture

### Core Modules

- **`main_window.py`**: Main application window and table management
- **`config.py`**: Configuration loading, saving, and normalization
- **`formula.py`**: Formula evaluation engine
- **`graph/`**: Graph configuration and rendering
- **`latex.py`**: LaTeX table generation and compilation
- **`dialogs/`**: UI dialogs for settings and configuration
- **`widgets/`**: Reusable UI components

### Data Flow

```
CSV Input
    ↓
[Spreadsheet UI] → Formulas → [Calculations]
    ↓                           ↓
[Config YAML] ← ← ← ← ← ← ← ←  ↓
    ↓                           ↓
[LaTeX Generator] ← ← ← ← ← ← Table Data
    ↓                           ↓
[LaTeX Table] ← ← ← ← ← ← [Graph Renderer]
                                ↓
                          [Graph PDF]
```

## Known Limitations

- **Graph preview requires PySide6 display**: Cannot preview graphs in headless environments
- **LaTeX compilation**: Requires a working TeX installation (if auto-compile enabled)
- **Large datasets**: Performance may degrade with very large spreadsheets (>10,000 rows)
- **Formula dependencies**: Circular references not detected; may cause infinite loops

## Troubleshooting

### Application won't start
```bash
# Verify dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

### Graphs not rendering
- Ensure matplotlib is properly installed: `pip install --upgrade matplotlib`
- Check that graph series have valid numeric data
- Verify X/Y column selections in graph configuration

### LaTeX compilation fails
- Ensure a TeX distribution is installed (TeX Live, MiKTeX, MacTeX)
- Check `pdflatex` is available: `pdflatex --version`
- Verify LaTeX generated `.tex` files are syntactically correct

### Configuration issues
- Check `config.yaml` YAML syntax (use online validators)
- Verify CSV file paths are relative to project directory
- Ensure column names match between CSV and configuration

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Submit a pull request

## Recent Updates

### Version 2026-05-15
- Fixed graph configuration synchronization between tabs
- Enhanced numeric data filtering (NaN, Inf handling)
- Improved axis restoration when reopening saved graphs
- Added support for `^` exponentiation operator
- Added comprehensive graph rendering diagnostics

See `PATCH_NOTES.md` for detailed changelog.

## License

[Specify license if applicable]

## Contact & Support

For issues, questions, or suggestions, please [create an issue](https://github.com/f8vnm4pjpv-bit/TeXSheet/issues) on GitHub.

---

**TeXSheet** - Making scientific document generation easier, one formula at a time.
