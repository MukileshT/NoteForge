# COMPLETE_FIX.ps1 - Final fix for all import issues

# Fix progress_tracker.py (was missing gui. prefix)
@"
import tkinter as tk
from tkinter import ttk

class ProgressWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Processing...")
        self.window.geometry("400x150")
        self.window.transient(parent)
        self.window.grab_set()
        self.label = tk.Label(self.window, text="Starting...")
        self.label.pack(pady=20)
        self.progress = ttk.Progressbar(self.window, length=300, mode='determinate')
        self.progress.pack(pady=20)
        self.window.update()
    
    def update(self, message: str, progress: float):
        self.label.config(text=message)
        self.progress['value'] = progress * 100
        self.window.update()
    
    def close(self):
        self.window.destroy()
"@ | Out-File -FilePath "src/gui/progress_tracker.py" -Encoding UTF8

Write-Host "✅ Fixed progress_tracker.py" -ForegroundColor Green
Write-Host ""
Write-Host "Now run: python main.py" -ForegroundColor Cyan