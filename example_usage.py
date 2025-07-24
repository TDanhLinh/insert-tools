#!/usr/bin/env python3
"""
Example usage of ExcelAPITool for processing SIM outbound data
"""

from excel_api_tool import ExcelAPITool, APIConfig
import json

def main():
    """Example of how to use the ExcelAPITool"""
    
    # Initialize the tool
    excel_file = "Mapping thông tin sản phẩm SIM outbound.xlsx"
    tool = ExcelAPITool(excel_file)
    
    # Load and examine the data
    print("=== Excel File Analysis ===")
    sheets = tool.get_sheet_names()
    print(f"Available sheets: {sheets}")
    
    # Load data
    data = tool.load_excel_data()
    print(f"\nLoaded {len(data)} rows from Excel file")
    print(f"Columns: {list(data.columns)}")
    
    # Preview the data
    print("\n=== Data Preview ===")
    preview = tool.preview_data(10)
    print(preview.to_string())
    
    # Clean data - remove empty rows
    print("\n=== Data Cleaning ===")
    clean_data = data.dropna(how='all')  # Remove completely empty rows
    clean_data = clean_data[clean_data['KHAI BÁO SẢN PHẨM TRÊN BCSS'].notna()]  # Remove rows where main column is NaN
    print(f"Clean data has {len(clean_data)} rows")
    
    # Set up column mapping (mapping Excel columns to API field names)
    column_mapping = {
        'KHAI BÁO SẢN PHẨM TRÊN BCSS': 'product_name',
        'MAPPING SẢN PHẨM TRÊN FILE EXCEL VNSKY GỬI': 'excel_mapping',
        'GHI CHÚ': 'notes'
    }
    
    tool.data = clean_data  # Use cleaned data
    tool.set_column_mapping(column_mapping)
    
    # Example API configuration
    # Replace with your actual API endpoint
    api_config = APIConfig(
        url="https://httpbin.org/post",  # Test endpoint
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_API_TOKEN"  # Replace with actual token
        }
    )
    
    # Test with dry run first
    print("\n=== Dry Run Test ===")
    results = tool.process_all_rows(api_config, dry_run=True)
    
    # Print results summary
    successful = sum(1 for r in results if r['status'] == 'dry_run')
    print(f"Dry run completed: {successful} rows would be processed")
    
    # Show a few example transformations
    print("\n=== Example Data Transformations ===")
    for i, result in enumerate(results[:3]):
        if result['status'] == 'dry_run':
            print(f"Row {i+1}: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
    
    # Uncomment below to actually send to API
    # print("\n=== Sending to API ===")
    # actual_results = tool.process_all_rows(api_config, dry_run=False)
    # 
    # successful = sum(1 for r in actual_results if r['status'] == 'success')
    # failed = sum(1 for r in actual_results if r['status'] == 'failed')
    # print(f"API processing completed: {successful} successful, {failed} failed")

def demo_with_custom_api():
    """Demo with custom API configuration"""
    
    # Example of how to configure for different types of APIs
    
    # REST API with authentication
    rest_api = APIConfig(
        url="https://api.example.com/products",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer your-token-here",
            "X-API-Key": "your-api-key"
        }
    )
    
    # API with basic auth
    basic_auth_api = APIConfig(
        url="https://api.example.com/data",
        method="POST",
        headers={"Content-Type": "application/json"},
        auth=("username", "password")
    )
    
    # PUT request example
    put_api = APIConfig(
        url="https://api.example.com/update",
        method="PUT",
        headers={"Content-Type": "application/json"}
    )
    
    print("API configurations created (examples only)")
    print(f"REST API: {rest_api.url}")
    print(f"Basic Auth API: {basic_auth_api.url}")
    print(f"PUT API: {put_api.url}")

if __name__ == "__main__":
    main()
    print("\n" + "="*50)
    demo_with_custom_api() 