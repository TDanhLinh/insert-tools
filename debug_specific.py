#!/usr/bin/env python3
"""
Specific debug for attribute 803 issue
"""

import pandas as pd
from bcss_api_integration import BCSSAPIIntegration

def debug_specific_attribute():
    """Debug attribute 803 specifically"""
    
    # Initialize integration
    mapping_file = "BCSS_Mapping_Configuration.xlsx"
    bcss_integration = BCSSAPIIntegration(mapping_file, "test_token")
    bcss_integration.load_excel_mapping()
    
    # Test row
    excel_row = pd.Series({
        'SKUID': 'TEST001',
        'Days': '30',
        'Product Name Short': 'Test SIM Package',
        'High Speed Data (MB or GB or GB/day)': '5GB',
        'Package type': 'Prepaid',
        'Throttled Speed (kbps)': '128',
        'Hotspot sharing': 'Support',
        'Support eSIM/Sim Card': 'eSIM',
        'National Area': 'Vietnam',
        'Telco': 'Viettel',
        'Giá bán 26.5 ( THM đề xuất)': '50000'
    })
    
    # Let's trace through the attribute processing manually
    bcss_field = "Loại gói"
    attribute_id = 803
    
    print(f"=== Debugging Attribute {attribute_id} for field '{bcss_field}' ===")
    
    if bcss_field in bcss_integration.mapping_data:
        excel_col = bcss_integration.mapping_data[bcss_field]['excel_mapping']
        notes = bcss_integration.mapping_data[bcss_field]['notes']
        
        print(f"Excel Column Mapping: '{excel_col}'")
        print(f"Notes: '{notes}'")
        print(f"Is excel_col NotNa?: {pd.notna(excel_col)}")
        
        attribute_value = ""
        if pd.notna(excel_col):
            print(f"Processing column mapping...")
            
            # Handle special cases for fixed values
            if excel_col == "Không bắt buộc":
                attribute_value = "0"
                print(f"Fixed value case 1: '{attribute_value}'")
            elif excel_col == "SIM outbound":
                attribute_value = "SIM outbound"
                print(f"Fixed value case 2: '{attribute_value}'")
            elif excel_col == "Cái":
                attribute_value = "Cái"
                print(f"Fixed value case 3: '{attribute_value}'")
            elif "Text cố định" in str(notes):
                attribute_value = excel_col
                print(f"Fixed text case: '{attribute_value}' (because notes contain 'Text cố định')")
            elif excel_col in excel_row.index:
                value = bcss_integration._process_mapping_value(excel_row[excel_col], notes)
                if value is not None:
                    attribute_value = value
                print(f"Found column '{excel_col}' with value '{excel_row[excel_col]}' → processed: '{value}' → final: '{attribute_value}'")
            else:
                print(f"Column '{excel_col}' not found in Excel row")
                # Try to find column with similar name
                for col in excel_row.index:
                    if excel_col.lower() in col.lower() or col.lower() in excel_col.lower():
                        value = bcss_integration._process_mapping_value(excel_row[col], notes)
                        if value is not None:
                            attribute_value = value
                        print(f"Found similar column '{col}' with value '{excel_row[col]}' → processed: '{value}' → final: '{attribute_value}'")
                        break
        
        print(f"Final attribute_value: '{attribute_value}'")
        
        # Now let's see what the actual transformation returns
        payload = bcss_integration.transform_excel_row_to_api(excel_row)
        
        for attr in payload['attributeValueList']:
            if attr['productCategoryAttributeId'] == attribute_id:
                print(f"Actual result in payload: '{attr['attributeValue']}'")
                break


if __name__ == "__main__":
    debug_specific_attribute() 