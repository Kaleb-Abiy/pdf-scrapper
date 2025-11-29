# PDF Extractor - Alabama College Enrollment Data

A Python script that extracts high school college enrollment data from PDF reports and converts it to structured CSV format.

## How to Run the Script

### Prerequisites

1. **Python 3.7+** installed on your system
2. **Virtual environment** (recommended) - Python's `venv` module

### Installation

1. **Create a virtual environment** (recommended):
```bash
python3 -m venv env
```

2. **Activate the virtual environment**:
```bash
# On Linux/Mac:
source env/bin/activate

# On Windows:
env\Scripts\activate
```

3. **Install dependencies from requirements.txt**:
```bash
pip install -r requirements.txt
```

This will install all required packages including:
- `pdfplumber` - PDF text extraction
- `pandas` - Data manipulation and CSV export
- And other dependencies listed in `requirements.txt`

**Note**: Make sure your virtual environment is activated before running the script. You should see `(env)` in your terminal prompt when the virtual environment is active.

### Usage

Run the script from the command line with a PDF file path as an argument:

```bash
python pdf_extractor.py <pdf_path>
```

**Example:**
```bash
python pdf_extractor.py FA24_HSBasic.pdf
```

### Expected Input/Output

#### Input

- **File Format**: PDF file containing Alabama high school college enrollment data
- **File Naming Convention**: Files should follow the pattern `FA<YY>_<suffix>.pdf` (e.g., `FA24_HSBasic.pdf`)
  - The script extracts the year from the filename prefix (`FA24` → `2024`)
- **PDF Structure**: 
  - Tabular data with school information
  - Each school entry consists of:
    - Main school line: School ID, school name, and 9 data points
    - Sub-entries: Lines starting with `--Enrolled in 2YR Colleges` or `--Enrolled in 4YR Colleges` with 7 data points

#### Output

- **File Format**: CSV file
- **File Naming**: Automatically generated based on input filename
  - Pattern: `al_<YYYY>_college_enroll-prep_school.csv`
  - Example: `FA24_HSBasic.pdf` → `al_2024_college_enroll-prep_school.csv`
- **Output Columns**:
  - `HS Code` - High school identifier code
  - `school_name` - Name of the high school
  - `college_type` - Type of college enrollment: `'all'`, `'2YR'`, or `'4YR'`
  - `year` - Year extracted from PDF filename
  - `high_school_graduates` - Number of high school graduates
  - `enrolled_in_alabama_public_colleges` - Number enrolled in Alabama public colleges
  - `enrolled_in_remedial_math` - Number enrolled in remedial math
  - `enrolled_in_remedial_english` - Number enrolled in remedial English
  - `enrolled_in_remedial_both` - Number enrolled in both remedial subjects
  - `enrolled_in_remedial_total` - Total enrolled in remedial courses

- **Output Structure**: 
  - Each school generates 3 rows (one for `'all'`, one for `'2YR'`, one for `'4YR'`)
  - Duplicate entries are automatically removed
  - Console output shows extraction progress and duplicate removal statistics

## Notes on Logic, Assumptions, and PDF-Specific Challenges

### Extraction Logic

1. **Bounding Box Cropping Approach**:
   - Uses fixed bounding box coordinates to extract text from specific regions of each page
   - Configuration constants define the extraction area:
     - `ROW_HEIGHT = 42` - Vertical spacing between school entries
     - `INITIAL_TOP = 165` - Starting Y-coordinate
     - `INITIAL_BOTTOM = 200` - Initial bottom Y-coordinate
     - `LEFT_MARGIN = 13` - Left boundary
     - `RIGHT_MARGIN = 780` - Right boundary
   - The bounding box moves down by `ROW_HEIGHT` pixels for each iteration

2. **Line Classification**:
   - **Main school entries**: Lines with more than 11 tokens
     - First token: School ID (must be numeric)
     - Tokens 1 to -9: School name
     - Last 9 tokens: Data points
   - **Sub-entries**: Lines with exactly 11 tokens
     - Must start with `"--Enrolled in"`
     - Third token must be `"2YR"` or `"4YR"`
     - Last 7 tokens: Data points
     - Requires a preceding main school entry for context

3. **State Management**:
   - Maintains state of the last processed school across sub-entries
   - State is reset at the beginning of each page to prevent cross-page contamination
   - Sub-entries inherit school name, ID, and graduate count from the most recent main entry

### Assumptions

1. **PDF Structure Consistency**:
   - Assumes consistent table layout across all pages
   - Assumes fixed row height of 42 pixels between school entries
   - Assumes data starts at Y-coordinate 165 on each page

2. **Data Format**:
   - School IDs are always numeric and appear as the first token
   - School names don't contain numbers that could be mistaken for data points
   - All data points are numeric integers
   - Sub-entries always follow their parent school entry

3. **File Naming**:
   - PDF filename must start with `FA` followed by 2 digits (e.g., `FA24`)
   - Year is extracted by replacing `FA` with `20` (e.g., `FA24` → `2024`)

### PDF-Specific Challenges

1. **Fixed Row Height Limitation**:
   - The script uses a fixed 42-pixel row height, which works well for the target PDFs
   - **Challenge**: If PDFs have variable row heights, some entries may be missed or duplicated
   - **Solution**: The 42-pixel value was empirically determined to match the PDF structure

2. **Bounding Box Alignment**:
   - **Challenge**: Fixed coordinates may not align perfectly with table rows if PDF formatting varies
   - **Mitigation**: The script includes error handling for out-of-bounds bounding boxes

3. **Duplicate Detection**:
   - **Challenge**: Overlapping bounding boxes or PDF rendering issues can cause duplicate extractions
   - **Solution**: Multi-level deduplication:
     - In-memory tracking using unique keys (`school_id + college_type`)
     - DataFrame-level deduplication as a safety net
     - Duplicates are automatically removed with the first occurrence kept

4. **Text Extraction Reliability**:
   - **Challenge**: PDF text extraction can be inconsistent (spacing, formatting, special characters)
   - **Mitigation**: 
     - Validates extracted data (numeric checks, token count validation)
     - Handles empty lines and invalid formats gracefully
     - Skips lines that don't match expected patterns

5. **Page Boundaries**:
   - **Challenge**: School entries may span across page boundaries
   - **Current Behavior**: State is reset per page, so sub-entries at the start of a new page without a parent entry are skipped
   - This is a known limitation for entries split across pages

6. **Data Validation**:
   - All data points are validated for:
     - Correct token count (9 for main entries, 7 for sub-entries)
     - Numeric format (must be convertible to integers)
   - Invalid entries are silently skipped

### Error Handling

- **File Not Found**: Script exits with error message if PDF doesn't exist
- **Bounding Box Errors**: Caught and handled as normal end-of-page condition
- **Invalid Data**: Lines that don't match expected patterns are skipped
- **Empty Results**: Warning message if no data is extracted
- **Infinite Loop Protection**: Maximum iteration limit (1000) prevents infinite loops

### Performance Considerations

- Processes one page at a time to manage memory
- Uses efficient set-based deduplication
- Safety limit of 1000 iterations per page prevents excessive processing

