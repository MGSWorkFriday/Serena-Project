# technique_editor.py
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import requests

SERVER_URL = "http://localhost:8000"

class TechniqueEditor(tk.Toplevel):
    def __init__(self, parent, current_name, protocol_data, on_save_callback):
        super().__init__(parent)
        self.title("Techniek Bewerken" if current_name else "Nieuwe Techniek")
        self.geometry("500x550")
        self.configure(bg='#2e2e2e')
        
        self.protocol_data = protocol_data
        self.on_save_callback = on_save_callback
        self.is_existing = bool(current_name)
        
        # UI Variabelen
        self.name_var = tk.StringVar(value=current_name)
        self.version_var = tk.StringVar(value="Default")
        self.show_in_app_var = tk.BooleanVar(value=False) # NIEUW: Default uit
        self.desc_text = None
        
        self._build_ui()
        
        # Als het bestaat, haal details op van server
        if self.is_existing:
            self._fetch_details(current_name)

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Dark.TLabel", background='#2e2e2e', foreground='white')
        style.configure("Dark.TCheckbutton", background='#2e2e2e', foreground='white')
        
        # Hoofdcontainer met padding
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- Grid Layout voor Header ---
        
        # Rij 0: Naam Label (Links) & Checkbox (Rechts)
        ttk.Label(main_frame, text="Naam Techniek (Verplicht):", style="Dark.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 2))
        
        # NIEUW: Checkbox "Tonen in App"
        cb = ttk.Checkbutton(main_frame, text="Tonen in App", variable=self.show_in_app_var, style="Dark.TCheckbutton")
        cb.grid(row=0, column=1, sticky="e", pady=(0, 2))

        # Rij 1: Naam Entry
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Rij 2: Parameter Versie
        ttk.Label(main_frame, text="Parameter Versie (uit resp_rr_param_sets):", style="Dark.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 2))
        
        ver_frame = ttk.Frame(main_frame)
        ver_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ver_entry = ttk.Entry(ver_frame, textvariable=self.version_var, width=30)
        ver_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_search = ttk.Button(ver_frame, text="...", width=4, command=self._open_version_browser)
        btn_search.pack(side=tk.LEFT, padx=(5, 0))

        # Rij 4: Beschrijving
        ttk.Label(main_frame, text="Beschrijving / Instructies:", style="Dark.TLabel").grid(row=4, column=0, sticky="w", pady=(0, 2))
        self.desc_text = tk.Text(main_frame, height=5, width=40)
        self.desc_text.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        
        # --- Knoppenbalk ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Button(btn_frame, text="Opslaan", style="Green.TButton", command=self._save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuleren", command=self.destroy).pack(side=tk.RIGHT)
        
        if self.is_existing:
            ttk.Button(btn_frame, text="Verwijderen", style="Red.TButton", command=self._delete).pack(side=tk.LEFT)

        main_frame.rowconfigure(5, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def _fetch_details(self, name):
        """Haalt de bestaande gegevens op."""
        try:
            r = requests.get(f"{SERVER_URL}/techniques", timeout=3)
            r.raise_for_status()
            data = r.json()
            if name in data:
                info = data[name]
                self.desc_text.insert("1.0", info.get("description", ""))
                self.version_var.set(info.get("param_version", "Default"))
                # NIEUW: Laad de checkbox waarde
                self.show_in_app_var.set(info.get("show_in_app", False))
        except Exception as e:
            print(f"Kon details niet laden: {e}")

    def _open_version_browser(self):
        try:
            r = requests.get(f"{SERVER_URL}/param_versions", timeout=2)
            r.raise_for_status()
            versions = r.json()
        except Exception as e:
            messagebox.showerror("Fout", f"Kon parameters niet laden: {e}", parent=self)
            return

        if not versions:
            messagebox.showinfo("Info", "Geen parameter versies gevonden.", parent=self)
            return

        top = tk.Toplevel(self)
        top.title("Kies Parameter Set")
        top.geometry("400x350")
        top.configure(bg='#2e2e2e')
        top.transient(self)
        top.grab_set()

        lbl = ttk.Label(top, text="Beschikbare Parameter Sets:", background='#2e2e2e', foreground='white')
        lbl.pack(pady=5)

        lb = tk.Listbox(top, bg='#3c3c3c', fg='white', selectbackground='#4a90e2')
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for v in versions: lb.insert(tk.END, v)

        def select():
            sel = lb.curselection()
            if sel:
                self.version_var.set(lb.get(sel[0]))
                top.destroy()

        btn_box = ttk.Frame(top)
        btn_box.pack(pady=10)
        ttk.Button(btn_box, text="Kies", command=select).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Sluiten", command=top.destroy).pack(side=tk.LEFT)

    def _save(self):
        name = self.name_var.get().strip()
        desc = self.desc_text.get("1.0", tk.END).strip()
        version = self.version_var.get().strip()
        show_app = self.show_in_app_var.get() # NIEUW: Uitlezen
        
        if not name:
            messagebox.showwarning("Let op", "Naam is verplicht!", parent=self)
            return
            
        payload = {
            "name": name,
            "description": desc,
            "param_version": version,
            "show_in_app": show_app, # NIEUW: Meesturen
            "protocol": self.protocol_data
        }
        
        try:
            r = requests.post(f"{SERVER_URL}/techniques", json=payload, timeout=3)
            if r.status_code == 200:
                self.on_save_callback(name)
                self.destroy()
            else:
                messagebox.showerror("Fout", f"Server fout: {r.text}", parent=self)
        except Exception as e:
            messagebox.showerror("Fout", f"Verbindingsfout: {e}", parent=self)

    def _delete(self):
        name = self.name_var.get().strip()
        if not messagebox.askyesno("Bevestig", f"Wil je '{name}' echt verwijderen?", parent=self):
            return
        try:
            r = requests.delete(f"{SERVER_URL}/techniques/{name}", timeout=3)
            if r.status_code == 200:
                self.on_save_callback(None)
                self.destroy()
            else:
                messagebox.showerror("Fout", f"Server fout: {r.text}", parent=self)
        except Exception as e:
            messagebox.showerror("Fout", f"Verbindingsfout: {e}", parent=self)