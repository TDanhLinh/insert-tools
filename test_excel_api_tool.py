#!/usr/bin/env python3
"""
Unit tests for ExcelAPITool
"""

import pytest
import pandas as pd
import requests
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import json
import warnings

from excel_api_tool import ExcelAPITool, APIConfig


class TestAPIConfig:
    """Test cases for APIConfig class"""
    
    def test_api_config_default_headers(self):
        """Test APIConfig with default headers"""
        config = APIConfig(url="https://test.com")
        assert config.url == "https://test.com"
        assert config.method == "POST"
        assert config.headers == {"Content-Type": "application/json"}
        assert config.auth is None
    
    def test_api_config_custom_headers(self):
        """Test APIConfig with custom headers"""
        custom_headers = {"Authorization": "Bearer token", "X-API-Key": "key"}
        config = APIConfig(url="https://test.com", headers=custom_headers)
        assert config.headers == custom_headers
    
    def test_api_config_with_auth(self):
        """Test APIConfig with authentication"""
        config = APIConfig(
            url="https://test.com", 
            auth=("username", "password"),
            method="PUT"
        )
        assert config.auth == ("username", "password")
        assert config.method == "PUT"


class TestExcelAPITool:
    """Test cases for ExcelAPITool class"""
    
    @pytest.fixture
    def sample_excel_file(self):
        """Create a temporary Excel file for testing"""
        # Create sample data
        data = {
            'Product Name': ['Product A', 'Product B', 'Product C'],
            'Price': [100, 200, 300],
            'Category': ['Electronics', 'Books', 'Clothing'],
            'Description': ['Device', 'Manual', 'Shirt']
        }
        df = pd.DataFrame(data)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        try:
            os.unlink(temp_file.name)
        except (OSError, PermissionError):
            pass  # File might be locked on Windows
    
    @pytest.fixture
    def sample_multi_sheet_excel(self):
        """Create a temporary Excel file with multiple sheets"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file.close()  # Close immediately to avoid Windows file locking
        
        with pd.ExcelWriter(temp_file.name) as writer:
            # Sheet 1
            data1 = {
                'Name': ['Item 1', 'Item 2'],
                'Value': [10, 20]
            }
            pd.DataFrame(data1).to_excel(writer, sheet_name='Sheet1', index=False)
            
            # Sheet 2
            data2 = {
                'Code': ['A001', 'B002'],
                'Amount': [500, 600]
            }
            pd.DataFrame(data2).to_excel(writer, sheet_name='Sheet2', index=False)
        
        yield temp_file.name
        
        # Cleanup
        try:
            os.unlink(temp_file.name)
        except (OSError, PermissionError):
            pass  # File might be locked on Windows
    
    @pytest.fixture
    def tool_with_sample_data(self, sample_excel_file):
        """Create ExcelAPITool instance with sample data loaded"""
        tool = ExcelAPITool(sample_excel_file)
        tool.load_excel_data()
        return tool
    
    def test_init(self, sample_excel_file):
        """Test tool initialization"""
        tool = ExcelAPITool(sample_excel_file)
        assert tool.excel_file_path == Path(sample_excel_file)
        assert tool.data is None
        assert tool.column_mapping == {}
    
    def test_load_excel_data(self, sample_excel_file):
        """Test loading Excel data"""
        tool = ExcelAPITool(sample_excel_file)
        data = tool.load_excel_data()
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 3
        assert list(data.columns) == ['Product Name', 'Price', 'Category', 'Description']
        assert data.iloc[0]['Product Name'] == 'Product A'
    
    def test_load_excel_data_specific_sheet(self, sample_multi_sheet_excel):
        """Test loading data from specific sheet"""
        tool = ExcelAPITool(sample_multi_sheet_excel)
        data = tool.load_excel_data(sheet_name='Sheet2')
        
        assert len(data) == 2
        assert list(data.columns) == ['Code', 'Amount']
        assert data.iloc[0]['Code'] == 'A001'
    
    def test_load_excel_data_file_not_found(self):
        """Test loading non-existent file"""
        tool = ExcelAPITool("non_existent_file.xlsx")
        
        with pytest.raises(Exception):
            tool.load_excel_data()
    
    def test_get_sheet_names(self, sample_multi_sheet_excel):
        """Test getting sheet names"""
        tool = ExcelAPITool(sample_multi_sheet_excel)
        sheets = tool.get_sheet_names()
        
        assert isinstance(sheets, list)
        assert 'Sheet1' in sheets
        assert 'Sheet2' in sheets
    
    def test_preview_data(self, tool_with_sample_data):
        """Test data preview"""
        preview = tool_with_sample_data.preview_data(2)
        
        assert isinstance(preview, pd.DataFrame)
        assert len(preview) == 2
        assert preview.iloc[0]['Product Name'] == 'Product A'
        assert preview.iloc[1]['Product Name'] == 'Product B'
    
    def test_preview_data_no_data_loaded(self):
        """Test preview when no data is loaded"""
        tool = ExcelAPITool("dummy_path.xlsx")
        
        with pytest.raises(ValueError, match="No data loaded"):
            tool.preview_data()
    
    def test_set_column_mapping(self, tool_with_sample_data):
        """Test setting column mapping"""
        mapping = {
            'Product Name': 'name',
            'Price': 'cost',
            'Category': 'type'
        }
        
        tool_with_sample_data.set_column_mapping(mapping)
        assert tool_with_sample_data.column_mapping == mapping
    
    def test_transform_row_to_api_format(self, tool_with_sample_data):
        """Test row transformation to API format"""
        mapping = {
            'Product Name': 'name',
            'Price': 'cost',
            'Category': 'type'
        }
        tool_with_sample_data.set_column_mapping(mapping)
        
        row = tool_with_sample_data.data.iloc[0]
        api_data = tool_with_sample_data.transform_row_to_api_format(row)
        
        expected = {
            'name': 'Product A',
            'cost': 100,
            'type': 'Electronics'
        }
        assert api_data == expected
    
    def test_transform_row_with_nan_values(self, tool_with_sample_data):
        """Test row transformation with NaN values"""
        # Add NaN value to test data
        tool_with_sample_data.data.loc[0, 'Description'] = pd.NA
        
        mapping = {
            'Product Name': 'name',
            'Description': 'desc'
        }
        tool_with_sample_data.set_column_mapping(mapping)
        
        row = tool_with_sample_data.data.iloc[0]
        api_data = tool_with_sample_data.transform_row_to_api_format(row)
        
        assert api_data['name'] == 'Product A'
        assert api_data['desc'] is None
    
    def test_transform_row_missing_column(self, tool_with_sample_data):
        """Test row transformation with missing column in mapping"""
        mapping = {
            'Product Name': 'name',
            'NonExistentColumn': 'missing'
        }
        tool_with_sample_data.set_column_mapping(mapping)
        
        row = tool_with_sample_data.data.iloc[0]
        
        # Capture warnings manually
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            api_data = tool_with_sample_data.transform_row_to_api_format(row)
        
        assert api_data['name'] == 'Product A'
        assert 'missing' not in api_data
    
    @patch('excel_api_tool.requests.post')
    def test_send_to_api_post_success(self, mock_post, tool_with_sample_data):
        """Test successful POST request to API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        api_config = APIConfig(url="https://test-api.com/data")
        data = {"name": "Product A", "price": 100}
        
        response = tool_with_sample_data.send_to_api(api_config, data)
        
        mock_post.assert_called_once_with(
            "https://test-api.com/data",
            json=data,
            headers={"Content-Type": "application/json"},
            auth=None
        )
        assert response.status_code == 200
    
    @patch('excel_api_tool.requests.put')
    def test_send_to_api_put_success(self, mock_put, tool_with_sample_data):
        """Test successful PUT request to API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        
        api_config = APIConfig(url="https://test-api.com/data", method="PUT")
        data = {"name": "Product A", "price": 100}
        
        response = tool_with_sample_data.send_to_api(api_config, data)
        
        mock_put.assert_called_once_with(
            "https://test-api.com/data",
            json=data,
            headers={"Content-Type": "application/json"},
            auth=None
        )
        assert response.status_code == 200
    
    def test_send_to_api_unsupported_method(self, tool_with_sample_data):
        """Test unsupported HTTP method"""
        api_config = APIConfig(url="https://test-api.com/data", method="DELETE")
        data = {"name": "Product A"}
        
        with pytest.raises(ValueError, match="Unsupported HTTP method: DELETE"):
            tool_with_sample_data.send_to_api(api_config, data)
    
    @patch('excel_api_tool.requests.post')
    def test_send_to_api_request_exception(self, mock_post, tool_with_sample_data):
        """Test API request exception handling"""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        api_config = APIConfig(url="https://test-api.com/data")
        data = {"name": "Product A"}
        
        with pytest.raises(requests.exceptions.RequestException):
            tool_with_sample_data.send_to_api(api_config, data)
    
    @patch('excel_api_tool.requests.post')
    def test_process_all_rows_dry_run(self, mock_post, tool_with_sample_data):
        """Test processing all rows with dry run"""
        mapping = {
            'Product Name': 'name',
            'Price': 'price'
        }
        tool_with_sample_data.set_column_mapping(mapping)
        
        api_config = APIConfig(url="https://test-api.com/data")
        results = tool_with_sample_data.process_all_rows(api_config, dry_run=True)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result['row'] == i + 1
            assert result['status'] == 'dry_run'
            assert 'data' in result
        
        # Ensure no actual API calls were made
        mock_post.assert_not_called()
    
    @patch('excel_api_tool.requests.post')
    def test_process_all_rows_actual_requests(self, mock_post, tool_with_sample_data):
        """Test processing all rows with actual API requests"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        mapping = {
            'Product Name': 'name',
            'Price': 'price'
        }
        tool_with_sample_data.set_column_mapping(mapping)
        
        api_config = APIConfig(url="https://test-api.com/data")
        results = tool_with_sample_data.process_all_rows(api_config, dry_run=False)
        
        assert len(results) == 3
        assert mock_post.call_count == 3
        
        for result in results:
            assert result['status'] == 'success'
            assert result['response_status'] == 201
    
    def test_process_all_rows_no_data(self, sample_excel_file):
        """Test processing when no data is loaded"""
        tool = ExcelAPITool(sample_excel_file)  # Don't load data
        api_config = APIConfig(url="https://test-api.com/data")
        
        with pytest.raises(ValueError, match="No data loaded"):
            tool.process_all_rows(api_config)
    
    def test_process_all_rows_no_mapping(self, tool_with_sample_data):
        """Test processing when no column mapping is set"""
        api_config = APIConfig(url="https://test-api.com/data")
        
        with pytest.raises(ValueError, match="No column mapping set"):
            tool_with_sample_data.process_all_rows(api_config)
    
    @patch('excel_api_tool.requests.post')
    def test_process_all_rows_with_failures(self, mock_post, tool_with_sample_data):
        """Test processing with some API failures"""
        # Setup mock to fail on second request
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        mock_post.side_effect = [
            mock_response_success,  # First request succeeds
            mock_response_fail,     # Second request fails
            mock_response_success   # Third request succeeds
        ]
        
        mapping = {'Product Name': 'name'}
        tool_with_sample_data.set_column_mapping(mapping)
        
        api_config = APIConfig(url="https://test-api.com/data")
        results = tool_with_sample_data.process_all_rows(api_config, dry_run=False)
        
        assert len(results) == 3
        assert results[0]['status'] == 'success'
        assert results[1]['status'] == 'failed'
        assert results[2]['status'] == 'success'
        assert 'error' in results[1]


class TestIntegration:
    """Integration tests using real data scenarios"""
    
    @pytest.fixture
    def sim_outbound_mock_data(self):
        """Create mock data similar to the SIM outbound Excel file"""
        data = {
            'KHAI BÁO SẢN PHẨM TRÊN BCSS': [
                'THÔNG TIN SẢN PHẨM',
                'Mã sản phẩm', 
                'Tên sản phẩm',
                'Nhóm sản phẩm',
                'Đơn vị tính'
            ],
            'MAPPING SẢN PHẨM TRÊN FILE EXCEL VNSKY GỬI': [
                None,
                'SKUID-Days',
                'Product Name Short', 
                'SIM outbound',
                'Cái'
            ],
            'GHI CHÚ': [
                None,
                'Cột trong file sản phẩm',
                'Cột trong file sản phẩm', 
                'Giá trị cố định',
                'Text cố định'
            ]
        }
        df = pd.DataFrame(data)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        try:
            os.unlink(temp_file.name)
        except (OSError, PermissionError):
            pass  # File might be locked on Windows
    
    @patch('excel_api_tool.requests.post')
    def test_sim_outbound_integration(self, mock_post, sim_outbound_mock_data):
        """Test integration with SIM outbound-like data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        tool = ExcelAPITool(sim_outbound_mock_data)
        data = tool.load_excel_data()
        
        # Clean data (similar to example_usage.py)
        clean_data = data.dropna(how='all')
        clean_data = clean_data[clean_data['KHAI BÁO SẢN PHẨM TRÊN BCSS'].notna()]
        tool.data = clean_data
        
        # Set column mapping
        column_mapping = {
            'KHAI BÁO SẢN PHẨM TRÊN BCSS': 'product_name',
            'MAPPING SẢN PHẨM TRÊN FILE EXCEL VNSKY GỬI': 'excel_mapping',
            'GHI CHÚ': 'notes'
        }
        tool.set_column_mapping(column_mapping)
        
        # Test dry run
        api_config = APIConfig(url="https://api.example.com/products")
        results = tool.process_all_rows(api_config, dry_run=True)
        
        assert len(results) == 5
        assert all(r['status'] == 'dry_run' for r in results)
        
        # Verify data transformation
        first_result = results[0]
        assert first_result['data']['product_name'] == 'THÔNG TIN SẢN PHẨM'
        assert first_result['data']['excel_mapping'] is None
        
        second_result = results[1]
        assert second_result['data']['product_name'] == 'Mã sản phẩm'
        assert second_result['data']['excel_mapping'] == 'SKUID-Days'


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 