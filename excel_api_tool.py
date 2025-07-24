import pandas as pd
import requests
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuration for API endpoint"""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = None
    auth: Optional[tuple] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}

class ExcelAPITool:
    """Tool to read Excel data and send to API endpoints"""
    
    def __init__(self, excel_file_path: str):
        """
        Initialize the tool with Excel file path
        
        Args:
            excel_file_path (str): Path to the Excel file
        """
        self.excel_file_path = Path(excel_file_path)
        self.data = None
        self.column_mapping = {}
        
    def load_excel_data(self, sheet_name: str = None, header_row: int = 0) -> pd.DataFrame:
        """
        Load data from Excel file
        
        Args:
            sheet_name (str): Name of the sheet to read. If None, reads the first sheet
            header_row (int): Row number to use as header (0-indexed)
            
        Returns:
            pd.DataFrame: Loaded data
        """
        try:
            if sheet_name:
                self.data = pd.read_excel(self.excel_file_path, sheet_name=sheet_name, header=header_row)
            else:
                self.data = pd.read_excel(self.excel_file_path, header=header_row)
                
            logger.info(f"Successfully loaded {len(self.data)} rows from Excel file")
            logger.info(f"Columns: {list(self.data.columns)}")
            return self.data
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise
    
    def get_sheet_names(self) -> List[str]:
        """
        Get all sheet names from the Excel file
        
        Returns:
            List[str]: List of sheet names
        """
        try:
            excel_file = pd.ExcelFile(self.excel_file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Error getting sheet names: {str(e)}")
            raise
    
    def preview_data(self, rows: int = 5) -> pd.DataFrame:
        """
        Preview the first few rows of data
        
        Args:
            rows (int): Number of rows to preview
            
        Returns:
            pd.DataFrame: Preview data
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_excel_data() first.")
        
        return self.data.head(rows)
    
    def set_column_mapping(self, mapping: Dict[str, str]):
        """
        Set mapping between Excel columns and API field names
        
        Args:
            mapping (Dict[str, str]): Mapping of Excel column names to API field names
        """
        self.column_mapping = mapping
        logger.info(f"Column mapping set: {mapping}")
    
    def transform_row_to_api_format(self, row: pd.Series) -> Dict[str, Any]:
        """
        Transform a DataFrame row to API format using column mapping
        
        Args:
            row (pd.Series): DataFrame row
            
        Returns:
            Dict[str, Any]: Transformed data for API
        """
        api_data = {}
        
        for excel_col, api_field in self.column_mapping.items():
            if excel_col in row.index:
                value = row[excel_col]
                # Handle NaN values
                if pd.isna(value):
                    api_data[api_field] = None
                else:
                    api_data[api_field] = value
            else:
                logger.warning(f"Column '{excel_col}' not found in data")
                
        return api_data
    
    def send_to_api(self, api_config: APIConfig, data: Dict[str, Any]) -> requests.Response:
        """
        Send data to API endpoint
        
        Args:
            api_config (APIConfig): API configuration
            data (Dict[str, Any]): Data to send
            
        Returns:
            requests.Response: API response
        """
        try:
            if api_config.method.upper() == "POST":
                response = requests.post(
                    api_config.url,
                    json=data,
                    headers=api_config.headers,
                    auth=api_config.auth
                )
            elif api_config.method.upper() == "PUT":
                response = requests.put(
                    api_config.url,
                    json=data,
                    headers=api_config.headers,
                    auth=api_config.auth
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {api_config.method}")
            
            response.raise_for_status()
            logger.info(f"Successfully sent data to API. Status: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def process_all_rows(self, api_config: APIConfig, batch_size: int = 1, 
                        dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Process all rows from Excel and send to API
        
        Args:
            api_config (APIConfig): API configuration
            batch_size (int): Number of rows to process in each batch
            dry_run (bool): If True, don't actually send to API
            
        Returns:
            List[Dict[str, Any]]: Results of API calls
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_excel_data() first.")
        
        if not self.column_mapping:
            raise ValueError("No column mapping set. Call set_column_mapping() first.")
        
        results = []
        failed_rows = []
        
        for index, row in self.data.iterrows():
            try:
                # Transform row to API format
                api_data = self.transform_row_to_api_format(row)
                
                if dry_run:
                    logger.info(f"Dry run - Row {index + 1}: {api_data}")
                    results.append({"row": index + 1, "data": api_data, "status": "dry_run"})
                else:
                    # Send to API
                    response = self.send_to_api(api_config, api_data)
                    results.append({
                        "row": index + 1, 
                        "data": api_data, 
                        "status": "success",
                        "response_status": response.status_code
                    })
                    
            except Exception as e:
                logger.error(f"Failed to process row {index + 1}: {str(e)}")
                failed_rows.append({"row": index + 1, "error": str(e)})
                results.append({
                    "row": index + 1, 
                    "status": "failed", 
                    "error": str(e)
                })
        
        logger.info(f"Processed {len(results)} rows. Failed: {len(failed_rows)}")
        return results


def main():
    """Example usage of the ExcelAPITool"""
    # Example configuration
    excel_file = "Mapping thông tin sản phẩm SIM outbound.xlsx"
    
    # Initialize tool
    tool = ExcelAPITool(excel_file)
    
    # Get sheet names
    try:
        sheets = tool.get_sheet_names()
        print(f"Available sheets: {sheets}")
        
        # Load data from first sheet
        data = tool.load_excel_data()
        print(f"Loaded {len(data)} rows")
        print("\nPreview:")
        print(tool.preview_data())
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 