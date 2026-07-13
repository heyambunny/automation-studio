# services/excel_reader.py
import pandas as pd
import openpyxl
import re
from typing import Optional, Tuple

class ExcelReader:
    """Reads Excel files and extracts summary tables"""
    
    @staticmethod
    def detect_active_range(file_path: str, sheet_name: str, start_cell: str) -> Optional[pd.DataFrame]:
        """
        Read data starting from a cell and detect the contiguous range.
        Returns DataFrame or None.
        """
        try:
            col_letter = ''.join(c for c in start_cell if c.isalpha())
            row_number = int(''.join(c for c in start_cell if c.isdigit()))
            
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            col_index = openpyxl.utils.column_index_from_string(col_letter) - 1
            row_index = row_number - 1
            
            if row_index >= len(df) or col_index >= len(df.columns):
                return None
            
            sub_df = df.iloc[row_index:, col_index:]
            sub_df = sub_df.dropna(how='all')
            
            if sub_df.empty:
                return None
            
            sub_df.columns = sub_df.iloc[0]
            sub_df = sub_df.iloc[1:]
            sub_df = sub_df.reset_index(drop=True)
            
            return sub_df
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    @staticmethod
    def dataframe_to_html(df: pd.DataFrame) -> str:
        """Convert DataFrame to styled HTML table"""
        if df is None or df.empty:
            return "<p>No data available.</p>"
        
        html = '<table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:13px;">'
        
        # Header row - Yellow
        html += '<thead><tr style="background-color:#FFD700;color:#333;font-weight:bold;">'
        for col in df.columns:
            html += f'<th style="padding:8px 12px;text-align:left;border:1px solid #ddd;">{col}</th>'
        html += '</tr></thead>'
        
        # Data rows with alternating colors
        html += '<tbody>'
        for i, row in df.iterrows():
            bg = '#f9f9f9' if i % 2 == 0 else 'white'
            html += f'<tr style="background-color:{bg};">'
            for val in row:
                html += f'<td style="padding:8px 12px;border:1px solid #ddd;">{val}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        
        # Add spacing around table
        html = '<br>' + html + '<br>'
        
        return html
    
    @staticmethod
    def dataframe_to_text(df: pd.DataFrame) -> str:
        """Convert DataFrame to plain text table"""
        if df is None or df.empty:
            return "No data available."
        return df.to_string(index=False)