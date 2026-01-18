import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


from core.config_manager import ConfigManager
from core.pipeline import ProcessingPipeline
from gui.progress_tracker import ProgressWindow

def main():
    root = tk.Tk()
    root.title("Obsidian Notes Converter")
    root.geometry("600x400")
    
    config = ConfigManager()
    pipeline = ProcessingPipeline(config)
    
    input_files = []
    vault_path = None
    
    def select_files():
        nonlocal input_files
        files = filedialog.askopenfilenames(title="Select PDF or Images", 
                                           filetypes=[("PDF files", "*.pdf"), ("Images", "*.png *.jpg")])
        if files:
            input_files = [Path(f) for f in files]
            file_label.config(text=f"Selected: {len(input_files)} files")
    
    def select_vault():
        nonlocal vault_path
        folder = filedialog.askdirectory(title="Select Obsidian Vault")
        if folder:
            vault_path = Path(folder)
            vault_label.config(text=f"Vault: {vault_path.name}")
    
    def start_processing():
        if not input_files:
            messagebox.showerror("Error", "No files selected")
            return
        if not vault_path:
            messagebox.showerror("Error", "No vault selected")
            return
        progress_win = ProgressWindow(root)
        try:
            result = pipeline.process(input_files, vault_path, progress_win.update)
            progress_win.close()
            msg = f"Success!\n\nCreated: {result.markdown_filename}"
            if result.warnings:
                msg += f"\n\nWarnings:\n" + "\n".join(result.warnings[:5])
            messagebox.showinfo("Complete", msg)
        except Exception as e:
            progress_win.close()
            messagebox.showerror("Error", str(e))
    
    tk.Label(root, text="Obsidian Notes Converter", font=("Arial", 16, "bold")).pack(pady=20)
    tk.Button(root, text="Select PDF/Images", command=select_files, width=20).pack(pady=10)
    file_label = tk.Label(root, text="No files selected")
    file_label.pack()
    tk.Button(root, text="Select Obsidian Vault", command=select_vault, width=20).pack(pady=10)
    vault_label = tk.Label(root, text="No vault selected")
    vault_label.pack()
    tk.Button(root, text="Start Processing", command=start_processing, bg="green", fg="white", width=20, height=2).pack(pady=30)
    root.mainloop()

if __name__ == "__main__":
    main()
