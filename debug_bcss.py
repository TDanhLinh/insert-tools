#!/usr/bin/env python3
"""
Debug script for BCSS integration
"""

import pandas as pd
from bcss_api_integration import BCSSAPIIntegration

def debug_transform():
    """Debug the transformation process"""
    
    # Initialize integration
    mapping_file = "BCSS_Mapping_Configuration.xlsx"
    bcss_integration = BCSSAPIIntegration(mapping_file, "test_token")
    bcss_integration.load_excel_mapping()
    
    print("=== Mapping Data ===")
    for field, mapping in bcss_integration.mapping_data.items():
        print(f"{field}: {mapping}")
    
    print("\n=== Attribute Mapping ===")
    attr_mapping = bcss_integration._get_attribute_mapping()
    for field, attr_id in attr_mapping.items():
        print(f"{field} (ID: {attr_id})")
    
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
    
    print(f"\n=== Excel Row Columns ===")
    for col in excel_row.index:
        print(f"'{col}': '{excel_row[col]}'")
    
    print(f"\n=== Processing Attributes ===")
    for bcss_field, attribute_id in attr_mapping.items():
        if bcss_field in bcss_integration.mapping_data:
            excel_col = bcss_integration.mapping_data[bcss_field]['excel_mapping']
            notes = bcss_integration.mapping_data[bcss_field]['notes']
            
            print(f"\nBCSS Field: {bcss_field}")
            print(f"  Excel Column Mapping: {excel_col}")
            print(f"  Notes: {notes}")
            print(f"  Attribute ID: {attribute_id}")
            
            if pd.notna(excel_col):
                if excel_col == "Không bắt buộc":
                    print(f"  → Fixed value: '0'")
                elif excel_col == "SIM outbound":
                    print(f"  → Fixed value: 'SIM outbound'")
                elif excel_col == "Cái":
                    print(f"  → Fixed value: 'Cái'")
                elif "Text cố định" in str(notes):
                    print(f"  → Fixed text: '{excel_col}'")
                elif excel_col in excel_row.index:
                    value = excel_row[excel_col]
                    processed = bcss_integration._process_mapping_value(value, notes)
                    print(f"  → Found column '{excel_col}' with value '{value}' → processed: '{processed}'")
                else:
                    print(f"  → Column '{excel_col}' not found in Excel row")
                    # Try to find similar column
                    for col in excel_row.index:
                        if excel_col.lower() in col.lower() or col.lower() in excel_col.lower():
                            value = excel_row[col]
                            processed = bcss_integration._process_mapping_value(value, notes)
                            print(f"    Found similar column '{col}' with value '{value}' → processed: '{processed}'")
                            break
    
    print(f"\n=== Full Transformation ===")
    payload = bcss_integration.transform_excel_row_to_api(excel_row)
    
    print(f"Product Code: {payload['productCode']}")
    print(f"Product Name: {payload['productName']}")
    print(f"Price: {payload['productPriceDTOS'][0]['price']}")
    
    print(f"\nAttributes:")
    for attr in payload['attributeValueList']:
        print(f"  ID {attr['productCategoryAttributeId']}: '{attr['attributeValue']}'")


if __name__ == "__main__":
    debug_transform() 