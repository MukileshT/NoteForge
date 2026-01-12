"""Enhanced Main Window with Provider/OCR Selection and API Key Management"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from security.key_manager import KeyManager
from llm.provider_factory import ProviderFactory
from ocr.ocr_manager import OCRMode
from core.config_manager import ConfigManager
from core.pipeline import ProcessingPipeline
from gui.progress_tracker import ProgressWindow
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedMainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian Notes Converter - Enhanced")
        self.root.geometry("800x700")
        
        self.key_manager = KeyManager()
        self.config = ConfigManager()
        
        # State
        self.input_files = []
        self.vault_path = None
        self.current_provider = None
        self.current_ocr_mode = OCRMode.LOCAL
        
        self._build_ui()
        self._load_settings()
    
    def _build_ui(self):
        """Build the user interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Main Processing
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Process Notes")
        self._build_main_tab(main_tab)
        
        # Tab 2: Provider Settings
        provider_tab = ttk.Frame(notebook)
        notebook.add(provider_tab, text="LLM Providers")
        self._build_provider_tab(provider_tab)
        
        # Tab 3: OCR Settings
        ocr_tab = ttk.Frame(notebook)
        notebook.add(ocr_tab, text="OCR Settings")
        self._build_ocr_tab(ocr_tab)
        
        # Tab 4: API Keys
        keys_tab = ttk.Frame(notebook)
        notebook.add(keys_tab, text="API Keys")
        self._build_keys_tab(keys_tab)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _build_main_tab(self, parent):
        """Build main processing tab"""
        ttk.Label(parent, text="Obsidian Notes Converter", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # File selection
        file_frame = ttk.LabelFrame(parent, text="Input Files", padding=10)
        file_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(file_frame, text="Select PDF/Images", 
                  command=self._select_files).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(file_frame, text="No files selected")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Vault selection
        vault_frame = ttk.LabelFrame(parent, text="Obsidian Vault", padding=10)
        vault_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(vault_frame, text="Select Vault Folder", 
                  command=self._select_vault).pack(side=tk.LEFT, padx=5)
        self.vault_label = ttk.Label(vault_frame, text="No vault selected")
        self.vault_label.pack(side=tk.LEFT, padx=10)
        
        # Current settings display
        settings_frame = ttk.LabelFrame(parent, text="Current Settings", padding=10)
        settings_frame.pack(fill='x', padx=20, pady=10)
        
        self.settings_display = tk.Text(settings_frame, height=6, width=70, 
                                       state='disabled', bg='#f0f0f0')
        self.settings_display.pack()
        
        # Process button
        ttk.Button(parent, text="Start Processing", 
                  command=self._start_processing,
                  style='Accent.TButton').pack(pady=30)
    
    def _build_provider_tab(self, parent):
        """Build LLM provider configuration tab"""
        ttk.Label(parent, text="LLM Provider Configuration", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Provider selection
        provider_frame = ttk.LabelFrame(parent, text="Select Provider", padding=10)
        provider_frame.pack(fill='x', padx=20, pady=10)
        
        self.provider_var = tk.StringVar()
        providers = ProviderFactory.get_available_providers()
        
        for provider in providers:
            ttk.Radiobutton(provider_frame, text=provider.capitalize(), 
                           variable=self.provider_var, value=provider,
                           command=self._on_provider_changed).pack(anchor=tk.W, pady=2)
        
        # Model selection
        model_frame = ttk.LabelFrame(parent, text="Model Settings", padding=10)
        model_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(model_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar()
        self.model_entry = ttk.Entry(model_frame, textvariable=self.model_var, width=40)
        self.model_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(model_frame, text="Max Tokens:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=1024)
        ttk.Spinbox(model_frame, from_=256, to=8192, textvariable=self.max_tokens_var, 
                   width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(model_frame, text="Temperature:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.7)
        ttk.Spinbox(model_frame, from_=0.0, to=2.0, increment=0.1, 
                   textvariable=self.temperature_var, width=15).grid(row=2, column=1, 
                                                                     sticky=tk.W, padx=5, pady=5)
        
        # Base URL for custom endpoints
        ttk.Label(model_frame, text="Base URL (optional):").grid(row=3, column=0, 
                                                                  sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar()
        ttk.Entry(model_frame, textvariable=self.base_url_var, width=40).grid(row=3, column=1, 
                                                                               padx=5, pady=5)
        
        # Save button
        ttk.Button(parent, text="Save Provider Settings", 
                  command=self._save_provider_settings).pack(pady=10)
    
    def _build_ocr_tab(self, parent):
        """Build OCR configuration tab"""
        ttk.Label(parent, text="OCR Configuration", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # OCR mode selection
        mode_frame = ttk.LabelFrame(parent, text="OCR Mode", padding=10)
        mode_frame.pack(fill='x', padx=20, pady=10)
        
        self.ocr_mode_var = tk.StringVar(value="local")
        ttk.Radiobutton(mode_frame, text="Local OCR (Default - No API costs)",
                       variable=self.ocr_mode_var, value="local",
                       command=self._on_ocr_mode_changed).pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(mode_frame, text="AI OCR (Uses vision API - costs tokens)",
                       variable=self.ocr_mode_var, value="ai",
                       command=self._on_ocr_mode_changed).pack(anchor=tk.W, pady=5)
        
        # Local OCR settings
        local_frame = ttk.LabelFrame(parent, text="Local OCR Settings", padding=10)
        local_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(local_frame, text="Tesseract Path:").grid(row=0, column=0, 
                                                             sticky=tk.W, pady=5)
        self.tesseract_path_var = tk.StringVar()
        ttk.Entry(local_frame, textvariable=self.tesseract_path_var, 
                 width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(local_frame, text="Browse", 
                  command=self._browse_tesseract).grid(row=0, column=2, padx=5)
        
        ttk.Label(local_frame, text="Confidence Threshold:").grid(row=1, column=0, 
                                                                   sticky=tk.W, pady=5)
        self.confidence_var = tk.DoubleVar(value=0.6)
        ttk.Scale(local_frame, from_=0.0, to=1.0, variable=self.confidence_var, 
                 orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.conf_label = ttk.Label(local_frame, text="0.60")
        self.conf_label.grid(row=1, column=2, padx=5)
        self.confidence_var.trace('w', lambda *args: self.conf_label.config(
            text=f"{self.confidence_var.get():.2f}"))
        
        # Engine info
        info_frame = ttk.LabelFrame(parent, text="Available OCR Engines", padding=10)
        info_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.ocr_info_text = scrolledtext.ScrolledText(info_frame, height=8, 
                                                       state='disabled', bg='#f0f0f0')
        self.ocr_info_text.pack(fill='both', expand=True)
        
        ttk.Button(parent, text="Test OCR Engines", 
                  command=self._test_ocr_engines).pack(pady=10)
    
    def _build_keys_tab(self, parent):
        """Build API key management tab"""
        ttk.Label(parent, text="API Key Management", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Add/Update key
        add_frame = ttk.LabelFrame(parent, text="Add/Update API Key", padding=10)
        add_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(add_frame, text="Provider:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.key_provider_var = tk.StringVar()
        providers = ProviderFactory.get_available_providers()
        ttk.Combobox(add_frame, textvariable=self.key_provider_var, 
                    values=providers, state='readonly', width=20).grid(row=0, column=1, 
                                                                       padx=5, pady=5)
        
        ttk.Label(add_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.key_value_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.key_value_var, show="*", 
                 width=50).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(add_frame, text="Save Key", 
                  command=self._save_api_key).grid(row=2, column=1, pady=10)
        
        # Stored keys list
        list_frame = ttk.LabelFrame(parent, text="Stored API Keys", padding=10)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.keys_listbox = tk.Listbox(list_frame, height=10)
        self.keys_listbox.pack(side=tk.LEFT, fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, command=self.keys_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.keys_listbox.config(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.RIGHT, fill='y', padx=5)
        
        ttk.Button(btn_frame, text="Refresh", 
                  command=self._refresh_keys_list).pack(pady=2)
        ttk.Button(btn_frame, text="Delete Selected", 
                  command=self._delete_selected_key).pack(pady=2)
        
        self._refresh_keys_list()
    
    # Event handlers
    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="Select PDF or Images",
            filetypes=[("All supported", "*.pdf *.png *.jpg *.jpeg"),
                      ("PDF files", "*.pdf"),
                      ("Images", "*.png *.jpg *.jpeg")]
        )
        if files:
            self.input_files = [Path(f) for f in files]
            self.file_label.config(text=f"Selected: {len(self.input_files)} files")
            self._update_settings_display()
    
    def _select_vault(self):
        folder = filedialog.askdirectory(title="Select Obsidian Vault")
        if folder:
            self.vault_path = Path(folder)
            self.vault_label.config(text=f"Vault: {self.vault_path.name}")
            self._update_settings_display()
    
    def _on_provider_changed(self):
        provider = self.provider_var.get()
        default_model = ProviderFactory.get_default_model(provider)
        self.model_var.set(default_model)
        self._update_settings_display()
    
    def _on_ocr_mode_changed(self):
        mode = self.ocr_mode_var.get()
        self.current_ocr_mode = OCRMode.AI if mode == "ai" else OCRMode.LOCAL
        self._update_settings_display()
    
    def _save_provider_settings(self):
        try:
            provider = self.provider_var.get()
            if not provider:
                messagebox.showerror("Error", "Please select a provider")
                return
            
            # Update config
            self.config.config['ai_provider'] = provider
            self.config.config[f'{provider}_model'] = self.model_var.get()
            self.config.config['max_tokens'] = self.max_tokens_var.get()
            self.config.config['temperature'] = self.temperature_var.get()
            
            if self.base_url_var.get():
                self.config.config[f'{provider}_base_url'] = self.base_url_var.get()
            
            messagebox.showinfo("Success", f"Provider settings saved for {provider}")
            self._update_settings_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _browse_tesseract(self):
        filename = filedialog.askopenfilename(
            title="Select Tesseract Executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.tesseract_path_var.set(filename)
    
    def _test_ocr_engines(self):
        from ocr.local_engines import TesseractEngine, PaddleOCREngine, EasyOCREngine
        
        tesseract_path = self.tesseract_path_var.get() or None
        
        results = []
        results.append("Testing OCR Engines...\n")
        
        # Test Tesseract
        tess = TesseractEngine(tesseract_path)
        status = "✓ Available" if tess.is_available() else "✗ Not Available"
        results.append(f"Tesseract: {status}")
        
        # Test PaddleOCR
        paddle = PaddleOCREngine()
        status = "✓ Available" if paddle.is_available() else "✗ Not Available (pip install paddleocr)"
        results.append(f"PaddleOCR: {status}")
        
        # Test EasyOCR
        easy = EasyOCREngine()
        status = "✓ Available" if easy.is_available() else "✗ Not Available (pip install easyocr)"
        results.append(f"EasyOCR: {status}")
        
        # Update display
        self.ocr_info_text.config(state='normal')
        self.ocr_info_text.delete(1.0, tk.END)
        self.ocr_info_text.insert(1.0, '\n'.join(results))
        self.ocr_info_text.config(state='disabled')
    
    def _save_api_key(self):
        try:
            provider = self.key_provider_var.get()
            api_key = self.key_value_var.get()
            
            if not provider or not api_key:
                messagebox.showerror("Error", "Provider and API key required")
                return
            
            self.key_manager.save_key(provider, api_key)
            messagebox.showinfo("Success", f"API key saved for {provider}")
            
            self.key_value_var.set("")
            self._refresh_keys_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key: {e}")
    
    def _refresh_keys_list(self):
        self.keys_listbox.delete(0, tk.END)
        providers = self.key_manager.list_providers()
        for provider in providers:
            self.keys_listbox.insert(tk.END, f"{provider} - [Key Stored]")
    
    def _delete_selected_key(self):
        selection = self.keys_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No key selected")
            return
        
        provider = self.keys_listbox.get(selection[0]).split(' - ')[0]
        
        if messagebox.askyesno("Confirm", f"Delete API key for {provider}?"):
            try:
                self.key_manager.delete_key(provider)
                self._refresh_keys_list()
                messagebox.showinfo("Success", f"API key deleted for {provider}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete key: {e}")
    
    def _update_settings_display(self):
        settings = []
        settings.append(f"Provider: {self.provider_var.get() or 'Not set'}")
        settings.append(f"Model: {self.model_var.get() or 'Not set'}")
        settings.append(f"OCR Mode: {self.current_ocr_mode.value}")
        settings.append(f"Files: {len(self.input_files)} selected")
        settings.append(f"Vault: {self.vault_path.name if self.vault_path else 'Not set'}")
        
        self.settings_display.config(state='normal')
        self.settings_display.delete(1.0, tk.END)
        self.settings_display.insert(1.0, '\n'.join(settings))
        self.settings_display.config(state='disabled')
    
    def _start_processing(self):
        if not self.input_files:
            messagebox.showerror("Error", "No files selected")
            return
        if not self.vault_path:
            messagebox.showerror("Error", "No vault selected")
            return
        
        provider = self.provider_var.get()
        if not provider:
            messagebox.showerror("Error", "No LLM provider selected")
            return
        
        # Get API key
        api_key = self.key_manager.get_key(provider)
        if not api_key:
            messagebox.showerror("Error", 
                               f"No API key found for {provider}. Please add one in the API Keys tab.")
            return
        
        try:
            # Create progress window
            progress_win = ProgressWindow(self.root)
            
            # Update config with current settings
            self.config.config['ocr_strategy'] = self.current_ocr_mode.value
            self.config.config['tesseract_path'] = self.tesseract_path_var.get()
            
            # Create pipeline
            pipeline = ProcessingPipeline(
                self.config, 
                provider_name=provider,
                api_key=api_key,
                model=self.model_var.get(),
                ocr_mode=self.current_ocr_mode
            )
            
            # Process
            result = pipeline.process(self.input_files, self.vault_path, progress_win.update)
            
            progress_win.close()
            
            msg = f"Success!\n\nCreated: {result.markdown_filename}"
            if result.warnings:
                msg += f"\n\nWarnings:\n" + "\n".join(result.warnings[:5])
            messagebox.showinfo("Complete", msg)
            
        except Exception as e:
            if 'progress_win' in locals():
                progress_win.close()
            messagebox.showerror("Error", f"Processing failed: {e}")
            logger.error(f"Processing failed: {e}", exc_info=True)
    
    def _load_settings(self):
        """Load saved settings"""
        provider = self.config.get('ai_provider', 'gemini')
        self.provider_var.set(provider)
        
        model = self.config.get(f'{provider}_model', '')
        if model:
            self.model_var.set(model)
        
        tesseract_path = self.config.get('tesseract_path', '')
        if tesseract_path:
            self.tesseract_path_var.set(tesseract_path)
        
        ocr_mode = self.config.get('ocr_strategy', 'local')
        self.ocr_mode_var.set(ocr_mode)
        self.current_ocr_mode = OCRMode.AI if ocr_mode == 'ai' else OCRMode.LOCAL
        
        self._update_settings_display()
        self._test_ocr_engines()

def main():
    root = tk.Tk()
    app = EnhancedMainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
