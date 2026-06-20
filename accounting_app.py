import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime, timedelta
import os
import platform
import subprocess
import shutil

DB_NAME = "accounting.db"
ADMIN_PASSWORD = "admin"

# -------------------- Theme Definitions --------------------
THEMES = {
    "Light": {
        "BG_MAIN": "#F0F0F0",
        "BG_TAB": "#FFFFFF",
        "HEADER_BG": "#2C3E50",
        "HEADER_FG": "#FFFFFF",
        "BUTTON_PRIMARY": "#3498DB",
        "BUTTON_DANGER": "#E74C3C",
        "BUTTON_SUCCESS": "#2ECC71",
        "BUTTON_WARN": "#F39C12",
        "TEXT_DARK": "#2C3E50",
        "TEXT_LIGHT": "#FFFFFF",
        "ACCENT": "#1ABC9C",
        "TREE_BG": "#FFFFFF",
        "TREE_FIELD": "#FFFFFF",
        "TREE_SELECTED": "#1ABC9C",
        "TREE_SELECTED_FG": "#FFFFFF",
        "FRAME_BG": "#F0F0F0",
        "LABEL_BG": "#F0F0F0",
        "STATUS_BG": "#2C3E50",
        "STATUS_FG": "#FFFFFF",
        "TAB_BG": "#FFFFFF",
        "TAB_ACTIVE_BG": "#1ABC9C",
        "TAB_ACTIVE_FG": "#FFFFFF",
        "TAB_HOVER_BG": "#E0F2F1",   # new
        "TAB_HOVER_FG": "#2C3E50",   # new
        "POPUP_BG": "#F0F0F0"
    },
    "Dark": {
        "BG_MAIN": "#1E1E1E",
        "BG_TAB": "#2D2D2D",
        "HEADER_BG": "#3C3C3C",
        "HEADER_FG": "#E0E0E0",
        "BUTTON_PRIMARY": "#007ACC",
        "BUTTON_DANGER": "#D32F2F",
        "BUTTON_SUCCESS": "#388E3C",
        "BUTTON_WARN": "#F57C00",
        "TEXT_DARK": "#E0E0E0",
        "TEXT_LIGHT": "#E0E0E0",
        "ACCENT": "#007ACC",
        "TREE_BG": "#2D2D2D",
        "TREE_FIELD": "#2D2D2D",
        "TREE_SELECTED": "#007ACC",
        "TREE_SELECTED_FG": "#FFFFFF",
        "FRAME_BG": "#1E1E1E",
        "LABEL_BG": "#1E1E1E",
        "STATUS_BG": "#007ACC",
        "STATUS_FG": "#FFFFFF",
        "TAB_BG": "#2D2D2D",
        "TAB_ACTIVE_BG": "#007ACC",
        "TAB_ACTIVE_FG": "#FFFFFF",
        "TAB_HOVER_BG": "#3A3A3A",   # new
        "TAB_HOVER_FG": "#FFFFFF",   # new
        "POPUP_BG": "#1E1E1E"
    },
    "Blue": {
        "BG_MAIN": "#F0F4F8",
        "BG_TAB": "#FFFFFF",
        "HEADER_BG": "#2C3E50",
        "HEADER_FG": "#FFFFFF",
        "BUTTON_PRIMARY": "#3498DB",
        "BUTTON_DANGER": "#E74C3C",
        "BUTTON_SUCCESS": "#2ECC71",
        "BUTTON_WARN": "#F39C12",
        "TEXT_DARK": "#2C3E50",
        "TEXT_LIGHT": "#FFFFFF",
        "ACCENT": "#1ABC9C",
        "TREE_BG": "#FFFFFF",
        "TREE_FIELD": "#FFFFFF",
        "TREE_SELECTED": "#1ABC9C",
        "TREE_SELECTED_FG": "#FFFFFF",
        "FRAME_BG": "#F0F4F8",
        "LABEL_BG": "#F0F4F8",
        "STATUS_BG": "#2C3E50",
        "STATUS_FG": "#FFFFFF",
        "TAB_BG": "#FFFFFF",
        "TAB_ACTIVE_BG": "#1ABC9C",
        "TAB_ACTIVE_FG": "#FFFFFF",
        "TAB_HOVER_BG": "#D6EAF8",   # new
        "TAB_HOVER_FG": "#2C3E50",   # new
        "POPUP_BG": "#F0F4F8"
    }
}

class AccountingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi‑Account Credit/Debit Manager")
        self.root.geometry("1050x750")

        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()
        self.migrate_tables()

        self.current_theme = tk.StringVar(value="Blue")
        try:
            self.apply_theme()
        except Exception:
            self.theme = THEMES["Blue"]
            self.root.configure(bg=self.theme["BG_MAIN"])
            self.style = ttk.Style()
            self.style.theme_use('clam')

        self.build_ui()

    def apply_theme(self):
        theme_name = self.current_theme.get()
        t = THEMES[theme_name]
        self.theme = t
        self.root.configure(bg=t["BG_MAIN"])

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=t["FRAME_BG"])
        style.configure('TLabel', background=t["LABEL_BG"], foreground=t["TEXT_DARK"], font=('Segoe UI', 10))
        style.configure('TNotebook', background=t["BG_MAIN"], borderwidth=0)
        style.configure('TNotebook.Tab', background=t["TAB_BG"], foreground=t["TEXT_DARK"], padding=[15, 5],
                        font=('Segoe UI', 10, 'bold'))
        # FIXED: use the new TAB_HOVER_BG / TAB_HOVER_FG for the hover state
        style.map('TNotebook.Tab',
                  background=[('selected', t["TAB_ACTIVE_BG"]),
                              ('active', t["TAB_HOVER_BG"])],
                  foreground=[('selected', t["TAB_ACTIVE_FG"]),
                              ('active', t["TAB_HOVER_FG"])])

        style.configure('Primary.TButton', background=t["BUTTON_PRIMARY"], foreground=t["TEXT_LIGHT"],
                        borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Primary.TButton',
                  background=[('active', self._darken_color(t["BUTTON_PRIMARY"], 0.1)),
                              ('pressed', self._darken_color(t["BUTTON_PRIMARY"], 0.2))])
        style.configure('Danger.TButton', background=t["BUTTON_DANGER"], foreground=t["TEXT_LIGHT"],
                        borderwidth=0, font=('Segoe UI', 10, 'bold'))
        style.map('Danger.TButton',
                  background=[('active', self._darken_color(t["BUTTON_DANGER"], 0.1)),
                              ('pressed', self._darken_color(t["BUTTON_DANGER"], 0.2))])
        style.configure('Success.TButton', background=t["BUTTON_SUCCESS"], foreground=t["TEXT_LIGHT"],
                        borderwidth=0, font=('Segoe UI', 10, 'bold'))
        style.map('Success.TButton',
                  background=[('active', self._darken_color(t["BUTTON_SUCCESS"], 0.1)),
                              ('pressed', self._darken_color(t["BUTTON_SUCCESS"], 0.2))])
        style.configure('Warn.TButton', background=t["BUTTON_WARN"], foreground=t["TEXT_LIGHT"],
                        borderwidth=0, font=('Segoe UI', 10, 'bold'))
        style.map('Warn.TButton',
                  background=[('active', self._darken_color(t["BUTTON_WARN"], 0.1)),
                              ('pressed', self._darken_color(t["BUTTON_WARN"], 0.2))])

        style.configure('Treeview', background=t["TREE_BG"], foreground=t["TEXT_DARK"],
                        rowheight=25, fieldbackground=t["TREE_FIELD"], font=('Segoe UI', 9))
        style.configure('Treeview.Heading', background=t["HEADER_BG"], foreground=t["HEADER_FG"],
                        font=('Segoe UI', 9, 'bold'))
        style.map('Treeview',
                  background=[('selected', t["TREE_SELECTED"])],
                  foreground=[('selected', t["TREE_SELECTED_FG"])])

        style.configure('Status.TLabel', background=t["STATUS_BG"], foreground=t["STATUS_FG"],
                        font=('Segoe UI', 9), padding=5)
        self.style = style

    def _darken_color(self, hex_color, factor=0.2):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f'#{r:02x}{g:02x}{b:02x}'

    # --- rest of the class is unchanged from the previous working version ---
    # (build_ui, backup/restore, accounts, transactions, overview, reports, etc.)
    # I'll include the full class below for completeness.

    def build_ui(self):
        theme_frame = ttk.Frame(self.root)
        theme_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(theme_frame, text="Theme:").pack(side='left', padx=(0,5))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.current_theme,
                                   values=list(THEMES.keys()), state='readonly', width=10)
        theme_combo.pack(side='left')
        theme_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_theme())

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=(5,0))

        self.build_accounts_tab()
        self.build_transactions_tab()
        self.build_overview_tab()
        self.build_report_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, style='Status.TLabel', anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")

    def set_status(self, msg, is_error=False, duration=3000):
        self.status_var.set(msg)
        if is_error:
            self.style.configure('Status.TLabel', background=self.theme["BUTTON_DANGER"])
        else:
            self.style.configure('Status.TLabel', background=self.theme["BUTTON_SUCCESS"])
        self.root.after(duration, lambda: self.status_var.set("Ready"))

    def check_admin(self):
        pwd = simpledialog.askstring("Admin Password", "Enter admin password:", show="*")
        if pwd is None:
            return False
        if pwd != ADMIN_PASSWORD:
            messagebox.showerror("Access Denied", "Incorrect password.")
            return False
        return True

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT DEFAULT 'Bank',
                        bank_name TEXT,
                        account_name TEXT,
                        account_number TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER NOT NULL,
                        type TEXT CHECK(type IN ('credit','debit')) NOT NULL,
                        amount REAL NOT NULL,
                        description TEXT,
                        date TEXT NOT NULL,
                        FOREIGN KEY (account_id) REFERENCES accounts(id))''')
        self.conn.commit()

    def migrate_tables(self):
        try:
            cur = self.conn.cursor()
            cur.execute("PRAGMA table_info(accounts)")
            existing_cols = [col[1] for col in cur.fetchall()]
            if 'type' not in existing_cols:
                cur.execute("ALTER TABLE accounts ADD COLUMN type TEXT DEFAULT 'Bank'")
                self.conn.commit()
        except Exception:
            pass

    def on_tab_changed(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "Overview":
            self.refresh_overview()
        elif selected_tab == "Transactions":
            self.refresh_transaction_list()

    # ---------------- Backup & Restore ----------------
    def backup_database(self):
        if not self.check_admin():
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            initialfile=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            title="Save Backup As"
        )
        if not file_path:
            return
        try:
            self.conn.close()
            shutil.copy2(DB_NAME, file_path)
            self.conn = sqlite3.connect(DB_NAME)
            self.set_status(f"Backup saved to {file_path}")
        except Exception as e:
            self.conn = sqlite3.connect(DB_NAME)
            messagebox.showerror("Backup Error", str(e))

    def restore_database(self):
        if not self.check_admin():
            return
        if not messagebox.askyesno("Confirm Restore",
                                   "This will replace ALL current data with the backup.\nAre you sure?"):
            return
        file_path = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            title="Select Backup File"
        )
        if not file_path:
            return
        try:
            self.conn.close()
            shutil.copy2(file_path, DB_NAME)
            self.conn = sqlite3.connect(DB_NAME)
            self.refresh_account_list()
            self.populate_account_combo()
            self.populate_report_combo()
            self.refresh_transaction_list()
            self.refresh_overview()
            self.set_status("Database restored successfully.")
        except Exception as e:
            self.conn = sqlite3.connect(DB_NAME)
            messagebox.showerror("Restore Error", str(e))

    # ---------------- Accounts Tab ----------------
    def build_accounts_tab(self):
        self.acc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.acc_frame, text="Accounts")

        cols = ('ID', 'Name', 'Type', 'Bank Name', 'Account Name', 'Account No')
        self.acc_tree = ttk.Treeview(self.acc_frame, columns=cols, show='headings', height=12)
        widths = {'ID':40, 'Name':120, 'Type':80, 'Bank Name':130, 'Account Name':150, 'Account No':120}
        for col in cols:
            self.acc_tree.heading(col, text=col)
            self.acc_tree.column(col, width=widths.get(col, 100), anchor='center')
        self.acc_tree.pack(fill='both', expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(self.acc_frame)
        btn_frame.pack(pady=(0,10))
        ttk.Button(btn_frame, text="➕ Add Account", style='Primary.TButton', command=self.add_account).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Account", style='Warn.TButton', command=self.edit_account).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Account", style='Danger.TButton', command=self.delete_account).pack(side='left', padx=5)

        bk_frame = ttk.Frame(self.acc_frame)
        bk_frame.pack(pady=(5,10))
        ttk.Button(bk_frame, text="💾 Backup Database", style='Success.TButton', command=self.backup_database).pack(side='left', padx=5)
        ttk.Button(bk_frame, text="📥 Restore Database", style='Primary.TButton', command=self.restore_database).pack(side='left', padx=5)

        self.refresh_account_list()

    def refresh_account_list(self):
        for row in self.acc_tree.get_children():
            self.acc_tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, type, bank_name, account_name, account_number FROM accounts ORDER BY name")
        for row in cur.fetchall():
            self.acc_tree.insert('', 'end', values=(
                row[0], row[1], row[2] or '', row[3] or '', row[4] or '', row[5] or ''
            ))

    def get_bank_list(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT bank_name FROM accounts WHERE type='Bank' AND bank_name IS NOT NULL AND bank_name != '' ORDER BY bank_name")
        return [row[0] for row in cur.fetchall()]

    def add_account(self):
        if not self.check_admin():
            return
        self._account_dialog("Add Account")

    def edit_account(self):
        if not self.check_admin():
            return
        selected = self.acc_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an account to edit.")
            return
        aid = self.acc_tree.item(selected[0])['values'][0]
        cur = self.conn.cursor()
        cur.execute("SELECT name, type, bank_name, account_name, account_number FROM accounts WHERE id=?", (aid,))
        row = cur.fetchone()
        self._account_dialog("Edit Account", aid, row[0], row[1], row[2], row[3], row[4])

    def delete_account(self):
        if not self.check_admin():
            return
        selected = self.acc_tree.selection()
        if not selected:
            return
        if messagebox.askyesno("Confirm", "Delete selected account and all its transactions?"):
            aid = self.acc_tree.item(selected[0])['values'][0]
            self.conn.execute("DELETE FROM transactions WHERE account_id=?", (aid,))
            self.conn.execute("DELETE FROM accounts WHERE id=?", (aid,))
            self.conn.commit()
            self.refresh_account_list()
            self.refresh_transaction_list()
            self.populate_account_combo()
            self.populate_report_combo()
            self.refresh_overview()
            self.set_status("Account deleted.")

    def _account_dialog(self, title, aid=None, name='', atype='Bank',
                        bank_name='', account_name='', account_number=''):
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.geometry("400x400")
        dlg.resizable(False, False)
        dlg.configure(bg=self.theme["POPUP_BG"])

        dlg.update_idletasks()
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        popup_w = 400
        popup_h = 400
        x = main_x + (main_w // 2) - (popup_w // 2)
        y = main_y + (main_h // 2) - (popup_h // 2)
        dlg.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

        dlg.grab_set()
        dlg.lift()
        dlg.attributes('-topmost', True)

        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Account Name:").grid(row=0, column=0, sticky='w', pady=5)
        name_var = tk.StringVar(value=name)
        ttk.Entry(frame, textvariable=name_var, width=30, font=('Segoe UI', 10)).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Type:").grid(row=1, column=0, sticky='w', pady=5)
        type_var = tk.StringVar(value=atype)
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=['Bank', 'Cash', 'Other'], state='readonly', width=27, font=('Segoe UI', 10))
        type_combo.grid(row=1, column=1, padx=5, pady=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.toggle_bank_fields(bank_frame, type_var.get()))

        bank_frame = ttk.Frame(frame)
        bank_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')
        ttk.Label(bank_frame, text="Bank Name:").grid(row=0, column=0, sticky='w', pady=5)
        bank_var = tk.StringVar(value=bank_name)
        bank_combo = ttk.Combobox(bank_frame, textvariable=bank_var, width=27, font=('Segoe UI', 10))
        bank_combo['values'] = self.get_bank_list()
        bank_combo.grid(row=0, column=1, padx=5, pady=5)
        bank_combo.configure(state='normal')

        ttk.Label(bank_frame, text="Account Name:").grid(row=1, column=0, sticky='w', pady=5)
        acct_name_var = tk.StringVar(value=account_name)
        ttk.Entry(bank_frame, textvariable=acct_name_var, width=30, font=('Segoe UI', 10)).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(bank_frame, text="Account Number:").grid(row=2, column=0, sticky='w', pady=5)
        acct_num_var = tk.StringVar(value=account_number)
        ttk.Entry(bank_frame, textvariable=acct_num_var, width=30, font=('Segoe UI', 10)).grid(row=2, column=1, padx=5, pady=5)

        self.toggle_bank_fields(bank_frame, atype)

        def save():
            n = name_var.get().strip()
            if not n:
                messagebox.showerror("Error", "Account Name is required.", parent=dlg)
                return
            t = type_var.get()
            b_name = bank_var.get().strip() if t == 'Bank' else ''
            a_name = acct_name_var.get().strip() if t == 'Bank' else ''
            a_num = acct_num_var.get().strip() if t == 'Bank' else ''

            if aid:
                self.conn.execute("UPDATE accounts SET name=?, type=?, bank_name=?, account_name=?, account_number=? WHERE id=?",
                                  (n, t, b_name, a_name, a_num, aid))
            else:
                self.conn.execute("INSERT INTO accounts (name, type, bank_name, account_name, account_number) VALUES (?,?,?,?,?)",
                                  (n, t, b_name, a_name, a_num))
            self.conn.commit()
            dlg.destroy()
            self.refresh_account_list()
            self.populate_account_combo()
            self.populate_report_combo()
            self.refresh_transaction_list()
            self.refresh_overview()
            self.set_status("Account saved.")

        save_btn = ttk.Button(frame, text="💾 SAVE ACCOUNT", style='Success.TButton', command=save)
        save_btn.grid(row=3, column=0, columnspan=2, pady=20)
        self.style.configure('Success.TButton', font=('Segoe UI', 12, 'bold'))
        save_btn.configure(style='Success.TButton')

    def toggle_bank_fields(self, bank_frame, atype):
        for widget in bank_frame.winfo_children():
            widget.configure(state='normal' if atype == 'Bank' else 'disabled')

    # ---------------- Transactions Tab ----------------
    def build_transactions_tab(self):
        self.trans_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trans_frame, text="Transactions")

        top = ttk.Frame(self.trans_frame)
        top.pack(fill='x', padx=10, pady=10)
        ttk.Label(top, text="Account:").pack(side='left')
        self.acc_combo = ttk.Combobox(top, state='readonly', font=('Segoe UI', 10))
        self.acc_combo.pack(side='left', padx=5)
        self.acc_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_transaction_list())

        ttk.Label(top, text="Period:").pack(side='left', padx=(20,5))
        self.period_var = tk.StringVar(value='All')
        period_combo = ttk.Combobox(top, textvariable=self.period_var, state='readonly',
                                    values=['All', 'Today', 'This Week', 'This Month', 'This Year', 'Custom'],
                                    width=12, font=('Segoe UI', 10))
        period_combo.pack(side='left', padx=5)
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.on_period_change())

        ttk.Label(top, text="From:").pack(side='left', padx=(20,2))
        self.from_var = tk.StringVar()
        self.from_entry = tk.Entry(top, textvariable=self.from_var, width=10, font=('Segoe UI', 10), state='disabled')
        self.from_entry.pack(side='left')
        self.bind_date_picker(self.from_entry, self.from_var)

        ttk.Label(top, text="To:").pack(side='left', padx=2)
        self.to_var = tk.StringVar()
        self.to_entry = tk.Entry(top, textvariable=self.to_var, width=10, font=('Segoe UI', 10), state='disabled')
        self.to_entry.pack(side='left')
        self.bind_date_picker(self.to_entry, self.to_var)

        ttk.Button(top, text="Apply", command=self.refresh_transaction_list).pack(side='left', padx=5)

        entry_frame = ttk.Frame(self.trans_frame)
        entry_frame.pack(fill='x', padx=10, pady=5)
        self.entry_frame = entry_frame

        ttk.Label(entry_frame, text="Date:").grid(row=0, column=0, sticky='w')
        self.date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        self.date_entry = tk.Entry(entry_frame, textvariable=self.date_var, width=12, font=('Segoe UI', 10))
        self.date_entry.grid(row=0, column=1, padx=5)
        self.bind_date_picker(self.date_entry, self.date_var)

        ttk.Label(entry_frame, text="Type:").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.type_var = tk.StringVar(value='credit')
        ttk.Radiobutton(entry_frame, text='Credit', variable=self.type_var, value='credit').grid(row=0, column=3)
        ttk.Radiobutton(entry_frame, text='Debit', variable=self.type_var, value='debit').grid(row=0, column=4)

        ttk.Label(entry_frame, text="Amount:").grid(row=1, column=0, sticky='w', pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.amount_var, width=12, font=('Segoe UI', 10)).grid(row=1, column=1, pady=5)

        ttk.Label(entry_frame, text="Description:").grid(row=1, column=2, sticky='w', padx=(20,0), pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.desc_var, width=30, font=('Segoe UI', 10)).grid(row=1, column=3, columnspan=2, padx=5, pady=5)

        self.record_btn = ttk.Button(entry_frame, text="📝 Record Transaction", style='Primary.TButton', command=self.record_transaction)
        self.record_btn.grid(row=2, column=0, columnspan=5, pady=10)

        cols = ('ID', 'Date', 'Description', 'Credit', 'Debit', 'Balance')
        self.ledger_tree = ttk.Treeview(self.trans_frame, columns=cols, show='headings', height=12)
        self.ledger_tree.heading('ID', text='ID')
        self.ledger_tree.heading('Date', text='Date')
        self.ledger_tree.heading('Description', text='Description')
        self.ledger_tree.heading('Credit', text='Credit')
        self.ledger_tree.heading('Debit', text='Debit')
        self.ledger_tree.heading('Balance', text='Balance')
        self.ledger_tree.column('ID', width=0, stretch=False)
        self.ledger_tree.column('Date', width=100, anchor='center')
        self.ledger_tree.column('Description', width=200)
        self.ledger_tree.column('Credit', width=100, anchor='center')
        self.ledger_tree.column('Debit', width=100, anchor='center')
        self.ledger_tree.column('Balance', width=100, anchor='center')
        self.ledger_tree.pack(fill='both', expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self.trans_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="✏️ Edit Selected Transaction", style='Warn.TButton', command=self.edit_transaction).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Selected Transaction", style='Danger.TButton', command=self.delete_transaction).pack(side='left', padx=5)

        self.populate_account_combo()

    def bind_date_picker(self, entry_widget, string_var):
        try:
            from tkcalendar import DateEntry
        except ImportError:
            return
        def show_calendar(event):
            top = tk.Toplevel(entry_widget)
            top.title("Select Date")
            top.geometry("250x250")
            top.resizable(False, False)
            top.configure(bg=self.theme["POPUP_BG"])
            top.grab_set()
            x = entry_widget.winfo_rootx()
            y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
            top.geometry(f"+{x}+{y}")

            cal = DateEntry(top, width=12, background='darkblue', foreground='white',
                            borderwidth=2, date_pattern='yyyy-mm-dd')
            cal.pack(padx=10, pady=10)
            cal.set_date(string_var.get() or datetime.today().strftime('%Y-%m-%d'))

            def set_date():
                string_var.set(cal.get_date().strftime('%Y-%m-%d'))
                top.destroy()
            ttk.Button(top, text="OK", command=set_date).pack(pady=5)
            cal.bind("<Return>", lambda e: set_date())
        entry_widget.bind("<Button-1>", show_calendar)

    def on_period_change(self):
        period = self.period_var.get()
        if period == 'Custom':
            self.from_entry.configure(state='normal')
            self.to_entry.configure(state='normal')
        else:
            self.from_entry.configure(state='disabled')
            self.to_entry.configure(state='disabled')
            self.from_var.set('')
            self.to_var.set('')

    def get_date_range(self):
        period = self.period_var.get()
        today = datetime.today()
        if period == 'All':
            return None, None
        elif period == 'Today':
            return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'This Week':
            start = today - timedelta(days=today.weekday())
            return start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'This Month':
            start = today.replace(day=1)
            return start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'This Year':
            start = today.replace(month=1, day=1)
            return start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'Custom':
            from_date = self.from_var.get().strip()
            to_date = self.to_var.get().strip()
            if from_date and to_date:
                return from_date, to_date
            return None, None
        return None, None

    def populate_account_combo(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM accounts ORDER BY name")
        accounts = cur.fetchall()
        self.acc_combo['values'] = [f"{aid} - {name}" for aid, name in accounts]
        if accounts:
            self.acc_combo.current(0)
            self.refresh_transaction_list()
        else:
            for row in self.ledger_tree.get_children():
                self.ledger_tree.delete(row)

    def get_selected_account_id(self):
        sel = self.acc_combo.get()
        if sel:
            return int(sel.split(' - ')[0])
        return None

    def refresh_transaction_list(self):
        for row in self.ledger_tree.get_children():
            self.ledger_tree.delete(row)
        aid = self.get_selected_account_id()
        if not aid:
            return
        from_date, to_date = self.get_date_range()
        cur = self.conn.cursor()
        query = "SELECT id, date, description, type, amount FROM transactions WHERE account_id=? "
        params = [aid]
        if from_date and to_date:
            query += " AND date >= ? AND date <= ?"
            params.extend([from_date, to_date])
        query += " ORDER BY date, id"
        cur.execute(query, params)
        rows = cur.fetchall()
        balance = 0.0
        for tid, date, desc, ttype, amount in rows:
            credit = amount if ttype == 'credit' else 0.0
            debit = amount if ttype == 'debit' else 0.0
            balance += credit - debit
            self.ledger_tree.insert('', 'end', values=(
                tid, date, desc or "", f"{credit:,.2f}" if credit else "",
                f"{debit:,.2f}" if debit else "", f"{balance:,.2f}"
            ))

    def record_transaction(self):
        aid = self.get_selected_account_id()
        if not aid:
            messagebox.showerror("Error", "Please select an account.")
            return
        date = self.date_var.get().strip()
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Date must be YYYY-MM-DD.")
            return
        ttype = self.type_var.get()
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Amount must be a positive number.")
            return
        desc = self.desc_var.get().strip()

        self.conn.execute("INSERT INTO transactions (account_id, type, amount, description, date) VALUES (?,?,?,?,?)",
                          (aid, ttype, amount, desc, date))
        self.conn.commit()
        self.amount_var.set('')
        self.desc_var.set('')
        self.date_var.set(datetime.today().strftime('%Y-%m-%d'))
        self.refresh_transaction_list()
        self.refresh_overview()
        self.set_status("Transaction recorded.")

    def edit_transaction(self):
        if not self.check_admin():
            return
        selected = self.ledger_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a transaction to edit.")
            return
        tid = self.ledger_tree.item(selected[0])['values'][0]
        cur = self.conn.cursor()
        cur.execute("SELECT date, type, amount, description FROM transactions WHERE id=?", (tid,))
        row = cur.fetchone()
        if not row:
            return
        date, ttype, amount, desc = row

        self.date_var.set(date)
        self.type_var.set(ttype)
        self.amount_var.set(str(amount))
        self.desc_var.set(desc if desc else '')

        self.record_btn.destroy()
        self.update_btn = ttk.Button(self.entry_frame, text="🔄 Update Transaction", style='Success.TButton',
                                     command=lambda: self.do_update_transaction(tid))
        self.update_btn.grid(row=2, column=0, columnspan=5, pady=10)
        self.cancel_btn = ttk.Button(self.entry_frame, text="Cancel", command=self.cancel_edit)
        self.cancel_btn.grid(row=3, column=0, columnspan=5, pady=5)

    def do_update_transaction(self, tid):
        new_date = self.date_var.get().strip()
        try:
            datetime.strptime(new_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Date must be YYYY-MM-DD.")
            return
        new_type = self.type_var.get()
        try:
            new_amount = float(self.amount_var.get())
            if new_amount <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Amount must be a positive number.")
            return
        new_desc = self.desc_var.get().strip()

        self.conn.execute("UPDATE transactions SET date=?, type=?, amount=?, description=? WHERE id=?",
                          (new_date, new_type, new_amount, new_desc, tid))
        self.conn.commit()
        self.cancel_edit()
        self.refresh_transaction_list()
        self.refresh_overview()
        self.set_status("Transaction updated.")

    def cancel_edit(self):
        self.amount_var.set('')
        self.desc_var.set('')
        self.date_var.set(datetime.today().strftime('%Y-%m-%d'))
        if hasattr(self, 'update_btn'):
            self.update_btn.destroy()
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.destroy()
        self.record_btn = ttk.Button(self.entry_frame, text="📝 Record Transaction", style='Primary.TButton',
                                     command=self.record_transaction)
        self.record_btn.grid(row=2, column=0, columnspan=5, pady=10)

    def delete_transaction(self):
        if not self.check_admin():
            return
        selected = self.ledger_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a transaction to delete.")
            return
        tid = self.ledger_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this transaction? This cannot be undone."):
            self.conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
            self.conn.commit()
            self.refresh_transaction_list()
            self.refresh_overview()
            self.set_status("Transaction deleted.")

    # ---------------- Overview Tab ----------------
    def build_overview_tab(self):
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="Overview")

        title_lbl = ttk.Label(self.overview_frame, text="Accounts Overview", font=('Segoe UI', 14, 'bold'))
        title_lbl.pack(pady=10)

        cols = ('Account', 'Type', 'Total Credit', 'Total Debit', 'Net Balance')
        self.overview_tree = ttk.Treeview(self.overview_frame, columns=cols, show='headings', height=12)
        self.overview_tree.heading('Account', text='Account')
        self.overview_tree.heading('Type', text='Type')
        self.overview_tree.heading('Total Credit', text='Total Credit')
        self.overview_tree.heading('Total Debit', text='Total Debit')
        self.overview_tree.heading('Net Balance', text='Net Balance')
        self.overview_tree.column('Account', width=200, anchor='w')
        self.overview_tree.column('Type', width=80, anchor='center')
        self.overview_tree.column('Total Credit', width=120, anchor='center')
        self.overview_tree.column('Total Debit', width=120, anchor='center')
        self.overview_tree.column('Net Balance', width=120, anchor='center')
        self.overview_tree.pack(fill='both', expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self.overview_frame)
        btn_frame.pack(pady=(5,10))
        ttk.Button(btn_frame, text="🔄 Refresh Overview", style='Primary.TButton', command=self.refresh_overview).pack()

    def refresh_overview(self):
        for row in self.overview_tree.get_children():
            self.overview_tree.delete(row)

        cur = self.conn.cursor()
        cur.execute("SELECT id, name, type FROM accounts ORDER BY name")
        accounts = cur.fetchall()

        total_credit_all = 0.0
        total_debit_all = 0.0
        total_net_all = 0.0

        for aid, aname, atype in accounts:
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE account_id=? AND type='credit'", (aid,))
            credit = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE account_id=? AND type='debit'", (aid,))
            debit = cur.fetchone()[0]
            net = credit - debit

            total_credit_all += credit
            total_debit_all += debit
            total_net_all += net

            self.overview_tree.insert('', 'end', values=(
                aname, atype or 'Bank', f"{credit:,.2f}", f"{debit:,.2f}", f"{net:,.2f}"
            ))

        if accounts:
            self.overview_tree.insert('', 'end', values=(
                "GRAND TOTALS", "", f"{total_credit_all:,.2f}", f"{total_debit_all:,.2f}", f"{total_net_all:,.2f}"
            ), tags=('totals',))
            self.overview_tree.tag_configure('totals', background='#D5E8D4', font=('Segoe UI', 9, 'bold'))

    # ---------------- Reports Tab ----------------
    def build_report_tab(self):
        self.report_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.report_frame, text="Reports")

        top = ttk.Frame(self.report_frame)
        top.pack(fill='x', padx=10, pady=10)
        ttk.Label(top, text="Account:").pack(side='left')
        self.report_acc_combo = ttk.Combobox(top, state='readonly', font=('Segoe UI', 10), width=30)
        self.report_acc_combo.pack(side='left', padx=5)

        date_frame = ttk.Frame(self.report_frame)
        date_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(date_frame, text="Period:").grid(row=0, column=0, sticky='w')
        self.report_period_var = tk.StringVar(value='All')
        rperiod_combo = ttk.Combobox(date_frame, textvariable=self.report_period_var, state='readonly',
                                     values=['All', 'Today', 'This Week', 'This Month', 'This Year', 'Custom'],
                                     width=12, font=('Segoe UI', 10))
        rperiod_combo.grid(row=0, column=1, padx=5)
        rperiod_combo.bind('<<ComboboxSelected>>', lambda e: self.on_report_period_change())

        ttk.Label(date_frame, text="From:").grid(row=0, column=2, padx=(20,2))
        self.r_from_var = tk.StringVar()
        self.r_from_entry = tk.Entry(date_frame, textvariable=self.r_from_var, width=10, font=('Segoe UI', 10), state='disabled')
        self.r_from_entry.grid(row=0, column=3)
        self.bind_date_picker(self.r_from_entry, self.r_from_var)

        ttk.Label(date_frame, text="To:").grid(row=0, column=4, padx=2)
        self.r_to_var = tk.StringVar()
        self.r_to_entry = tk.Entry(date_frame, textvariable=self.r_to_var, width=10, font=('Segoe UI', 10), state='disabled')
        self.r_to_entry.grid(row=0, column=5)
        self.bind_date_picker(self.r_to_entry, self.r_to_var)

        ttk.Label(date_frame, text="(leave empty for all dates)").grid(row=0, column=6, padx=10)

        btn_frame = ttk.Frame(self.report_frame)
        btn_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(btn_frame, text="📄 Generate Account Statement", style='Success.TButton', command=self.generate_pdf).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📊 Generate Overall Report", style='Primary.TButton', command=self.generate_overall_pdf).pack(side='left', padx=5)

        self.populate_report_combo()

    def on_report_period_change(self):
        period = self.report_period_var.get()
        if period == 'Custom':
            self.r_from_entry.configure(state='normal')
            self.r_to_entry.configure(state='normal')
        else:
            self.r_from_entry.configure(state='disabled')
            self.r_to_entry.configure(state='disabled')
            self.r_from_var.set('')
            self.r_to_var.set('')

    def get_report_date_range(self):
        period = self.report_period_var.get()
        today = datetime.today()
        if period == 'All':
            return None, None
        elif period == 'Today':
            return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'This Week':
            start = today - timedelta(days=today.weekday())
            return start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'This Month':
            start = today.replace(day=1)
            return start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'This Year':
            start = today.replace(month=1, day=1)
            return start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif period == 'Custom':
            from_date = self.r_from_var.get().strip()
            to_date = self.r_to_var.get().strip()
            if from_date and to_date:
                return from_date, to_date
            return None, None
        return None, None

    def populate_report_combo(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM accounts ORDER BY name")
        accounts = cur.fetchall()
        self.report_acc_combo['values'] = [f"{aid} - {name}" for aid, name in accounts]
        if accounts:
            self.report_acc_combo.current(0)

    def generate_pdf(self):
        sel = self.report_acc_combo.get()
        if not sel:
            messagebox.showwarning("Warning", "Select an account.")
            return
        aid = int(sel.split(' - ')[0])
        aname = sel.split(' - ', 1)[1]

        from_date, to_date = self.get_report_date_range()
        for d in [from_date, to_date]:
            if d:
                try:
                    datetime.strptime(d, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Error", "Dates must be YYYY-MM-DD (or leave empty).")
                    return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            messagebox.showerror("Error", "reportlab library is required for PDF generation.")
            return

        cur = self.conn.cursor()
        cur.execute("SELECT type, bank_name, account_name, account_number FROM accounts WHERE id=?", (aid,))
        acct_info = cur.fetchone()
        atype, bname, acct_name, acct_num = acct_info

        filename = f"statement_{aname.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Account Statement – {aname}", styles['Title']))
        if atype == 'Bank':
            bank_text = f"Bank: {bname or 'N/A'} | Account: {acct_name or 'N/A'} | No: {acct_num or 'N/A'}"
            elements.append(Paragraph(bank_text, styles['Normal']))
        else:
            elements.append(Paragraph(f"Type: {atype}", styles['Normal']))
        if from_date or to_date:
            period = f"Period: {from_date or 'start'} to {to_date or 'end'}"
            elements.append(Paragraph(period, styles['Normal']))
        elements.append(Spacer(1, 12))

        query = "SELECT date, description, type, amount FROM transactions WHERE account_id=?"
        params = [aid]
        if from_date:
            query += " AND date >= ?"
            params.append(from_date)
        if to_date:
            query += " AND date <= ?"
            params.append(to_date)
        query += " ORDER BY date, id"
        cur.execute(query, params)
        rows = cur.fetchall()

        table_data = [["Date", "Description", "Credit", "Debit", "Balance"]]
        balance = 0.0
        total_credit = 0.0
        total_debit = 0.0

        for date, desc, ttype, amt in rows:
            credit = amt if ttype == 'credit' else 0.0
            debit = amt if ttype == 'debit' else 0.0
            balance += credit - debit
            total_credit += credit
            total_debit += debit
            table_data.append([date, desc or "", f"{credit:,.2f}" if credit else "",
                               f"{debit:,.2f}" if debit else "", f"{balance:,.2f}"])

        table_data.append(["", "TOTALS", f"{total_credit:,.2f}", f"{total_debit:,.2f}", f"{balance:,.2f}"])

        col_widths = [80, 220, 70, 70, 70]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor(self.theme["HEADER_BG"])),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-2), 0.5, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#D5E8D4")),
        ]))

        elements.append(table)
        doc.build(elements)

        try:
            if platform.system() == 'Windows':
                os.startfile(filename)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', filename])
            else:
                subprocess.run(['xdg-open', filename])
        except:
            pass

        self.set_status(f"PDF generated: {filename}")

    def generate_overall_pdf(self):
        from_date, to_date = self.get_report_date_range()
        for d in [from_date, to_date]:
            if d:
                try:
                    datetime.strptime(d, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Error", "Dates must be YYYY-MM-DD (or leave empty).")
                    return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            messagebox.showerror("Error", "reportlab library is required for PDF generation.")
            return

        cur = self.conn.cursor()
        cur.execute("SELECT id, name, type FROM accounts ORDER BY name")
        accounts = cur.fetchall()

        filename = f"overall_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Overall Accounts Report", styles['Title']))
        if from_date or to_date:
            period = f"Period: {from_date or 'start'} to {to_date or 'end'}"
            elements.append(Paragraph(period, styles['Normal']))
        elements.append(Spacer(1, 12))

        table_data = [["Account", "Type", "Credit", "Debit", "Net Balance"]]
        total_credit = 0.0
        total_debit = 0.0
        total_net = 0.0

        for aid, aname, atype in accounts:
            query = "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE account_id=? AND type='credit'"
            params = [aid]
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
            cur.execute(query, params)
            credit = cur.fetchone()[0]

            query = "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE account_id=? AND type='debit'"
            params = [aid]
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
            cur.execute(query, params)
            debit = cur.fetchone()[0]
            net = credit - debit

            total_credit += credit
            total_debit += debit
            total_net += net

            table_data.append([aname, atype or 'Bank', f"{credit:,.2f}", f"{debit:,.2f}", f"{net:,.2f}"])

        table_data.append(["GRAND TOTALS", "", f"{total_credit:,.2f}", f"{total_debit:,.2f}", f"{total_net:,.2f}"])

        col_widths = [120, 60, 80, 80, 80]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor(self.theme["HEADER_BG"])),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-2), 0.5, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#D5E8D4")),
        ]))

        elements.append(table)
        doc.build(elements)

        try:
            if platform.system() == 'Windows':
                os.startfile(filename)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', filename])
            else:
                subprocess.run(['xdg-open', filename])
        except:
            pass

        self.set_status(f"Overall report generated: {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AccountingApp(root)
    root.mainloop()
