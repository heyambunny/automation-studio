# services/excel_reader.py
import pandas as pd
import openpyxl
import re
from typing import Optional, Tuple

class ExcelReader:
    """Reads Excel files and extracts summary tables"""
    
    @staticmethod
    def detect_active_range(file_path: str, sheet_name: str, start_cell: str) -> Optional[pd.DataFrame]:
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
    def dataframe_to_html(df: pd.DataFrame, header_color: str = "#FFD700") -> str:
        if df is None or df.empty:
            return "<p>No data available.</p>"
        
        html = '<table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:13px;">'
        
        html += f'<thead><tr style="background-color:{header_color};color:#333;font-weight:bold;">'
        for col in df.columns:
            html += f'<th style="padding:8px 12px;text-align:left;border:1px solid #ddd;">{col}</th>'
        html += '</tr></thead>'
        
        html += '<tbody>'
        for i, row in df.iterrows():
            bg = '#f9f9f9' if i % 2 == 0 else 'white'
            html += f'<tr style="background-color:{bg};">'
            for col, val in row.items():
                col_lower = str(col).lower()
                if 'percentage' in col_lower or '%' in col_lower or 'pct' in col_lower or '%age' in col_lower:
                    if pd.notna(val) and isinstance(val, (int, float)):
                        val = f"{val * 100:.2f}%"
                html += f'<td style="padding:8px 12px;border:1px solid #ddd;">{val}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        
        html = '<br>' + html + '<br>'
        
        return html
    
    @staticmethod
    def dataframe_to_text(df: pd.DataFrame) -> str:
        if df is None or df.empty:
            return "No data available."
        return df.to_string(index=False)
    
    @staticmethod
    def get_cell_value(file_path: str, sheet_name: str, cell_ref: str):
        """Get a single cell value from Excel, preserving percentage formatting"""
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            ws = wb[sheet_name]
            cell = ws[cell_ref]
            
            if cell.number_format and '%' in cell.number_format:
                if cell.value is not None:
                    return f"{cell.value * 100:.1f}%"
            
            if cell.value is not None:
                return str(cell.value)
            return ""
        except:
            try:
                col_letter = ''.join(c for c in cell_ref if c.isalpha())
                row_number = int(''.join(c for c in cell_ref if c.isdigit()))
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                col_index = openpyxl.utils.column_index_from_string(col_letter) - 1
                row_index = row_number - 1
                if row_index < len(df) and col_index < len(df.columns):
                    value = df.iloc[row_index, col_index]
                    return str(value) if pd.notna(value) else ""
                return ""
            except:
                return ""