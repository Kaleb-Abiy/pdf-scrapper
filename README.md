# PDF Extractor - Alabama College Enrollment Data

This Python script pulls high school college enrollment data out of PDF reports and turns it into a clean CSV file.

## How to Run the Script

### What You'll Need

- **Python 3.7 or higher** installed on your computer
- A **virtual environment** (highly recommended) - Python's built-in `venv` module works great

### Getting Set Up

1. **Create a virtual environment** (this keeps your project dependencies separate):
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

3. **Install all the dependencies**:
```bash
pip install -r requirements.txt
```

This installs everything you need, including:
- `pdfplumber` - handles the PDF text extraction
- `pandas` - for working with the data and creating CSV files
- Plus all the other dependencies listed in `requirements.txt`

**Quick tip**: Make sure your virtual environment is activated before running the script. You'll know it's active when you see `(env)` at the start of your terminal prompt.

### Running the Script

Just run it from the command line and pass in your PDF file:

```bash
python pdf_extractor.py <pdf_path>
```

**Example:**
```bash
python pdf_extractor.py FA24_HSBasic.pdf
```

## Expected Input/Output

### Input

- **File Format**: A PDF file with Alabama high school college enrollment data
- **File Naming**: Your PDF files should follow the pattern `FA<YY>_<suffix>.pdf` (like `FA24_HSBasic.pdf`)
  - The script automatically figures out the year from the filename prefix (so `FA24` becomes `2024`)
- **What's Inside**: 
  - The PDF has a table with school information
  - Each school has:
    - A main line with the school ID, name, and 9 data points
    - Sub-entries that start with `--Enrolled in 2YR Colleges` or `--Enrolled in 4YR Colleges` with 7 data points each

### Output

- **File Format**: A CSV file
- **File Naming**: The output filename is automatically created from your input filename
  - Pattern: `al_<YYYY>_college_enroll-prep_school.csv`
  - Example: `FA24_HSBasic.pdf` becomes `al_2024_college_enroll-prep_school.csv`
- **What's in the CSV**: 
  - `HS Code` - The high school's ID number
  - `school_name` - The name of the high school
  - `college_type` - Either `'all'`, `'2YR'`, or `'4YR'`
  - `year` - The year pulled from the PDF filename
  - `high_school_graduates` - How many students graduated
  - `enrolled_in_alabama_public_colleges` - How many enrolled in Alabama public colleges
  - `enrolled_in_remedial_math` - How many enrolled in remedial math
  - `enrolled_in_remedial_english` - How many enrolled in remedial English
  - `enrolled_in_remedial_both` - How many enrolled in both remedial subjects
  - `enrolled_in_remedial_total` - Total number enrolled in remedial courses

- **How It's Organized**: 
  - Each school gets 3 rows (one for `'all'`, one for `'2YR'`, one for `'4YR'`)
  - Any duplicate entries get automatically removed
  - You'll see progress messages in the console, including how many duplicates were found and removed

## Notes on Logic, Assumptions, and PDF-Specific Challenges

### How It Works

1. **The Bounding Box Approach**:
   - The script uses fixed coordinates to grab text from specific spots on each page
   - These settings control where it looks:
     - `ROW_HEIGHT = 42` - How much space between each school entry
     - `INITIAL_TOP = 165` - Where to start on the page
     - `INITIAL_BOTTOM = 200` - The initial bottom boundary
     - `LEFT_MARGIN = 13` - The left edge
     - `RIGHT_MARGIN = 780` - The right edge
   - As it goes through the page, the bounding box moves down by `ROW_HEIGHT` pixels each time

2. **How It Figures Out What Each Line Is**:
   - **Main school entries**: Lines with more than 11 words/tokens
     - First token is the school ID (has to be a number)
     - Everything from token 1 to -9 is the school name
     - The last 9 tokens are the data points
   - **Sub-entries**: Lines with exactly 11 tokens
     - Must start with `"--Enrolled in"`
     - The third token has to be `"2YR"` or `"4YR"`
     - The last 7 tokens are the data points
     - These need a main school entry above them to make sense

3. **Keeping Track of State**:
   - The script remembers the last school it processed so it can attach sub-entries to the right school
   - It resets this memory at the start of each new page to avoid mixing things up
   - Sub-entries automatically get the school name, ID, and graduate count from the main entry above them

### What We're Assuming

1. **The PDF Structure**:
   - We're assuming the table layout stays consistent across all pages
   - We're assuming there's a fixed 42-pixel gap between school entries
   - We're assuming the data always starts at Y-coordinate 165 on each page

2. **The Data Format**:
   - School IDs are always numbers and show up first
   - School names don't have numbers in them that could be confused with data
   - All the data points are whole numbers
   - Sub-entries always come right after their parent school entry

3. **File Naming**:
   - PDF filenames need to start with `FA` followed by 2 digits (like `FA24`)
   - The year gets pulled by replacing `FA` with `20` (so `FA24` becomes `2024`)

### PDF-Specific Challenges We're Dealing With

1. **The Fixed Row Height Thing**:
   - We're using a fixed 42-pixel row height, which works great for these specific PDFs
   - **The problem**: If a PDF has rows that are different heights, we might miss some entries or grab duplicates
   - **What we did**: We tested and found that 42 pixels matches the PDF structure perfectly

2. **Bounding Box Alignment**:
   - **The problem**: If the PDF formatting changes, our fixed coordinates might not line up perfectly with the table rows
   - **How we handle it**: The script catches errors when the bounding box goes out of bounds and handles them gracefully

3. **Duplicate Detection**:
   - **The problem**: Sometimes overlapping bounding boxes or weird PDF rendering can cause us to grab the same entry twice
   - **How we fix it**: We use a two-step approach:
     - We track what we've seen in memory using unique keys (`school_id + college_type`)
     - We also do a final deduplication pass on the DataFrame as a backup
     - When we find duplicates, we keep the first one and toss the rest

4. **Text Extraction Can Be Tricky**:
   - **The problem**: PDFs don't always extract text cleanly - spacing can be weird, formatting can be inconsistent, special characters can cause issues
   - **How we handle it**: 
     - We validate everything we extract (checking that numbers are actually numbers, making sure we have the right number of tokens)
     - We skip empty lines and anything that doesn't match what we expect
     - If something looks wrong, we just move on to the next line

5. **Page Boundaries**:
   - **The problem**: Sometimes a school entry might get split across two pages
   - **What happens**: We reset our state at the start of each page, so if a sub-entry shows up at the beginning of a new page without its parent school entry, we'll skip it
   - This is a known limitation - entries that span pages might not get fully captured

6. **Data Validation**:
   - We check every data point to make sure:
     - We have the right number of tokens (9 for main entries, 7 for sub-entries)
     - Everything that should be a number actually is a number
   - If something doesn't pass these checks, we skip it and keep going

### Error Handling

- **File Not Found**: If the PDF doesn't exist, the script will tell you and exit
- **Bounding Box Errors**: These are caught and treated as normal "end of page" conditions
- **Invalid Data**: Lines that don't match what we expect just get skipped
- **Empty Results**: If we don't find any data, you'll get a warning message
- **Infinite Loop Protection**: We cap it at 1000 iterations per page so it can't get stuck

### Performance Notes

- We process one page at a time to keep memory usage reasonable
- We use a set-based approach for deduplication, which is pretty fast
- The 1000 iteration limit per page keeps things from running too long
