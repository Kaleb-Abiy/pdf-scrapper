import pdfplumber
import sys
from pathlib import Path
import pandas as pd

OUTPUT_PREFIX = 'al_'
OUTPUT_SUFFIX = '_college_enroll-prep_school'

# Configuration constants
ROW_HEIGHT = 42
INITIAL_TOP = 165
INITIAL_BOTTOM = 200
LEFT_MARGIN = 13
RIGHT_MARGIN = 780


class SchoolDataExtractor:
    """Handles extraction and deduplication of school data from PDF."""
    
    def __init__(self,doc_year):
        self.last_school_name = None
        self.last_school_id = None
        self.last_graduates_number = None
        self.doc_year = doc_year
        self.seen_entries = set()  # Track seen entries to avoid duplicates
        
    def reset_page_state(self):
        """Reset state for each new page to avoid cross-page contamination."""
        self.last_school_name = None
        self.last_school_id = None
        self.last_graduates_number = None
    
    def _create_entry_key(self, school_id, college_type):
        """Create a unique key for deduplication."""
        return f"{school_id}_{college_type}"
    
    def _is_duplicate(self, school_id, college_type):
        """Check if entry already exists."""
        key = self._create_entry_key(school_id, college_type)
        if key in self.seen_entries:
            return True
        self.seen_entries.add(key)
        return False
    
    def _validate_data_points(self, data_points, expected_count):
        """Validate that data points have expected count and are numeric."""
        if len(data_points) != expected_count:
            return False
        # Check if all are numeric (or can be converted)
        try:
            [int(x) for x in data_points]
            return True
        except (ValueError, TypeError):
            return False
    
    def format_result(self, school_id, school_name, data_points, college_type='all'):
        """Format extracted data into structured result dictionary."""
        result = {}
        result['HS Code'] = school_id
        result['school_name'] = school_name
        result['college_type'] = college_type
        result['year'] = self.doc_year
        if college_type == 'all':
            if not self._validate_data_points(data_points, 9):
                return None
            result['high_school_graduates'] = data_points[0]
            result['enrolled_in_alabama_public_colleges'] = data_points[2]
            result['enrolled_in_remedial_math'] = data_points[3]
            result['enrolled_in_remedial_english'] = data_points[4]
            result['enrolled_in_remedial_both'] = data_points[5]
            result['enrolled_in_remedial_total'] = data_points[6]
        else:
            if not self._validate_data_points(data_points, 7):
                return None
            if self.last_graduates_number is None:
                return None  # Can't create entry without parent school data
            result['high_school_graduates'] = self.last_graduates_number
            result['enrolled_in_alabama_public_colleges'] = data_points[0]
            result['enrolled_in_remedial_math'] = data_points[1]
            result['enrolled_in_remedial_english'] = data_points[2]
            result['enrolled_in_remedial_both'] = data_points[3]
            result['enrolled_in_remedial_total'] = data_points[4]
        
        return result

    def get_entities(self, line):
        """Extract entities from a line of text."""
        text = line.get('text', '').strip()
        if not text:
            return None
        
        split_text = text.split()
        if not split_text:
            return None
        
        # Main school entry (has more than 11 tokens)
        if len(split_text) > 11:
            school_id = split_text[0]
            data_points = split_text[-9:]
            school_name = ' '.join(split_text[1:-9])
            
            # Validate school ID is numeric
            if not school_id.isdigit():
                return None
            
            # Check for duplicates
            if self._is_duplicate(school_id, 'all'):
                return None
            
            # Update state
            self.last_school_name = school_name
            self.last_school_id = school_id
            self.last_graduates_number = data_points[0]
            
            return self.format_result(school_id, school_name, data_points)
        
        # Sub-entry (enrollment type line - exactly 11 tokens)
        elif len(split_text) == 11:
            # Validate format: "--Enrolled in XYR Colleges"
            if split_text[0] != '--Enrolled' or split_text[1] != 'in':
                return None
            
            college_type = split_text[2]  # Should be "2YR" or "4YR"
            if college_type not in ['2YR', '4YR']:
                return None
            
            # Must have parent school data
            if self.last_school_id is None or self.last_school_name is None:
                return None
            
            data_points = split_text[-7:]
            
            # Check for duplicates
            if self._is_duplicate(self.last_school_id, college_type):
                return None
            
            return self.format_result(
                self.last_school_id, 
                self.last_school_name, 
                data_points, 
                college_type=college_type
            )
        
        return None


def crop_and_extract(pdf_path):
    """Extract school data from PDF using bounding box cropping."""
    doc_year = pdf_path.split('_')[0].replace('FA', '20')
    extractor = SchoolDataExtractor(doc_year)
    all_results = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            extractor.reset_page_state()  # Reset state for each page
            
            top = INITIAL_TOP
            bottom = INITIAL_BOTTOM
            bbox = page.crop((LEFT_MARGIN, top, RIGHT_MARGIN, bottom))
            
            iteration_count = 0
            max_iterations = 1000  # Safety limit to prevent infinite loops
            
            while bbox and iteration_count < max_iterations:
                try:
                    lines = bbox.extract_text_lines()
                    
                    if not lines:
                        # No more lines, move to next page
                        break
                    
                    for line in lines:
                        result = extractor.get_entities(line)
                        if result is not None:
                            all_results.append(result)
                    
                    # Move to next row
                    top += ROW_HEIGHT
                    bottom += ROW_HEIGHT
                    bbox = page.crop((LEFT_MARGIN, top, RIGHT_MARGIN, bottom))
                    iteration_count += 1
                    
                except ValueError as e:
                    # Bounding box out of page bounds - normal end condition
                    break
                except Exception as e:
                    print(f"Error on page {page_num + 1}, iteration {iteration_count}: {e}")
                    break
    
    return all_results

def get_output_path(pdf_path):
    year = pdf_path.split('_')[0].replace('FA', '20')
    return f'{OUTPUT_PREFIX + year +  OUTPUT_SUFFIX}.csv'
def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    print(f"Extracting data from {pdf_path}...")
    results = crop_and_extract(pdf_path)
    
    if not results:
        print("Warning: No data extracted from PDF")
        sys.exit(1)
    
    # Create DataFrame and save
    df = pd.DataFrame(results)
    
    # Additional deduplication at DataFrame level (safety net)
    initial_count = len(df)
    df = df.drop_duplicates(subset=['HS Code', 'college_type'], keep='first')
    final_count = len(df)
    
    if initial_count != final_count:
        print(f"Removed {initial_count - final_count} duplicate entries")
    output_path = get_output_path(pdf_path)

    df.to_csv(output_path, index=False)
    print(f"Extracted {final_count} unique entries")
    print(f"Results saved to {output_path}")


if __name__ == '__main__':
    main()
