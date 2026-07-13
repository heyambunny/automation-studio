# services/file_scanner.py
import os
import pandas as pd
from typing import List, Dict, Optional

class FileScanner:
    """Scans folder and matches files to branch names from mapping"""
    
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
    
    def scan_folder(self) -> List[str]:
        """Get all Excel and CSV files in the folder"""
        if not os.path.exists(self.folder_path):
            return []
        
        files = []
        for f in os.listdir(self.folder_path):
            if f.endswith(('.xlsx', '.csv')):
                files.append(f)
        return files
    
    def match_branches(self, branch_names: List[str]) -> Dict[str, Optional[str]]:
        """
        Match branch names to files in folder.
        Returns {branch_name: file_path or None if not found}
        """
        available_files = self.scan_folder()
        matches = {}
        
        for branch in branch_names:
            found = None
            for file in available_files:
                # Match by file name without extension
                file_name = os.path.splitext(file)[0]
                if file_name.lower() == branch.lower():
                    found = os.path.join(self.folder_path, file)
                    break
            matches[branch] = found
        
        return matches
    
    def get_missing_branches(self, branch_names: List[str]) -> List[str]:
        """Return list of branches with no matching file"""
        matches = self.match_branches(branch_names)
        return [b for b, f in matches.items() if f is None]