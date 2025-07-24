import pandas as pd
import requests
import json
import logging
import pprint
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from excel_api_tool import ExcelAPITool, APIConfig

# Define CustomFormatter before its first use
class CustomFormatter(logging.Formatter):
    """Custom log formatter for well-looking logs"""
    def format(self, record):
        # Add section dividers for major events
        msg = super().format(record)
        if record.levelno == logging.INFO and (
            'Loaded' in msg or 'Processing' in msg or 'Successfully created product' in msg or 'API error' in msg or 'API request failed' in msg
        ):
            msg = f"\n{'='*80}\n{msg}\n{'='*80}"
        return msg

# Configure logging
log_formatter = CustomFormatter(
    fmt='[%(asctime)s] [%(levelname)s]\n%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler = logging.FileHandler('bcss_api_integration_log.txt', encoding='utf-8')
file_handler.setFormatter(log_formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
# Remove all handlers associated with the logger object
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)

class BCSSAPIIntegration:
    """Specialized integration for BCSS API with Excel mapping"""
    
    def __init__(self, excel_file_path: str, bearer_token: str):
        """
        Initialize BCSS API integration
        
        Args:
            excel_file_path (str): Path to the Excel mapping file
            bearer_token (str): Bearer token for API authentication
        """
        self.excel_tool = ExcelAPITool(excel_file_path)
        self.bearer_token = bearer_token
        self.api_config = self._setup_api_config()
        self.excel_data = None
        self.mapping_data = {}
        
    def _setup_api_config(self) -> APIConfig:
        """Setup BCSS API configuration with new URL and headers from curl"""
        return APIConfig(
            url="https://api-bcss-private.vnsky.vn/catalog-service/private/api/v1/product",
            method="POST",
            headers={
                'accept': '*',
                'accept-language': 'vi-VN',
                'authorization': f'Bearer {self.bearer_token}',
                'origin': 'https://bcss.vnsky.vn',
                'priority': 'u=1, i',
                'referer': 'https://bcss.vnsky.vn/',
                'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                'Content-Type': 'application/json'
            }
        )
    
    def load_excel_mapping(self):
        """Load and parse Excel mapping data"""
        self.excel_data = self.excel_tool.load_excel_data()
        
        # Clean data - remove empty rows
        clean_data = self.excel_data.dropna(how='all')
        clean_data = clean_data[clean_data['KHAI BÁO SẢN PHẨM TRÊN BCSS'].notna()]
        
        # Create mapping dictionary
        for _, row in clean_data.iterrows():
            bcss_field = row['KHAI BÁO SẢN PHẨM TRÊN BCSS']
            excel_mapping = row['MAPPING SẢN PHẨM TRÊN FILE EXCEL VNSKY GỬI']
            notes = row['GHI CHÚ']
            
            self.mapping_data[bcss_field] = {
                'excel_mapping': excel_mapping,
                'notes': notes
            }
        
        logger.info(f"Loaded {len(self.mapping_data)} field mappings")
        return self.mapping_data
    
    def _get_default_api_payload(self) -> Dict[str, Any]:
        """Get default API payload structure (updated: fromDate, toDate, weight = null)"""
        return {
            "productCode": "",
            "productName": "",
            "parentId": 561,  # Default from curl
            "productUom": "01",  # Default unit
            "weight": None,
            "checkQuantity": 1,
            "checkSerial": 1,
            "productStatus": 1,
            "productDescription": "",
            "productCategoryId": 101,  # Default category for SIM outbound
            "productPriceDTOS": [
                {
                    "price": 0,
                    "fromDate": None,  # Set to null
                    "toDate": None,    # Set to null
                    "id": None
                }
            ],
            "productVatDTOS": [
                {
                    "price": 10,  # Default VAT 10%
                    "fromDate": None,  # Set to null
                    "toDate": None,    # Set to null
                    "id": None
                }
            ],
            "attributeValueList": [
                # Default attribute structure - will be populated based on mapping
            ],
            "productDescriptionEn": "",
            "id": None,
            "productType": 1
        }
    
    def _get_attribute_mapping(self) -> Dict[str, int]:
        """Map BCSS fields to productCategoryAttributeId only (id is always None)"""
        return {
            "Dung lượng tốc độ cao": 101,
            "Loại gói": 102,
            "eKYC (Xác minh danh tính)": 103,
            "Hết tốc độ cao giảm xuống": 104,
            "Chia sẻ Wifi": 105,
            "Loại SIM": 106,
            "Phạm vi phủ sóng": 107,
            "SKUID": 108,
            "Số ngày sử dụng": 109,
            "Nhà cung cấp": 110
        }
    
    def _get_national_area_mapping(self) -> dict:
        """Return a mapping from National Area names to codes (provided by user)"""
        return {
            "Thailand": 21,
            "Japan": 27,
            "Taiwan": 32,
            "Vietnam": 35,
            "Netherlands": 49,
            "Belgium": 50,
            "Spain": 52,
            "Estonia": 67,
            "Asia 10 countries": 98,
            "USA, Canada": 115,
            "Madagascar": 125,
            "Brazil": 22,
            "Egypt": 24,
            "India": 25,
            "Philippines": 31,
            "UAE": 33,
            "USA": 34,
            "HongKong": 36,
            "Malaysia": 38,
            "Singapore": 39,
            "Sri Lanka": 43,
            "Uzbekistan": 44,
            "Greece": 48,
            "France": 51,
            "Hungary": 53,
            "Croatia": 54,
            "Italy": 55,
            "Switzerland": 57,
            "Czech": 58,
            "United Kingdom": 60,
            "Norway": 63,
            "Portugal": 70,
            "Luxembourg": 71,
            "Republic of Ireland": 72,
            "Iceland": 73,
            "Turkey": 77,
            "Liechtenstein": 79,
            "Kuwait": 81,
            "Kazakhstan": 84,
            "Nicaragua": 87,
            "Peru": 89,
            "Argentina": 90,
            "Chile": 91,
            "Columbia": 92,
            "Ecuador": 93,
            "French Guiana": 94,
            "Mexico": 96,
            "Canada": 97,
            "Asia 19 countries": 100,
            "China Mainland, Macao": 105,
            "Singapore, Malaysia, Thailand": 113,
            "South America 11 countries": 161,
            "Denmark": 61,
            "Lithuania": 65,
            "Latvia": 66,
            "Australia, New Zealand": 102,
            "Brazil, Chile": 103,
            "China Mainland, Hong Kong, Macao": 104,
            "Europe 33 Countries": 106,
            "Austria": 107,
            "Indonesia, Singapore, Malaysia, Thailand": 109,
            "Jordan, Kuwait, Oman": 110,
            "Singapore, Malaysia, Indonesia": 112,
            "World Primary 70 Countries": 117,
            "Saudi Arabia": 118,
            "Qatar": 119,
            "New Zealand": 120,
            "Morocco": 121,
            "Tunisia": 122,
            "Seychelles": 123,
            "Kenya": 124,
            "South Africa": 126,
            "Costa Rica": 127,
            "Macau": 37,
            "Cambodia": 40,
            "Mongolia": 30,
            "New Zealnd": 47,
            "Slovakia": 59,
            "Poland": 68,
            "Malta": 74,
            "Cyprus": 75,
            "Jordan": 80,
            "Russia": 83,
            "Asia 14 countries": 99,
            "China Mainland": 23,
            "Israel": 26,
            "Korea": 28,
            "Laos": 29,
            "Indonesia": 41,
            "Pakistan": 42,
            "Kyrgyzstan": 45,
            "Australia": 46,
            "Romania": 56,
            "Sweden": 62,
            "Finland": 64,
            "Germany": 69,
            "Bulgari": 76,
            "Slovenia": 78,
            "Oman": 82,
            "Martinique Island": 85,
            "El Salvado": 86,
            "Panama": 88,
            "Uruguay": 95,
            "Asia 6 countries": 101,
            "Hong Kong, Macao": 108,
            "Russia, Kazakhstan, Uzbekistan, Pakistan": 111,
            "South America 12 countries": 114,
            "USA, Mexico": 116
        }
    
    def _process_mapping_value(self, mapping_value: Any, notes: str = "") -> Any:
        """
        Process mapping value according to business rules
        
        Args:
            mapping_value: Value from Excel mapping
            notes: Notes from Excel for additional context
            
        Returns:
            Processed value according to business rules
        """
        if pd.isna(mapping_value) or mapping_value == "Trống" or mapping_value == "":
            return None
            
        # Handle support logic
        if isinstance(mapping_value, str):
            mapping_str = mapping_value.lower().strip()
            if "support" in mapping_str:
                return "1"
            elif notes and "support = có" in notes.lower():
                return "1" if mapping_str == "có" or mapping_str == "yes" else "0"
            elif "không bắt buộc" in mapping_str:
                return "0"
        
        return str(mapping_value)
    
    def transform_excel_row_to_api(self, excel_row: pd.Series) -> Dict[str, Any]:
        """
        Transform Excel row data to BCSS API format
        """
        payload = self._get_default_api_payload()
        attribute_mapping = self._get_attribute_mapping()
        national_area_map = self._get_national_area_mapping()

        # Map basic fields
        field_mappings = {
            "Mã sản phẩm": "productCode",
            "Tên sản phẩm": "productName", 
            "SKY package code": "pckCode",
            # "Khối lượng": "weight",  # handled below
            # "Mô tả tiếng Việt": "productDescription",  # handled below
            # "Mô tả tiếng Anh": "productDescriptionEn",  # handled below
        }

        # Apply field mappings
        for bcss_field, api_field in field_mappings.items():
            if bcss_field in self.mapping_data:
                excel_col = self.mapping_data[bcss_field]['excel_mapping']
                notes = self.mapping_data[bcss_field]['notes']
                if pd.notna(excel_col) and excel_col in excel_row.index:
                    value = self._process_mapping_value(excel_row[excel_col], notes)
                    if value is not None:
                        payload[api_field] = value

        # Set productDescription to encoded string
        payload["productDescription"] = "Thời gian sử dụng là số ngày kể từ ngày kích hoạt"
        payload["productDescriptionEn"] = "The usage period is the number of days from the activation date."
        # Remove weight from payload if present
        if "weight" in payload:
            del payload["weight"]

        # Handle price mapping
        if "Giá hàng hóa" in self.mapping_data:
            price_col = self.mapping_data["Giá hàng hóa"]['excel_mapping']
            if pd.notna(price_col) and price_col in excel_row.index:
                price_value = excel_row[price_col]
                if pd.notna(price_value):
                    try:
                        payload["productPriceDTOS"][0]["price"] = float(price_value)
                    except (ValueError, TypeError):
                        payload["productPriceDTOS"][0]["price"] = 0

        # Handle VAT mapping
        if "VAT" in self.mapping_data:
            vat_col = self.mapping_data["VAT"]['excel_mapping']
            if pd.notna(vat_col) and vat_col in excel_row.index:
                vat_value = excel_row[vat_col]
                if pd.notna(vat_value):
                    try:
                        payload["productVatDTOS"][0]["price"] = float(vat_value)
                    except (ValueError, TypeError):
                        payload["productVatDTOS"][0]["price"] = 10  # Default VAT

        # Handle attributes with column name matching
        attribute_list = []
        for bcss_field, product_category_attribute_id in attribute_mapping.items():
            if bcss_field in self.mapping_data:
                excel_col = self.mapping_data[bcss_field]['excel_mapping']
                notes = self.mapping_data[bcss_field]['notes']
                attribute_value = ""
                if pd.notna(excel_col):
                    # Special logic for Hotspot sharing
                    if bcss_field == "Chia sẻ Wifi":
                        if excel_col in excel_row.index:
                            value = str(excel_row[excel_col]).lower()
                            attribute_value = "1" if "support" in value else "0"
                        else:
                            attribute_value = "0"
                    # Special logic for National Area
                    elif bcss_field == "Phạm vi phủ sóng":
                        if excel_col in excel_row.index:
                            area = str(excel_row[excel_col])
                            attribute_value = national_area_map.get(area, area)
                        else:
                            attribute_value = ""
                    # Fixed values
                    elif excel_col == "Không bắt buộc":
                        attribute_value = "0"
                    elif excel_col == "SIM outbound":
                        attribute_value = "SIM outbound"
                    elif excel_col == "Cái":
                        attribute_value = "Cái"
                    elif "Text cố định" in str(notes):
                        if excel_col in excel_row.index and pd.notna(excel_row[excel_col]) and str(excel_row[excel_col]).strip() != "":
                            attribute_value = self._process_mapping_value(excel_row[excel_col], notes)
                        else:
                            attribute_value = excel_col
                    elif excel_col in excel_row.index:
                        value = self._process_mapping_value(excel_row[excel_col], notes)
                        if value is not None:
                            attribute_value = value
                    else:
                        # Try to find column with similar name
                        for col in excel_row.index:
                            if excel_col.lower() in col.lower() or col.lower() in excel_col.lower():
                                value = self._process_mapping_value(excel_row[col], notes)
                                if value is not None:
                                    attribute_value = value
                                break
                # Post-process attribute values for special cases
                # 1. productCategoryAttributeId 104: handle number, Mbps, ∞, -1
                if product_category_attribute_id == 104:
                    if attribute_value in ['∞', '-1']:
                        attribute_value = None
                    elif isinstance(attribute_value, (int, float)) or (isinstance(attribute_value, str) and attribute_value.isdigit()):
                        attribute_value = f"{int(float(attribute_value))} Kbps"
                    elif isinstance(attribute_value, str):
                        val = attribute_value.replace(' ', '')
                        if val.lower() == '1mbps':
                            attribute_value = '1 Mbps'
                        elif 'mbps' in val.lower():
                            attribute_value = attribute_value.replace('Mbps', ' Mbps').replace('mbps', ' Mbps')
                        elif 'kbps' in val.lower():
                            attribute_value = attribute_value.replace('Kbps', ' Kbps').replace('kbps', ' Kbps')
                # 2. productCategoryAttributeId 106: 'eSIM' -> 2, 'Sim Card' -> 1
                if product_category_attribute_id == 106:
                    if str(attribute_value).strip().lower() == 'esim':
                        attribute_value = '2'
                    elif str(attribute_value).strip().lower() == 'sim card':
                        attribute_value = '1'
                # 3. productCategoryAttributeId 107 and 109: ensure integer if possible, else None
                if product_category_attribute_id in [107, 109]:
                    try:
                        if isinstance(attribute_value, str):
                            attribute_value = attribute_value.strip()
                        if attribute_value == '' or attribute_value is None:
                            attribute_value = None
                        else:
                            attribute_value = int(float(attribute_value))
                    except Exception:
                        attribute_value = None
                # 4. productCategoryAttributeId 101 (High Speed Data): if value is '∞', map to None
                if product_category_attribute_id == 101 and str(attribute_value).strip() == '∞':
                    attribute_value = None
                attribute_list.append({
                    "id": None,
                    "productCategoryAttributeId": product_category_attribute_id,
                    "productCategoryAttributeValueId": "",
                    "attributeValue": attribute_value
                })
        payload["attributeValueList"] = attribute_list

        # Generate product code as SKUID-Days
        skuid_value = ""
        days_value = ""
        for col in excel_row.index:
            if "SKUID" in col.upper() and pd.notna(excel_row[col]):
                skuid_value = str(excel_row[col])
            if col.strip().lower() == "days" and pd.notna(excel_row[col]):
                days_value = str(excel_row[col])
        if skuid_value and days_value:
            payload["productCode"] = f"{skuid_value}-{days_value}"
        elif skuid_value:
            payload["productCode"] = skuid_value
        else:
            payload["productCode"] = f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return payload
    
    def process_excel_file(self, excel_data_file: str, dry_run: bool = True, start_row: int = 1) -> List[Dict[str, Any]]:
        """
        Process Excel data file and send to BCSS API
        Args:
            excel_data_file (str): Path to Excel file
            dry_run (bool): If True, do not send to API
            start_row (int): 1-based index of first row to process (default 1 = all rows)
        """
        # Load product data
        data_tool = ExcelAPITool(excel_data_file)
        product_data = data_tool.load_excel_data()
        logger.info(f"Processing {len(product_data)} products from {excel_data_file}, starting from row {start_row}")
        results = []
        for index, row in product_data.iterrows():
            # index is 0-based, so row number is index+1
            if (index + 1) < start_row:
                continue
            try:
                # Transform row to API format
                api_payload = self.transform_excel_row_to_api(row)
                if dry_run:
                    logger.info(f"\n{'-'*40}\nProduct {index + 1} [DRY RUN]:\n  Product Code: {api_payload['productCode']}\n  Payload:\n{json.dumps(api_payload, indent=2, ensure_ascii=False)}\n{'-'*40}")
                    results.append({
                        "row": index + 1,
                        "product_code": api_payload['productCode'],
                        "status": "dry_run",
                        "payload": api_payload
                    })
                else:
                    # Send to API
                    try:
                        response = self.excel_tool.send_to_api(self.api_config, api_payload)
                        response_body = response.text if response.content else None
                        results.append({
                            "row": index + 1,
                            "product_code": api_payload['productCode'],
                            "status": "success" if response.ok else "failed",
                            "response_status": response.status_code,
                            "response_data": response.json() if response.content else None,
                            "response_body": response_body
                        })
                        if response.ok:
                            logger.info(f"\n{'*'*20} SUCCESSFULLY CREATED PRODUCT {'*'*20}\nProduct Code: {api_payload['productCode']}\n{'*'*60}")
                        else:
                            logger.error(f"\n{'!'*20} API ERROR {'!'*20}\nRow: {index + 1}\nStatus: {response.status_code}\nBody: {response_body}\n{'!'*60}")
                            if response.status_code == 400:
                                logger.error(f"[400 ERROR] Product Code with error: {api_payload['productCode']}")
                    except requests.RequestException as e:
                        error_body = None
                        if hasattr(e, 'response') and e.response is not None:
                            error_body = e.response.text
                        logger.error(f"API request failed: {e}\nResponse body: {error_body}")
                        results.append({
                            "row": index + 1,
                            "product_code": api_payload.get('productCode', '-'),
                            "status": "failed",
                            "error": str(e),
                            "response_body": error_body
                        })
            except Exception as e:
                logger.error(f"\n{'!'*20} FAILED TO PROCESS ROW {'!'*20}\nRow: {index + 1}\nError: {str(e)}\n{'!'*60}")
                results.append({
                    "row": index + 1,
                    "status": "failed",
                    "error": str(e)
                })
        # Add summary section to log
        summary = f"\n{'#'*40} PROCESSING SUMMARY {'#'*40}\nTotal processed: {len(results)}\nSuccess: {sum(1 for r in results if r['status']=='success')}\nFailed: {sum(1 for r in results if r['status']=='failed')}\nDry run: {sum(1 for r in results if r['status']=='dry_run')}\n{'#'*90}\n"
        logger.info(summary)
        return results
    
    def create_single_product(self, product_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        try:
            # Convert dict to Series for transformation
            row = pd.Series(product_data)
            api_payload = self.transform_excel_row_to_api(row)
            
            if dry_run:
                return {
                    "status": "dry_run",
                    "product_code": api_payload['productCode'],
                    "payload": api_payload
                }
            else:
                response = self.excel_tool.send_to_api(self.api_config, api_payload)
                return {
                    "status": "success",
                    "product_code": api_payload['productCode'],
                    "response_status": response.status_code,
                    "response_data": response.json() if response.content else None
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

def delete_products_by_id_range(start_id: int, end_id: int, bearer_token: str) -> list:
    """
    Delete products by a range of IDs using the BCSS API DELETE endpoint.
    Args:
        start_id (int): The starting product ID to delete (inclusive).
        end_id (int): The ending product ID to delete (inclusive).
        bearer_token (str): The Bearer token for authentication.
    Returns:
        list: List of results for each delete operation (status, response, etc.)
    """
    import requests
    import pprint
    results = []
    headers = {
        'accept': '*',
        'accept-language': 'vi-VN',
        'authorization': f'Bearer {bearer_token}',
        'origin': 'https://bcss.vnsky.vn',
        'priority': 'u=1, i',
        'referer': 'https://bcss.vnsky.vn/',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    }
    for product_id in range(start_id, end_id + 1):
        url = f"https://api-bcss-private.vnsky.vn/catalog-service/private/api/v1/product/{product_id}"
        try:
            response = requests.delete(url, headers=headers)
            logger.info(f"\n{'='*80}\n[DELETE] Product ID: {product_id}\n  Status: {response.status_code}\n  Response:\n{pprint.pformat(response.json() if response.content else response.text, indent=2, width=120)}\n{'='*80}")
            results.append({
                'product_id': product_id,
                'status': 'success' if response.ok else 'failed',
                'response_status': response.status_code,
                'response_data': response.json() if response.content else None,
                'response_body': response.text
            })
        except Exception as e:
            logger.error(f"[DELETE] Failed to delete product {product_id}: {str(e)}")
            results.append({
                'product_id': product_id,
                'status': 'failed',
                'error': str(e)
            })
    # Log summary after all deletes
    total = len(results)
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    logger.info(f"\n{'#'*40} DELETE SUMMARY {'#'*40}\nTotal attempted: {total}\nSuccess: {success}\nFailed: {failed}\n{'#'*90}\n")
    return results

def main():
    # Configuration
    bearer_token = "eyJraWQiOiJ2bnNreSIsInR5cCI6IkpXVCIsImFsZyI6IlJTNTEyIn0.eyJzdWIiOiIwMDAwMDAwMDAwMDBcXGxpbmgxMTMyMDAzQGdtYWlsLmNvbSIsImlzcyI6Imh0dHBzOi8vYXBpLWJjc3MtcHJpdmF0ZS52bnNreS52bi9hZG1pbi1zZXJ2aWNlIiwibGFzdF9tb2RpZmllZF9kYXRlIjoxNzQ4NDkyMzI0LCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJsaW5oMTEzMjAwM0BnbWFpbC5jb20iLCJzc29fcHJvdmlkZXIiOiJHT09HTEUiLCJjbGllbnRfaWQiOiIwMDAwMDAwMDAwMDAiLCJhdWQiOiJ2bnNreS1pbnRlcm5hbCIsImFwcF9uYW1lIjoiV2ViIEJDU1MgbuG7mWkgYuG7mSIsIm5iZiI6MTc0ODYwMjE3MSwidXNlcl9pZCI6IjAxSldENDczQzZNMjdRR1lXN1c2TUY4RVJGIiwiZnVsbG5hbWUiOiJEYW5oIExpbmgiLCJleHAiOjE3NDg2MDM5NzEsImlhdCI6MTc0ODYwMjE3MSwiY2xpZW50X25hbWUiOiJWTlNLWSIsInVzZXJfYXV0aG9yaXRpZXMiOlsiU0NPUEVfREVGQVVMVCJdLCJhcHBfaWQiOiIyMjY2Nzk0OC05NjQ1LTQ2ZmUtOGZmMy01Mzk2ZmE5M2JmOTEiLCJqdGkiOiJkMzFlOWNlZS03NTI5LTRjYWItODIzOS1lNDAxY2E1MjI5MzEiLCJjbGllbnRfY29kZSI6IlZOU0tZIiwidXNlcm5hbWUiOiJsaW5oMTEzMjAwM0BnbWFpbC5jb20iLCJhcHBfY29kZSI6InZuc2t5LWludGVybmFsIn0.BcGURic5Fp4XVRW07HcCamGSJ3uXG5XR0r6ZHvPQYcy89vI_Y-CnP_vaGcCM2A2R9VwJlCBiSCx5HAg1b6Tlysifrtgal2G--nQgbDmcCoBJ2IYARQdooqFoyOIvb_o6eyP2o-Ybg6QIV7vs9slWHcwms63IXnFwLuxZJTuywpq4GiI42Psk9m0y13SZY0cAVoCxatRIEd5QA9P-TQzNKgcKU_GnuAO-qU3dqlFQyWWhDJdjWV3eaSD0BhIqNlzbB74-SXLwNHIGb7ZsI2-SB3ut1DV3pp1QkjHBUEiipP-qe7_jZaXNGbBXdpXaprocV43MvOE7nFGpY37v7dVzMaDgI91nxJM_pQlNqQy7xZZthUnYXztKc6ZN-mv2NuOv7fNuUEAqR-xXmz0e860_D0Vucp4EV1xUL9f5Ymindq1r3HKJvLbL2B_f1iFPpFGGesJ5N9Bgm_yE-tgBRfa8SRVwARJluoBzhEuwAf4jZqxYvUXrMjNOILcqWrG1CxaUUrO7nRhXs31ClY_WOeFt5lTYN_yu7cTPd1vH6ls6coucJZG9ugXWxLrPD7M62KTOAL4BnrYzHgWxvLHgHZaPi3qiZLIJZ9-LPM9Mx8xEZO_yWehSV1yEgwsEEhywVIdXSs5PZiSKVXdKu6y81pS4TCU7v7E8g5Jp5IsMs76F-DI"  # Replace with actual token
    mapping_file = "BCSS_Mapping_Configuration.xlsx"  # Mapping config file
    # product_data_file = "TestImportDataOuntbound.xlsx"
    product_data_file = "Lỗi dữ liệu.xlsx"  # Product data file
    
    # Set the starting row (1-based, e.g. 1 = first row, 5 = start from row 5)
    start_row = 1
    
    # Initialize integration with mapping config
    bcss_integration = BCSSAPIIntegration(mapping_file, bearer_token)
    
    # Load mapping from config Excel
    bcss_integration.load_excel_mapping()
    
    # Process product data file and send to API
    results = bcss_integration.process_excel_file(product_data_file, dry_run=False, start_row=start_row)
    
    summary_lines = [
        f"\n=== API Call Results Summary (start_row={start_row}) ==="
    ]
    for res in results:
        summary_lines.append(f"Row: {res.get('row')}, Product Code: {res.get('product_code', '-')}, Status: {res['status']}")
        if res['status'] == 'success':
            summary_lines.append(f"  Response Status: {res.get('response_status')}")
            summary_lines.append(f"  Response Data: {json.dumps(res.get('response_data'), ensure_ascii=False, indent=2)}")
        elif res['status'] == 'failed':
            summary_lines.append(f"  Error: {res.get('error')}")
        elif res['status'] == 'dry_run':
            summary_lines.append(f"  Payload: {json.dumps(res.get('payload'), ensure_ascii=False, indent=2)}")
    summary_lines.append(f"\nTotal processed: {len(results)}")
    summary_lines.append(f"Success: {sum(1 for r in results if r['status']=='success')}")
    summary_lines.append(f"Failed: {sum(1 for r in results if r['status']=='failed')}")
    summary_lines.append(f"Dry run: {sum(1 for r in results if r['status']=='dry_run')}")

    logger.info("\n".join(summary_lines))

    # Example usage for delete (uncomment to use):
    # delete_result = delete_product_by_id(755, bearer_token)
    # logger.info(f"Delete result: {delete_result}")

if __name__ == "__main__":
    main() 