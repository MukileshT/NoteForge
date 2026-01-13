"""Enhanced GUI with OCR selection, Provider selection, and API Key Management"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import sys
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager
from core.enhanced_pipeline import EnhancedProcessingPipeline
from ocr.ocr_manager import OCRMode
from llm.provider_factory import ProviderFactory
from security.key_manager import KeyManager
from core.quota_manager import QuotaManager
from gui.progress_tracker import ProgressWindow
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedMainWindow:
    """Enhanced main window with all features"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Obsidian Notes Converter - Enhanced")
        self.root.geometry("800x700")
        
        self.config = ConfigManager()
        self.key_manager = KeyManager()
        self.quota_manager = QuotaManager()
        
        # State
        self.input_files = []
        self.vault_path = None
        self.selected_ocr_mode = tk.StringVar(value="local")
        self.selected_provider = tk.StringVar(value="gemini")
        self.selected_model = tk.StringVar(value="")
        self.provider_models = {}
        
        self._build_ui()
        self._load_settings()
        self._update_model_list()
    
    def _build_ui(self):
        """Build the complete UI"""
        # Title
        title_frame = tk.Frame(self.root)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="Obsidian Notes Converter", 
                font=("Arial", 18, "bold")).pack()
        tk.Label(title_frame, text="Enhanced Edition", 
                font=("Arial", 10)).pack()
        
        # File selection
        file_frame = tk.LabelFrame(self.root, text="Input Files", padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Button(file_frame, text="Select PDF/Images", 
                 command=self._select_files, width=25).pack(side=tk.LEFT, padx=5)
        self.file_label = tk.Label(file_frame, text="No files selected", anchor="w")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Vault selection
        vault_frame = tk.LabelFrame(self.root, text="Obsidian Vault", padx=10, pady=10)
        vault_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Button(vault_frame, text="Select Vault", 
                 command=self._select_vault, width=25).pack(side=tk.LEFT, padx=5)
        self.vault_label = tk.Label(vault_frame, text="No vault selected", anchor="w")
        self.vault_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # OCR Mode Selection
        ocr_frame = tk.LabelFrame(self.root, text="OCR Mode", padx=10, pady=10)
        ocr_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Radiobutton(ocr_frame, text="Local OCR (Default)", 
                      variable=self.selected_ocr_mode, value="local",
                      command=self._on_ocr_mode_changed).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(ocr_frame, text="AI OCR (Optional)", 
                      variable=self.selected_ocr_mode, value="ai",
                      command=self._on_ocr_mode_changed).pack(side=tk.LEFT, padx=10)
        self.ocr_info_label = tk.Label(ocr_frame, text="Local OCR uses Tesseract/PaddleOCR/EasyOCR", 
                                       fg="gray", font=("Arial", 8))
        self.ocr_info_label.pack(side=tk.LEFT, padx=10)
        
        # Provider Selection
        provider_frame = tk.LabelFrame(self.root, text="LLM Provider", padx=10, pady=10)
        provider_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(provider_frame, text="Provider:").grid(row=0, column=0, padx=5, sticky="w")
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.selected_provider,
                                     values=ProviderFactory.get_available_providers(),
                                     state="readonly", width=20)
        provider_combo.grid(row=0, column=1, padx=5)
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)
        
        tk.Label(provider_frame, text="Model:").grid(row=0, column=2, padx=5, sticky="w")
        # Allow typing model names directly
        self.model_combo = ttk.Combobox(provider_frame, textvariable=self.selected_model,
                        state="normal", width=25)
        self.model_combo.grid(row=0, column=3, padx=5)
        
        # Inline custom model fields (hidden by default)
        self.custom_model_frame = tk.Frame(provider_frame)
        tk.Label(self.custom_model_frame, text="Custom model name:").grid(row=0, column=0, padx=5, sticky="w")
        self.custom_model_entry = tk.Entry(self.custom_model_frame, width=30)
        self.custom_model_entry.grid(row=0, column=1, padx=5)
        tk.Label(self.custom_model_frame, text="Type:").grid(row=0, column=2, padx=5, sticky="w")
        self.custom_model_type = ttk.Combobox(self.custom_model_frame, values=['api', 'local'], width=8, state='readonly')
        self.custom_model_type.grid(row=0, column=3, padx=5)
        self.custom_model_type.set('api')
        # Save/Cancel buttons
        self._save_custom_btn = tk.Button(self.custom_model_frame, text="Save Custom", command=self._save_custom_model, bg="green", fg="white")
        self._save_custom_btn.grid(row=1, column=1, pady=5, sticky="w")
        self._cancel_custom_btn = tk.Button(self.custom_model_frame, text="Cancel", command=self._hide_custom_model_fields)
        self._cancel_custom_btn.grid(row=1, column=2, pady=5, sticky="w")
        self.custom_model_frame.grid(row=1, column=0, columnspan=4, pady=5, sticky="w")
        self.custom_model_frame.grid_remove()
        
        # API Key Management
        key_frame = tk.LabelFrame(self.root, text="API Key Management", padx=10, pady=10)
        key_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Button(key_frame, text="Manage API Keys", 
                 command=self._open_key_manager, width=25).pack(side=tk.LEFT, padx=5)
        self.key_status_label = tk.Label(key_frame, text="", anchor="w")
        self.key_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self._update_key_status()
        
        # Quota Status
        quota_frame = tk.LabelFrame(self.root, text="API Usage", padx=10, pady=10)
        quota_frame.pack(fill=tk.X, padx=20, pady=5)
        self.quota_label = tk.Label(quota_frame, text="", anchor="w", justify=tk.LEFT)
        self.quota_label.pack(fill=tk.X, padx=5)
        self._update_quota_status()
        
        # Process Button
        process_frame = tk.Frame(self.root)
        process_frame.pack(pady=20)
        self.process_button = tk.Button(process_frame, text="Start Processing", 
                                        command=self._start_processing,
                                        bg="green", fg="white", width=30, height=2,
                                        font=("Arial", 12, "bold"))
        self.process_button.pack()
    
    def _load_settings(self):
        """Load saved settings"""
        # Load OCR mode
        ocr_strategy = self.config.get('ocr.mode', 'local')
        self.selected_ocr_mode.set(ocr_strategy)

        # Load provider from config if present
        selected_model = self.config.get('models.selected', '')
        if selected_model:
            # Find provider for selected model
            for m in self.config.list_models():
                if m.get('name') == selected_model:
                    self.selected_provider.set(m.get('provider', self.selected_provider.get()))
                    self.selected_model.set(selected_model)
                    break
    
    def _on_ocr_mode_changed(self):
        """Handle OCR mode change"""
        mode = self.selected_ocr_mode.get()
        if mode == "local":
            self.ocr_info_label.config(text="Local OCR uses Tesseract/PaddleOCR/EasyOCR", fg="gray")
        else:
            self.ocr_info_label.config(text="AI OCR uses vision models (requires API key)", fg="orange")
    
    def _on_provider_changed(self, event=None):
        """Handle provider change"""
        self._update_model_list()
        self._update_key_status()
        self._update_quota_status()
    
    def _update_model_list(self):
        """Update model list for selected provider"""
        provider = self.selected_provider.get()

        # Build list from central config.models.available
        available = [m for m in self.config.list_models() if m.get('provider') == provider]
        names = [m.get('name') for m in available]

        # Add 'Other / Custom' option
        names.append('Other / Custom')

        self.provider_models[provider] = names
        self.model_combo['values'] = self.provider_models[provider]

        # If selected_model exists and matches provider, keep it
        cur_sel = self.selected_model.get()
        if cur_sel and cur_sel in names:
            return

        # Otherwise choose selected model from config if matches, else first available
        cfg_selected = self.config.get('models.selected', '')
        if cfg_selected and cfg_selected in names:
            self.selected_model.set(cfg_selected)
        elif names and names[0] != 'Other / Custom':
            self.selected_model.set(names[0])
        else:
            self.selected_model.set('')

        # Bind selection event for custom option
        def on_model_changed(event=None):
            val = self.selected_model.get()
            if val == 'Other / Custom':
                # Show inline fields instead of separate dialogs
                self._show_custom_model_fields()

        self.model_combo.bind('<<ComboboxSelected>>', on_model_changed)
        # Handle typed model names (Enter or focus out)
        self.model_combo.bind('<Return>', self._on_model_typed)
        self.model_combo.bind('<FocusOut>', self._on_model_focus_out)


    def _prompt_add_custom_model(self):
        # Kept for backward compatibility but no longer used.
        return

    def _show_custom_model_fields(self):
        # Show inline fields and focus entry
        self.custom_model_entry.delete(0, tk.END)
        self.custom_model_frame.grid()
        self.custom_model_entry.focus_set()

    def _hide_custom_model_fields(self):
        self.custom_model_frame.grid_remove()

    def _save_custom_model(self):
        name = self.custom_model_entry.get().strip()
        if not name:
            messagebox.showerror('Error', 'Custom model name cannot be empty')
            return
        provider = self.selected_provider.get() or 'custom'
        mtype = self.custom_model_type.get() or 'api'
        try:
            self.config.add_model(name=name, provider=provider, mtype=mtype)
            self.selected_model.set(name)
            self._hide_custom_model_fields()
            self._update_model_list()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to add model: {e}')

    def _on_model_typed(self, event=None):
        # Handle when user types a model name and presses Enter
        val = self.selected_model.get().strip()
        if not val:
            return
        provider = self.selected_provider.get()
        names = self.provider_models.get(provider, [])
        if val in names:
            # existing model, nothing to do
            return
        if val == 'Other / Custom':
            self._show_custom_model_fields()
            return
        # Treat typed model as custom: add and select
        try:
            self.config.add_model(name=val, provider=provider, mtype='api')
            self.selected_model.set(val)
            self._update_model_list()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to add typed model: {e}')

    def _on_model_focus_out(self, event=None):
        # Same behavior as pressing Enter
        try:
            self._on_model_typed()
        except Exception:
            pass
    
    def _update_key_status(self):
        """Update API key status display"""
        provider = self.selected_provider.get()
        key = self.key_manager.get_key(provider)
        
        if key:
            self.key_status_label.config(text=f"✓ API key configured for {provider}", fg="green")
        else:
            self.key_status_label.config(text=f"⚠ No API key for {provider}. Click 'Manage API Keys' to add.", fg="red")
    
    def _update_quota_status(self):
        """Update quota usage display"""
        provider = self.selected_provider.get()
        usage = self.quota_manager.get_usage(provider)
        
        if usage:
            tokens_hour = usage.get('tokens_hour', 0)
            tokens_day = usage.get('tokens_day', 0)
            max_hour = usage.get('limits', {}).get('max_tokens_hour', 0)
            max_day = usage.get('limits', {}).get('max_tokens_day', 0)
            
            status = f"Hour: {tokens_hour:,}/{max_hour:,} tokens | Day: {tokens_day:,}/{max_day:,} tokens"
            self.quota_label.config(text=status)
        else:
            self.quota_label.config(text="No usage data")
    
    def _select_files(self):
        """Select input files"""
        files = filedialog.askopenfilenames(
            title="Select PDF or Images",
            filetypes=[("PDF files", "*.pdf"), ("Images", "*.png *.jpg *.jpeg")]
        )
        if files:
            self.input_files = [Path(f) for f in files]
            self.file_label.config(text=f"Selected: {len(self.input_files)} files")
    
    def _select_vault(self):
        """Select Obsidian vault"""
        folder = filedialog.askdirectory(title="Select Obsidian Vault")
        if folder:
            self.vault_path = Path(folder)
            self.vault_label.config(text=f"Vault: {self.vault_path.name}")
    
    def _open_key_manager(self):
        """Open API key management window"""
        key_window = tk.Toplevel(self.root)
        key_window.title("API Key Management")
        key_window.geometry("600x500")
        
        # Provider selection
        tk.Label(key_window, text="Provider:", font=("Arial", 10, "bold")).pack(pady=5)
        provider_var = tk.StringVar(value=self.selected_provider.get())
        provider_combo = ttk.Combobox(key_window, textvariable=provider_var,
                                     values=ProviderFactory.get_available_providers(),
                                     state="readonly", width=30)
        provider_combo.pack(pady=5)
        
        # Key input
        tk.Label(key_window, text="API Key:").pack(pady=5)
        key_entry = tk.Entry(key_window, width=50, show="*")
        key_entry.pack(pady=5)
        
        # Load existing key if available
        current_provider = provider_var.get()
        existing_key = self.key_manager.get_key(current_provider)
        if existing_key:
            key_entry.insert(0, existing_key)
        
        def save_key():
            provider = provider_var.get()
            key = key_entry.get().strip()
            if not key:
                messagebox.showerror("Error", "API key cannot be empty")
                return
            try:
                self.key_manager.save_key(provider, key)
                messagebox.showinfo("Success", f"API key saved for {provider}")
                self._update_key_status()
                key_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save key: {e}")
        
        def delete_key():
            provider = provider_var.get()
            if messagebox.askyesno("Confirm", f"Delete API key for {provider}?"):
                try:
                    self.key_manager.delete_key(provider)
                    key_entry.delete(0, tk.END)
                    messagebox.showinfo("Success", f"API key deleted for {provider}")
                    self._update_key_status()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete key: {e}")
        
        def on_provider_change(event=None):
            provider = provider_var.get()
            existing_key = self.key_manager.get_key(provider)
            key_entry.delete(0, tk.END)
            if existing_key:
                key_entry.insert(0, existing_key)
        
        provider_combo.bind("<<ComboboxSelected>>", on_provider_change)
        
        # Buttons
        button_frame = tk.Frame(key_window)
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="Save Key", command=save_key, 
                 bg="green", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Key", command=delete_key, 
                 bg="red", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=key_window.destroy, 
                 width=15).pack(side=tk.LEFT, padx=5)
        
        # List all providers
        tk.Label(key_window, text="\nConfigured Providers:", font=("Arial", 10, "bold")).pack(pady=10)
        list_frame = tk.Frame(key_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        configured = self.key_manager.list_providers()
        if configured:
            for provider in configured:
                tk.Label(list_frame, text=f"✓ {provider}", fg="green", anchor="w").pack(fill=tk.X)
        else:
            tk.Label(list_frame, text="No providers configured", fg="gray").pack()
    
    def _start_processing(self):
        """Start processing"""
        if not self.input_files:
            messagebox.showerror("Error", "No files selected")
            return
        if not self.vault_path:
            messagebox.showerror("Error", "No vault selected")
            return
        
        # Get provider and API key
        provider = self.selected_provider.get()
        api_key = self.key_manager.get_key(provider)
        
        if not api_key:
            messagebox.showerror("Error", 
                               f"No API key configured for {provider}.\n"
                               "Please configure an API key in 'Manage API Keys'.")
            return
        
        # Get OCR mode
        ocr_mode_str = self.selected_ocr_mode.get()
        ocr_mode = OCRMode.LOCAL if ocr_mode_str == "local" else OCRMode.AI
        
        # Get model
        model = self.selected_model.get()
        if not model:
            model = ProviderFactory.get_default_model(provider)
        
        # Check quota
        estimated_tokens = 2000  # Rough estimate
        if not self.quota_manager.check_quota(provider, estimated_tokens):
            if not messagebox.askyesno("Quota Warning", 
                                     "Quota limit may be exceeded. Continue anyway?"):
                return
        
        # Create progress window
        progress_win = ProgressWindow(self.root)
        
        try:
            # Create pipeline
            pipeline = EnhancedProcessingPipeline(
                config=self.config,
                provider_name=provider,
                api_key=api_key,
                model=model,
                ocr_mode=ocr_mode
            )
            
            # Process
            result = pipeline.process(self.input_files, self.vault_path, 
                                     progress_win.update)
            
            progress_win.close()
            
            # Show success
            msg = f"Success!\n\nCreated: {result.markdown_filename}"
            if result.warnings:
                msg += f"\n\nWarnings ({len(result.warnings)}):\n"
                msg += "\n".join(result.warnings[:5])
                if len(result.warnings) > 5:
                    msg += f"\n... and {len(result.warnings) - 5} more"
            
            messagebox.showinfo("Complete", msg)
            
            # Update quota status
            self._update_quota_status()
            
        except Exception as e:
            progress_win.close()
            logger.error(f"Processing failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")

def main():
    root = tk.Tk()
    app = EnhancedMainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
