import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import os
import platform
import subprocess

DB_NAME = "accounting.db"
ADMIN_PASSWORD = "admin"   # Change this to your desired password

# -------------------- Color Palette --------------------
BG_MAIN        = "#F0F4F8"
BG_TAB         = "#FFFFFF"
HEADER_BG      = "#2C3E50"
HEADER_FG      = "#FFFFFF"
BUTTON_PRIMARY = "#3498DB"
BUTTON_DANGER  = "#E74C3C"
BUTTON_SUCCESS = "#2ECC71"
BUTTON_WARN    = "#F39C12"
TEXT_DARK      = "#2C3E50"
TEXT_LIGHT     = "#FFFFFF"
ACCENT         = "#1ABC9C"

class AccountingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Customer Credit/Debit Manager")
        self.root.geometry("960x700")
        self.root.configure(bg=BG_MAIN)
        
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()
        self.migrate_tables()
        
        # -------------------- Styles --------------------
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=BG_MAIN)
        self.style.configure('TLabel', background=BG_MAIN, foreground=TEXT_DARK, font=('Segoe UI', 10))
        self.style.configure('TNotebook', background=BG_MAIN, borderwidth=0)
        self.style.configure('TNotebook.Tab', background=BG_TAB, foreground=TEXT_DARK, padding=[15, 5],
                             font=('Segoe UI', 10, 'bold'))
        self.style.map('TNotebook.Tab',
                       background=[('selected', ACCENT), ('active', '#D5E8D4')],
                       foreground=[('selected', TEXT_LIGHT)])
        self.style.configure('Primary.TButton', background=BUTTON_PRIMARY, foreground=TEXT_LIGHT,
                             borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        self.style.map('Primary.TButton',
                       background=[('active', '#2980B9'), ('pressed', '#1F6DA0')])
        self.style.configure('Danger.TButton', background=BUTTON_DANGER, foreground=TEXT_LIGHT,
                             borderwidth=0, font=('Segoe UI', 10, 'bold'))
        self.style.map('Danger.TButton',
                       background=[('active', '#C0392B'), ('pressed', '#A93226')])
        self.style.configure('Success.TButton', background=BUTTON_SUCCESS, foreground=TEXT_LIGHT,
                             borderwidth=0, font=('Segoe UI', 10, 'bold'))
        self.style.map('Success.TButton',
                       background=[('active', '#27AE60'), ('pressed', '#1E8449')])
        self.style.configure('Warn.TButton', background=BUTTON_WARN, foreground=TEXT_LIGHT,
                             borderwidth=0, font=('Segoe UI', 10, 'bold'))
        self.style.map('Warn.TButton',
                       background=[('active', '#D68910'), ('pressed', '#B9770E')])
        self.style.configure('Treeview', background=BG_TAB, foreground=TEXT_DARK,
                             rowheight=25, fieldbackground=BG_TAB, font=('Segoe UI', 9))
        self.style.configure('Treeview.Heading', background=HEADER_BG, foreground=HEADER_FG,
                             font=('Segoe UI', 9, 'bold'))
        self.style.map('Treeview', background=[('selected', ACCENT)], foreground=[('selected', TEXT_LIGHT)])
        self.style.configure('Status.TLabel', background=HEADER_BG, foreground=TEXT_LIGHT,
                             font=('Segoe UI', 9), padding=5)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=(5,0))
        
        self.build_customers_tab()
        self.build_transactions_tab()
        self.build_report_tab()
        
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(root, textvariable=self.status_var, style='Status.TLabel', anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")
    
    def set_status(self, msg, is_error=False, duration=3000):
        self.status_var.set(msg)
        if is_error:
            self.style.configure('Status.TLabel', background=BUTTON_DANGER)
        else:
            self.style.configure('Status.TLabel', background=BUTTON_SUCCESS)
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
        cur.execute('''CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT,
                        email TEXT,
                        bank_name TEXT,
                        account_name TEXT,
                        account_number TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id INTEGER NOT NULL,
                        type TEXT CHECK(type IN ('credit','debit')) NOT NULL,
                        amount REAL NOT NULL,
                        description TEXT,
                        date TEXT NOT NULL,
                        FOREIGN KEY (customer_id) REFERENCES customers(id))''')
        self.conn.commit()
    
    def migrate_tables(self):
        """Add bank columns if missing (for existing databases)."""
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(customers)")
        existing_cols = [col[1] for col in cur.fetchall()]
        for col, col_def in [('bank_name', 'TEXT'), ('account_name', 'TEXT'), ('account_number', 'TEXT')]:
            if col not in existing_cols:
                cur.execute(f"ALTER TABLE customers ADD COLUMN {col} {col_def}")
        self.conn.commit()
    
    # ---------------- Customers Tab ----------------
    def build_customers_tab(self):
        self.cust_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cust_frame, text="Customers")
        
        cols = ('ID', 'Name', 'Phone', 'Email', 'Bank Name', 'Account Name', 'Account No')
        self.cust_tree = ttk.Treeview(self.cust_frame, columns=cols, show='headings', height=15)
        widths = {'ID':40, 'Name':120, 'Phone':90, 'Email':130, 'Bank Name':100, 'Account Name':120, 'Account No':100}
        for col in cols:
            self.cust_tree.heading(col, text=col)
            self.cust_tree.column(col, width=widths.get(col, 100), anchor='center')
        self.cust_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(self.cust_frame)
        btn_frame.pack(pady=(0,10))
        ttk.Button(btn_frame, text="➕ Add Customer", style='Primary.TButton', command=self.add_customer).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Customer", style='Warn.TButton', command=self.edit_customer).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Customer", style='Danger.TButton', command=self.delete_customer).pack(side='left', padx=5)
        
        self.refresh_customer_list()
    
    def refresh_customer_list(self):
        for row in self.cust_tree.get_children():
            self.cust_tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, phone, email, bank_name, account_name, account_number FROM customers ORDER BY name")
        for row in cur.fetchall():
            self.cust_tree.insert('', 'end', values=(
                row[0], row[1], row[2] or '', row[3] or '', row[4] or '', row[5] or '', row[6] or ''
            ))
    
    def get_bank_list(self):
        """Return distinct non-empty bank names from customers."""
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT bank_name FROM customers WHERE bank_name IS NOT NULL AND bank_name != '' ORDER BY bank_name")
        return [row[0] for row in cur.fetchall()]
    
    def add_customer(self):
        if not self.check_admin():
            return
        self._customer_dialog("Add Customer")
    
    def edit_customer(self):
        if not self.check_admin():
            return
        selected = self.cust_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a customer to edit.")
            return
        cid = self.cust_tree.item(selected[0])['values'][0]
        cur = self.conn.cursor()
        cur.execute("SELECT name, phone, email, bank_name, account_name, account_number FROM customers WHERE id=?", (cid,))
        row = cur.fetchone()
        self._customer_dialog("Edit Customer", cid, row[0], row[1], row[2], row[3], row[4], row[5])
    
    def delete_customer(self):
        if not self.check_admin():
            return
        selected = self.cust_tree.selection()
        if not selected:
            return
        if messagebox.askyesno("Confirm", "Delete selected customer and all their transactions?"):
            cid = self.cust_tree.item(selected[0])['values'][0]
            self.conn.execute("DELETE FROM transactions WHERE customer_id=?", (cid,))
            self.conn.execute("DELETE FROM customers WHERE id=?", (cid,))
            self.conn.commit()
            self.refresh_customer_list()
            self.refresh_transaction_list()
            self.populate_customer_combo()
            self.populate_report_combo()
            self.set_status("Customer deleted.")
    
    def _customer_dialog(self, title, cid=None, name='', phone='', email='',
                         bank_name='', account_name='', account_number=''):
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.geometry("400x400")
        dlg.resizable(False, False)
        dlg.configure(bg=BG_MAIN)
        
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
        
        # Basic info
        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5)
        name_var = tk.StringVar(value=name)
        ttk.Entry(frame, textvariable=name_var, width=30, font=('Segoe UI', 10)).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Phone:").grid(row=1, column=0, sticky='w', pady=5)
        phone_var = tk.StringVar(value=phone)
        ttk.Entry(frame, textvariable=phone_var, width=30, font=('Segoe UI', 10)).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky='w', pady=5)
        email_var = tk.StringVar(value=email)
        ttk.Entry(frame, textvariable=email_var, width=30, font=('Segoe UI', 10)).grid(row=2, column=1, padx=5, pady=5)
        
        # Bank section
        ttk.Label(frame, text="Bank Name:").grid(row=3, column=0, sticky='w', pady=5)
        bank_var = tk.StringVar(value=bank_name)
        bank_combo = ttk.Combobox(frame, textvariable=bank_var, width=27, font=('Segoe UI', 10))
        bank_combo['values'] = self.get_bank_list()
        bank_combo.grid(row=3, column=1, padx=5, pady=5)
        # Allow typing new bank names
        bank_combo.configure(state='normal')
        
        ttk.Label(frame, text="Account Name:").grid(row=4, column=0, sticky='w', pady=5)
        acct_name_var = tk.StringVar(value=account_name)
        ttk.Entry(frame, textvariable=acct_name_var, width=30, font=('Segoe UI', 10)).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Account Number:").grid(row=5, column=0, sticky='w', pady=5)
        acct_num_var = tk.StringVar(value=account_number)
        ttk.Entry(frame, textvariable=acct_num_var, width=30, font=('Segoe UI', 10)).grid(row=5, column=1, padx=5, pady=5)
        
        def save():
            n = name_var.get().strip()
            if not n:
                messagebox.showerror("Error", "Name is required.", parent=dlg)
                return
            b_name = bank_var.get().strip()
            a_name = acct_name_var.get().strip()
            a_num = acct_num_var.get().strip()
            
            if cid:
                self.conn.execute("UPDATE customers SET name=?, phone=?, email=?, bank_name=?, account_name=?, account_number=? WHERE id=?",
                                  (n, phone_var.get(), email_var.get(), b_name, a_name, a_num, cid))
            else:
                self.conn.execute("INSERT INTO customers (name, phone, email, bank_name, account_name, account_number) VALUES (?,?,?,?,?,?)",
                                  (n, phone_var.get(), email_var.get(), b_name, a_name, a_num))
            self.conn.commit()
            dlg.destroy()
            self.refresh_customer_list()
            self.populate_customer_combo()
            self.populate_report_combo()
            self.refresh_transaction_list()
            self.set_status("Customer saved.")
        
        save_btn = ttk.Button(frame, text="💾 SAVE CUSTOMER", style='Success.TButton', command=save)
        save_btn.grid(row=6, column=0, columnspan=2, pady=20)
        self.style.configure('Success.TButton', font=('Segoe UI', 12, 'bold'))
        save_btn.configure(style='Success.TButton')
    
    # ---------------- Transactions Tab ----------------
    def build_transactions_tab(self):
        self.trans_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trans_frame, text="Transactions")
        
        top = ttk.Frame(self.trans_frame)
        top.pack(fill='x', padx=10, pady=10)
        ttk.Label(top, text="Customer:").pack(side='left')
        self.cust_combo = ttk.Combobox(top, state='readonly', font=('Segoe UI', 10))
        self.cust_combo.pack(side='left', padx=5)
        self.cust_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_transaction_list())
        
        entry_frame = ttk.Frame(self.trans_frame)
        entry_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(entry_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky='w')
        self.date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        ttk.Entry(entry_frame, textvariable=self.date_var, width=12, font=('Segoe UI', 10)).grid(row=0, column=1, padx=5)
        
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
        
        ttk.Button(entry_frame, text="📝 Record Transaction", style='Primary.TButton', command=self.record_transaction).grid(row=2, column=0, columnspan=5, pady=10)
        
        cols = ('ID', 'Date', 'Description', 'Credit', 'Debit', 'Balance')
        self.ledger_tree = ttk.Treeview(self.trans_frame, columns=cols, show='headings', height=15)
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
        
        ttk.Button(self.trans_frame, text="🗑️ Delete Selected Transaction", style='Danger.TButton', command=self.delete_transaction).pack(pady=5)
        
        self.populate_customer_combo()
    
    def populate_customer_combo(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM customers ORDER BY name")
        customers = cur.fetchall()
        self.cust_combo['values'] = [f"{cid} - {name}" for cid, name in customers]
        if customers:
            self.cust_combo.current(0)
            self.refresh_transaction_list()
        else:
            for row in self.ledger_tree.get_children():
                self.ledger_tree.delete(row)
    
    def get_selected_customer_id(self):
        sel = self.cust_combo.get()
        if sel:
            return int(sel.split(' - ')[0])
        return None
    
    def refresh_transaction_list(self):
        for row in self.ledger_tree.get_children():
            self.ledger_tree.delete(row)
        cid = self.get_selected_customer_id()
        if not cid:
            return
        cur = self.conn.cursor()
        cur.execute("SELECT id, date, description, type, amount FROM transactions WHERE customer_id=? ORDER BY date, id", (cid,))
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
        cid = self.get_selected_customer_id()
        if not cid:
            messagebox.showerror("Error", "Please select a customer.")
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
        
        self.conn.execute("INSERT INTO transactions (customer_id, type, amount, description, date) VALUES (?,?,?,?,?)",
                          (cid, ttype, amount, desc, date))
        self.conn.commit()
        self.amount_var.set('')
        self.desc_var.set('')
        self.date_var.set(datetime.today().strftime('%Y-%m-%d'))
        self.refresh_transaction_list()
        self.set_status("Transaction recorded.")
    
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
            self.set_status("Transaction deleted.")
    
    # ---------------- Reports Tab ----------------
    def build_report_tab(self):
        self.report_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.report_frame, text="Reports")
        
        top = ttk.Frame(self.report_frame)
        top.pack(fill='x', padx=10, pady=10)
        ttk.Label(top, text="Customer:").pack(side='left')
        self.report_cust_combo = ttk.Combobox(top, state='readonly', font=('Segoe UI', 10), width=30)
        self.report_cust_combo.pack(side='left', padx=5)
        
        date_frame = ttk.Frame(self.report_frame)
        date_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(date_frame, text="From (YYYY-MM-DD):").grid(row=0, column=0, sticky='w')
        self.report_from_var = tk.StringVar()
        ttk.Entry(date_frame, textvariable=self.report_from_var, width=12, font=('Segoe UI', 10)).grid(row=0, column=1, padx=5)
        ttk.Label(date_frame, text="To (YYYY-MM-DD):").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.report_to_var = tk.StringVar()
        ttk.Entry(date_frame, textvariable=self.report_to_var, width=12, font=('Segoe UI', 10)).grid(row=0, column=3, padx=5)
        ttk.Label(date_frame, text="(leave empty for all dates)").grid(row=0, column=4, padx=10)
        
        ttk.Button(top, text="📄 Generate PDF Statement", style='Success.TButton', command=self.generate_pdf).pack(side='left', padx=20)
        
        self.populate_report_combo()
    
    def populate_report_combo(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM customers ORDER BY name")
        customers = cur.fetchall()
        self.report_cust_combo['values'] = [f"{cid} - {name}" for cid, name in customers]
        if customers:
            self.report_cust_combo.current(0)
    
    def generate_pdf(self):
        sel = self.report_cust_combo.get()
        if not sel:
            messagebox.showwarning("Warning", "Select a customer.")
            return
        cid = int(sel.split(' - ')[0])
        cname = sel.split(' - ', 1)[1]
        
        from_date = self.report_from_var.get().strip()
        to_date = self.report_to_var.get().strip()
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
        
        # Fetch customer bank info
        cur = self.conn.cursor()
        cur.execute("SELECT bank_name, account_name, account_number FROM customers WHERE id=?", (cid,))
        bank_info = cur.fetchone()
        
        filename = f"statement_{cname.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Paragraph(f"Customer Statement – {cname}", styles['Title']))
        if bank_info and (bank_info[0] or bank_info[1] or bank_info[2]):
            bank_text = f"Bank: {bank_info[0] or 'N/A'} | Account Name: {bank_info[1] or 'N/A'} | Account No: {bank_info[2] or 'N/A'}"
            elements.append(Paragraph(bank_text, styles['Normal']))
        if from_date or to_date:
            period = f"Period: {from_date or 'start'} to {to_date or 'end'}"
            elements.append(Paragraph(period, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        query = "SELECT date, description, type, amount FROM transactions WHERE customer_id=?"
        params = [cid]
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
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor(HEADER_BG)),
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

if __name__ == "__main__":
    root = tk.Tk()
    app = AccountingApp(root)
    root.mainloop()
