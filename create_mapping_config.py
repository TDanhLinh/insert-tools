#!/usr/bin/env python3
"""
Create mapping configuration for BCSS API based on Excel structure
"""

import pandas as pd

def create_mapping_excel():
    """Create the mapping Excel file based on the API requirements"""
    
    # Based on the curl you provided and the Excel structure we observed
    mapping_data = {
        'KHAI BÁO SẢN PHẨM TRÊN BCSS': [
            'THÔNG TIN SẢN PHẨM',
            'Mã sản phẩm', 
            'Tên sản phẩm',
            'Nhóm sản phẩm',
            'Đơn vị tính',
            'SKY package code',
            'Khối lượng',
            'Mô tả tiếng Anh',
            'Mô tả tiếng Việt',
            'Loại sản phẩm',
            'Số ngày sử dụng',
            'Dung lượng tốc độ cao',
            'Loại gói',
            'eKYC (Xác minh danh tính)',
            'Hết tốc độ cao giảm xuống',
            'Chia sẻ Wifi',
            'Loại SIM',
            'Phạm vi phủ sóng',
            'SKUID',
            'Nhà cung cấp',
            'Giá sản phẩm sau thuế',
            'Giá hàng hóa',
            'Thuế suất',
            'VAT'
        ],
        'MAPPING SẢN PHẨM TRÊN FILE EXCEL VNSKY GỬI': [
            None,  # Header row
            'SKUID',  # Will be combined with Days for productCode
            'Product Name Short',
            'SIM outbound',  # Fixed value
            'Cái',  # Fixed value
            'Trống',  # Leave blank
            'Trống',  # Leave blank
            'The usage period is the number of days from the activation date.',  # Fixed text
            'Thời gian sử dụng là số ngày kể từ ngày kích hoạt',  # Fixed text
            None,  # Product type
            'Days',
            'High Speed Data (MB or GB or GB/day)',
            'Package type',
            'Không bắt buộc',  # Fixed value
            'Throttled Speed (kbps)',
            'Hotspot sharing',  # Support logic applies
            'Support eSIM/Sim Card',
            'National Area',
            'SKUID',
            'Telco',
            None,  # Calculated
            'Giá bán 26.5 ( THM đề xuất)',
            None,  # Tax rate
            10  # Fixed VAT rate
        ],
        'GHI CHÚ': [
            None,
            'Cột trong file sản phẩm - kết hợp với Days làm productCode',
            'Cột trong file sản phẩm',
            'Giá trị cố định',
            'Text cố định',
            None,
            None,
            'Text cố định',
            'Text cố định',
            None,
            'Cột trong file sản phẩm',
            'Cột trong file sản phẩm',
            'Cột trong file sản phẩm',
            'Giá trị cố định',
            'Cột trong file sản phẩm',
            'Cột trong file sản phẩm (support = có)',
            'Cột trong file sản phẩm',
            'Cột trong file sản phẩm',
            'Cột trong file sản phẩm',
            'Cột trong file sản phẩm',
            None,
            'Cột trong file sản phẩm',
            None,
            'Text cố định'
        ]
    }
    
    df = pd.DataFrame(mapping_data)
    output_file = "BCSS_Mapping_Configuration.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"✅ Created mapping configuration: {output_file}")
    print("\n📋 Mapping Summary:")
    for i, (bcss_field, excel_col, notes) in enumerate(zip(
        mapping_data['KHAI BÁO SẢN PHẨM TRÊN BCSS'],
        mapping_data['MAPPING SẢN PHẨM TRÊN FILE EXCEL VNSKY GỬI'],
        mapping_data['GHI CHÚ']
    )):
        if pd.notna(excel_col):
            print(f"  • {bcss_field} → {excel_col}")
            if pd.notna(notes):
                print(f"    Notes: {notes}")
    
    return output_file

def analyze_product_data():
    """Analyze the existing product data file"""
    try:
        product_data = pd.read_excel("TestImportDataOuntbound.xlsx")
        print(f"\n📊 Product Data Analysis:")
        print(f"  Rows: {len(product_data)}")
        print(f"  Columns: {len(product_data.columns)}")
        
        print(f"\n📋 Available Columns in Product Data:")
        for i, col in enumerate(product_data.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\n📄 Sample Data (first 3 rows):")
        print(product_data.head(3).to_string())
        
        return product_data
        
    except Exception as e:
        print(f"❌ Error reading product data: {e}")
        return None

if __name__ == "__main__":
    print("=== BCSS Mapping Configuration Generator ===\n")
    
    # Analyze existing product data
    product_data = analyze_product_data()
    
    print("\n" + "="*60)
    
    # Create mapping configuration
    mapping_file = create_mapping_excel()
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Review the mapping configuration in {mapping_file}")
    print(f"2. Update bcss_example_usage.py to use {mapping_file}")
    print(f"3. Use TestImportDataOuntbound.xlsx as your product data file")
    print(f"4. Run the BCSS integration with your Bearer token") 