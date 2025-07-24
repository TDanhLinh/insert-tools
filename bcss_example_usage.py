#!/usr/bin/env python3
"""
BCSS API Integration Example Usage
Demonstrates how to use the BCSS integration to process SIM products
"""

import json
import pandas as pd
from bcss_api_integration import BCSSAPIIntegration

def main():
    """Example usage of BCSS API Integration with real scenarios"""
    
    # Configuration - Replace with your actual values
    BEARER_TOKEN = "YOUR_ACTUAL_BEARER_TOKEN_HERE"
    MAPPING_FILE = "BCSS_Mapping_Configuration.xlsx"  # Updated to use proper mapping file
    PRODUCT_DATA_FILE = "TestImportDataOuntbound.xlsx"  # Actual product data
    
    print("=== BCSS API Integration Demo ===\n")
    
    # Initialize integration
    try:
        bcss_integration = BCSSAPIIntegration(MAPPING_FILE, BEARER_TOKEN)
        print("✅ BCSS Integration initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Load Excel mapping
    try:
        mapping_data = bcss_integration.load_excel_mapping()
        print(f"✅ Loaded {len(mapping_data)} field mappings")
        
        # Show mapping summary
        print("\n📋 Field Mappings:")
        for bcss_field, mapping_info in mapping_data.items():
            excel_col = mapping_info['excel_mapping']
            notes = mapping_info['notes']
            if pd.notna(excel_col):
                print(f"  • {bcss_field} → {excel_col}")
                if pd.notna(notes):
                    print(f"    Notes: {notes}")
            else:
                print(f"  • {bcss_field} → [No mapping]")
        
    except Exception as e:
        print(f"❌ Failed to load mappings: {e}")
        return
    
    print("\n" + "="*60)
    
    # Example 1: Process the actual product data file
    print("\n📦 Example 1: Processing actual product data from Excel")
    
    try:
        # Process the actual product data file
        results = bcss_integration.process_excel_file(PRODUCT_DATA_FILE, dry_run=True)
        
        print(f"✅ Processed {len(results)} products from {PRODUCT_DATA_FILE}")
        
        for i, result in enumerate(results, 1):
            print(f"\nProduct {i}:")
            print(f"  Status: {result['status']}")
            if 'product_code' in result:
                print(f"  Product Code: {result['product_code']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
        
        # Show detailed payload for first product
        if results and results[0]['status'] == 'dry_run':
            print(f"\n📄 Sample API Payload for Product 1:")
            payload = results[0]['payload']
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            
            # Show attribute details
            print(f"\n🔧 Attribute Details:")
            for attr in payload['attributeValueList']:
                attr_id = attr['productCategoryAttributeId']
                attr_value = attr['attributeValue']
                print(f"  Attribute {attr_id}: '{attr_value}'")
            
    except Exception as e:
        print(f"❌ Failed to process Excel file: {e}")
    
    print("\n" + "="*60)
    
    # Example 2: Create a single product with test data
    print("\n📦 Example 2: Creating a single test product")
    
    test_product = {
        "SKUID (note- Nền màu đỏ là trùng, text màu nâu chưa có giá nhập, )": "TEST001",
        "Days": "30",
        "Product Name Short": "Test Vietnam 30-Day Data Plan",
        "High Speed Data (MB or GB or GB/day)": "5GB",
        "Package type": "Prepaid",
        "Throttled Speed (kbps)": "128",
        "Hotspot sharing": "Support",
        "Support eSIM/Sim Card": "eSIM",
        "National Area": "Vietnam",
        "Telco": "Viettel",
        "Giá bán 26.5 ( THM đề xuất)": "50000"
    }
    
    # Test with dry run first
    result = bcss_integration.create_single_product(test_product, dry_run=True)
    
    if result['status'] == 'dry_run':
        print("✅ Dry run successful!")
        print(f"Product Code: {result['product_code']}")
        print("\n📄 Generated API Payload (basic info):")
        payload = result['payload']
        print(f"  Product Name: {payload['productName']}")
        print(f"  Product Code: {payload['productCode']}")
        print(f"  Price: {payload['productPriceDTOS'][0]['price']}")
        print(f"  Attributes: {len(payload['attributeValueList'])} items")
    else:
        print(f"❌ Dry run failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    
    # Example 3: Demonstrate error handling
    print("\n🔧 Example 3: Error handling demonstration")
    
    # Test with invalid data
    invalid_product = {
        "SKUID (note- Nền màu đỏ là trùng, text màu nâu chưa có giá nhập, )": "",  # Empty SKUID
        "Days": "invalid_days",  # Invalid number
        "Product Name Short": "",  # Empty name
    }
    
    result = bcss_integration.create_single_product(invalid_product, dry_run=True)
    print(f"Invalid product test - Status: {result['status']}")
    
    if result['status'] == 'dry_run':
        print("✅ System handled invalid data gracefully")
        print(f"Generated Product Code: {result['product_code']}")
    elif result['status'] == 'failed':
        print(f"❌ Expected failure: {result['error']}")
    
    print("\n" + "="*60)
    
    # Example 4: Show field processing logic
    print("\n🔄 Example 4: Field processing logic demonstration")
    
    test_values = [
        ("Support", "Should become '1'"),
        ("Không bắt buộc", "Should become '0'"),
        ("Trống", "Should become None"),
        ("", "Should become None"),
        ("Normal value", "Should stay as 'Normal value'")
    ]
    
    print("Testing field value processing:")
    for value, expected in test_values:
        processed = bcss_integration._process_mapping_value(value)
        print(f"  '{value}' → '{processed}' ({expected})")
    
    print("\n🎉 Demo completed!")
    print("\nNext steps:")
    print("1. Replace 'YOUR_ACTUAL_BEARER_TOKEN_HERE' with your real token")
    print(f"2. Review and adjust mapping in {MAPPING_FILE} if needed")
    print(f"3. Add more product data to {PRODUCT_DATA_FILE}")
    print("4. Set dry_run=False to make actual API calls")
    print("5. Monitor logs for processing status")
    
    print(f"\n📋 API Endpoint: https://api.bcss-vnsky-test.vissoft.vn/catalog-service/private/api/v1/product")
    print(f"📋 Method: POST")
    print(f"📋 Authentication: Bearer Token Required")


if __name__ == "__main__":
    main() 