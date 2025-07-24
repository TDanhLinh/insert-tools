# Excel to API Tool

A Python tool for reading data from Excel files and sending it to web APIs. This tool is specifically designed to work with the SIM outbound product mapping Excel template, but can be adapted for any Excel-to-API workflow.

## Features

- 📊 **Excel Reading**: Support for `.xlsx` and `.xls` files with multiple sheets
- 🔄 **Data Transformation**: Flexible column mapping from Excel columns to API field names
- 🌐 **API Integration**: Support for POST and PUT HTTP requests with authentication
- 🛡️ **Error Handling**: Comprehensive error handling and logging
- 🧪 **Dry Run Mode**: Test your data transformations without making actual API calls
- 📋 **Batch Processing**: Process all rows with detailed results tracking
- ✅ **Comprehensive Testing**: Full unit test coverage with mocked dependencies

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from excel_api_tool import ExcelAPITool, APIConfig

# Initialize the tool
tool = ExcelAPITool("your_excel_file.xlsx")

# Load data from Excel
data = tool.load_excel_data()

# Set up column mapping (Excel column -> API field)
column_mapping = {
    'Product Name': 'name',
    'Price': 'price',
    'Category': 'category'
}
tool.set_column_mapping(column_mapping)

# Configure API endpoint
api_config = APIConfig(
    url="https://api.example.com/products",
    method="POST",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN"
    }
)

# Test with dry run first
results = tool.process_all_rows(api_config, dry_run=True)
print(f"Would process {len(results)} rows")

# Actually send to API
results = tool.process_all_rows(api_config, dry_run=False)
```

### Working with SIM Outbound Data

```python
from excel_api_tool import ExcelAPITool, APIConfig

# Load the SIM outbound mapping file
tool = ExcelAPITool("Mapping thông tin sản phẩm SIM outbound.xlsx")
data = tool.load_excel_data()

# Clean the data (remove empty rows)
clean_data = data.dropna(how='all')
clean_data = clean_data[clean_data['KHAI BÁO SẢN PHẨM TRÊN BCSS'].notna()]
tool.data = clean_data

# Set up column mapping for BCSS API
column_mapping = {
    'KHAI BÁO SẢN PHẨM TRÊN BCSS': 'product_name',
    'MAPPING SẢN PHẨM TRÊN FILE EXCEL VNSKY GỬI': 'excel_mapping',
    'GHI CHÚ': 'notes'
}
tool.set_column_mapping(column_mapping)

# Configure BCSS API
api_config = APIConfig(
    url="https://your-bcss-api.com/products",
    method="POST",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_BCSS_TOKEN"
    }
)

# Process all rows
results = tool.process_all_rows(api_config, dry_run=False)
```

## API Reference

### ExcelAPITool Class

#### Constructor
```python
ExcelAPITool(excel_file_path: str)
```
Initialize the tool with path to Excel file.

#### Methods

##### `load_excel_data(sheet_name=None, header_row=0)`
Load data from Excel file.
- `sheet_name`: Name of sheet to read (None for first sheet)
- `header_row`: Row number for headers (0-indexed)
- Returns: pandas DataFrame

##### `get_sheet_names()`
Get list of all sheet names in the Excel file.
- Returns: List of sheet names

##### `preview_data(rows=5)`
Preview first few rows of loaded data.
- `rows`: Number of rows to show
- Returns: pandas DataFrame

##### `set_column_mapping(mapping)`
Set mapping between Excel columns and API fields.
- `mapping`: Dictionary mapping Excel column names to API field names

##### `transform_row_to_api_format(row)`
Transform a DataFrame row to API format.
- `row`: pandas Series (DataFrame row)
- Returns: Dictionary for API

##### `send_to_api(api_config, data)`
Send data to API endpoint.
- `api_config`: APIConfig instance
- `data`: Dictionary to send
- Returns: requests.Response

##### `process_all_rows(api_config, batch_size=1, dry_run=False)`
Process all rows and send to API.
- `api_config`: APIConfig instance
- `batch_size`: Number of rows per batch (currently only 1 supported)
- `dry_run`: If True, don't actually send to API
- Returns: List of results

### APIConfig Class

```python
APIConfig(
    url: str,
    method: str = "POST",
    headers: Dict[str, str] = None,
    auth: tuple = None
)
```

Configuration for API endpoints.

#### Examples

```python
# Basic POST API
api_config = APIConfig(url="https://api.example.com/data")

# PUT with custom headers
api_config = APIConfig(
    url="https://api.example.com/update",
    method="PUT",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-key"
    }
)

# API with basic authentication
api_config = APIConfig(
    url="https://api.example.com/secure",
    auth=("username", "password")
)
```

## Example Workflows

### 1. Data Validation Workflow

```python
# Load and inspect data
tool = ExcelAPITool("data.xlsx")
data = tool.load_excel_data()

# Check data quality
print(f"Total rows: {len(data)}")
print(f"Columns: {list(data.columns)}")
print("\nFirst 5 rows:")
print(tool.preview_data(5))

# Check for missing values
print("\nMissing values per column:")
print(data.isnull().sum())
```

### 2. Incremental Processing

```python
# Process data in chunks for large files
tool = ExcelAPITool("large_file.xlsx")
data = tool.load_excel_data()

chunk_size = 100
total_rows = len(data)

for i in range(0, total_rows, chunk_size):
    chunk = data.iloc[i:i+chunk_size]
    tool.data = chunk
    
    results = tool.process_all_rows(api_config, dry_run=False)
    print(f"Processed rows {i+1} to {min(i+chunk_size, total_rows)}")
```

### 3. Error Handling and Retry

```python
import time

def process_with_retry(tool, api_config, max_retries=3):
    """Process with retry logic for failed requests"""
    
    results = tool.process_all_rows(api_config, dry_run=False)
    failed_rows = [r for r in results if r['status'] == 'failed']
    
    retry_count = 0
    while failed_rows and retry_count < max_retries:
        print(f"Retrying {len(failed_rows)} failed rows (attempt {retry_count + 1})")
        
        # Wait before retry
        time.sleep(2 ** retry_count)  # Exponential backoff
        
        # Retry failed rows
        retry_results = []
        for failed_result in failed_rows:
            row_index = failed_result['row'] - 1
            row = tool.data.iloc[row_index]
            
            try:
                api_data = tool.transform_row_to_api_format(row)
                response = tool.send_to_api(api_config, api_data)
                retry_results.append({
                    'row': failed_result['row'],
                    'status': 'success',
                    'response_status': response.status_code
                })
            except Exception as e:
                retry_results.append({
                    'row': failed_result['row'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        failed_rows = [r for r in retry_results if r['status'] == 'failed']
        retry_count += 1
    
    return results, failed_rows
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest test_excel_api_tool.py -v

# Run specific test class
python -m pytest test_excel_api_tool.py::TestExcelAPITool -v

# Run with coverage
python -m pytest test_excel_api_tool.py --cov=excel_api_tool
```

### Test Coverage

The test suite covers:
- ✅ Excel file loading and parsing
- ✅ Multiple sheet handling
- ✅ Data transformation and mapping
- ✅ API configuration and requests
- ✅ Error handling and edge cases
- ✅ Dry run functionality
- ✅ Integration scenarios with SIM outbound data

## File Structure

```
tools/
├── excel_api_tool.py          # Main tool implementation
├── example_usage.py           # Usage examples
├── test_excel_api_tool.py     # Comprehensive test suite
├── requirements.txt           # Python dependencies
├── README.md                 # This documentation
└── Mapping thông tin sản phẩm SIM outbound.xlsx  # Sample Excel file
```

## Dependencies

- `pandas>=1.5.0` - Excel file reading and data manipulation
- `requests>=2.28.0` - HTTP API calls
- `openpyxl>=3.0.0` - Excel file format support
- `xlrd>=2.0.0` - Legacy Excel file support
- `pytest>=7.0.0` - Testing framework
- `pytest-mock>=3.8.0` - Test mocking utilities

## Troubleshooting

### Common Issues

**1. Excel file not found or permission denied**
```python
# Check file path and permissions
import os
print(f"File exists: {os.path.exists('your_file.xlsx')}")
print(f"File readable: {os.access('your_file.xlsx', os.R_OK)}")
```

**2. Column mapping errors**
```python
# Check actual column names in Excel
tool = ExcelAPITool("your_file.xlsx")
data = tool.load_excel_data()
print("Available columns:", list(data.columns))
```

**3. API authentication issues**
```python
# Test API connectivity separately
import requests
response = requests.get("https://your-api.com/health")
print(f"API status: {response.status_code}")
```

**4. Data type conversion issues**
```python
# Check data types
print(tool.data.dtypes)

# Convert if needed
tool.data['numeric_column'] = pd.to_numeric(tool.data['numeric_column'], errors='coerce')
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please:
1. Check the troubleshooting section above
2. Review the test cases for usage examples
3. Create an issue with detailed error messages and sample data 