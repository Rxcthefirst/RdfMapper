import pandas as pd
import json

# Test the JSON file
with open('examples/owl2_rdfxml_demo/data/students_nested.json', 'r') as f:
    data = json.load(f)

print('Raw JSON structure:')
print(f'Type: {type(data)}')
print(f'Length: {len(data)}')
print(f'First record keys: {list(data[0].keys())}')
print()

# Test pandas.json_normalize
df_flat = pd.json_normalize(data)
print('Flattened DataFrame:')
print(f'Shape: {df_flat.shape}')
print(f'Columns: {df_flat.columns.tolist()}')
print()

# Show sample data
print('Sample rows:')
for col in df_flat.columns[:5]:
    print(f'{col}: {df_flat[col].iloc[0]}')

# Check if our mapping fields exist
mapping_fields = [
    'student_id',
    'academic_info.gpa',
    'academic_info.enrollment_date',
    'academic_info.academic_status',
    'courses.course_code',
    'courses.course_title',
    'courses.grade',
    'courses.semester'
]

print(f'\nMapping field check:')
for field in mapping_fields:
    exists = field in df_flat.columns
    print(f'{field}: {"✓" if exists else "✗"}')
