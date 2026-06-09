import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import os
import platform
import subprocess

DB_NAME = "accounting.db"
ADMIN_PASSWORD = "admin"   # Change this to your desired password

class AccountingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Customer Credit/Debit Manager")
        self.root.geometry("950x650")
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.build_customers_tab()
        self.build_transactions_tab()
        self.build_report_tab()
    
    def check_admin(self):
        """Ask for admin password before critical operations."""
        pwd = simpledialog.askstring("Admin Password", "Enter admin password:", show="*")
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
                        email TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id INTEGER NOT NULL,
                        type TEXT CHECK(type IN ('credit','debit')) NOT NULL,
                        amount REAL NOT NULL,
                        description TEXT,
                        date TEXT NOT NULL,
                        FOREIGN KEY (customer_id) REFERENCES customers(id))''')
        self.conn.commit()
    
    # ---------------- Customers Tab ----------------
    def build_customers_tab(self):
        self.cust_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cust_frame, text="Customers")
        
        cols = ('ID', 'Name', 'Phone', 'Email')
        self.cust_tree = ttk.Treeview(self.cust_frame, columns=cols, show='headings', height=15)
        for col in cols:
            self.cust_tree.heading(col, text=col)
            self.cust_tree.column(col, width=120)
        self.cust_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(self.cust_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add Customer", command=self.add_customer).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Edit Customer", command=self.edit_customer).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete Customer", command=self.delete_customer).pack(side='left', padx=5)
        
        self.refresh_customer_list()
    
    def refresh_customer_list(self):
        for row in self.cust_tree.get_children():
            self.cust_tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, phone, email FROM customers ORDER BY name")
        for cid, name, phone, email in cur.fetchall():
            self.cust_tree.insert('', 'end', values=(cid, name, phone if phone else '', email if email else ''))
    
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
        cur.execute("SELECT name, phone, email FROM customers WHERE id=?", (cid,))
        name, phone, email = cur.fetchone()
        self._customer_dialog("Edit Customer", cid, name, phone, email)
    
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
    
    def _customer_dialog(self, title, cid=None, name='', phone='', email=''):
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.geometry("350x250")
        dlg.resizable(False, False)
        
        dlg.update_idletasks()
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        popup_w = 350
        popup_h = 250
        x = main_x + (main_w // 2) - (popup_w // 2)
        y = main_y + (main_h // 2) - (popup_h // 2)
        dlg.geometry(f"{popup_w}x{popup_h}+{x}+{y}")
        
        dlg.grab_set()
        dlg.lift()
        dlg.attributes('-topmost', True)
        
        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5)
        name_var = tk.StringVar(value=name)
        ttk.Entry(frame, textvariable=name_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Phone:").grid(row=1, column=0, sticky='w', pady=5)
        phone_var = tk.StringVar(value=phone)
        ttk.Entry(frame, textvariable=phone_var, width=25).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky='w', pady=5)
        email_var = tk.StringVar(value=email)
        ttk.Entry(frame, textvariable=email_var, width=25).grid(row=2, column=1, padx=5, pady=5)
        
        def save():
            n = name_var.get().strip()
            if not n:
                messagebox.showerror("Error", "Name is required.", parent=dlg)
                return
            if cid:
                self.conn.execute("UPDATE customers SET name=?, phone=?, email=? WHERE id=?",
                                  (n, phone_var.get(), email_var.get(), cid))
            else:
                self.conn.execute("INSERT INTO customers (name, phone, email) VALUES (?,?,?)",
                                  (n, phone_var.get(), email_var.get()))
            self.conn.commit()
            dlg.destroy()
            self.refresh_customer_list()
            self.populate_customer_combo()   # Update dropdowns instantly
            self.populate_report_combo()
            self.refresh_transaction_list()
            messagebox.showinfo("Success", "Customer saved.", parent=self.root)
        
        btn = ttk.Button(frame, text="💾 SAVE CUSTOMER", command=save)
        btn.grid(row=3, column=0, columnspan=2, pady=20)
        style = ttk.Style()
        style.configure('Big.TButton', font=('TkDefaultFont', 12, 'bold'))
        btn.configure(style='Big.TButton')
    
    # ---------------- Transactions Tab ----------------
    def build_transactions_tab(self):
        self.trans_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trans_frame, text="Transactions")
        
        top = ttk.Frame(self.trans_frame)
        top.pack(fill='x', padx=5, pady=5)
        ttk.Label(top, text="Customer:").pack(side='left')
        self.cust_combo = ttk.Combobox(top, state='readonly')
        self.cust_combo.pack(side='left', padx=5)
        self.cust_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_transaction_list())
        
        entry_frame = ttk.Frame(self.trans_frame)
        entry_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(entry_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky='w')
        self.date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        ttk.Entry(entry_frame, textvariable=self.date_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(entry_frame, text="Type:").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.type_var = tk.StringVar(value='credit')
        ttk.Radiobutton(entry_frame, text='Credit', variable=self.type_var, value='credit').grid(row=0, column=3)
        ttk.Radiobutton(entry_frame, text='Debit', variable=self.type_var, value='debit').grid(row=0, column=4)
        
        ttk.Label(entry_frame, text="Amount:").grid(row=1, column=0, sticky='w', pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.amount_var, width=15).grid(row=1, column=1, pady=5)
        
        ttk.Label(entry_frame, text="Description:").grid(row=1, column=2, sticky='w', padx=(20,0), pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.desc_var, width=25).grid(row=1, column=3, columnspan=2, padx=5, pady=5)
        
        ttk.Button(entry_frame, text="Record Transaction", command=self.record_transaction).grid(row=2, column=0, columnspan=5, pady=10)
        
        # Ledger view with delete button
        cols = ('ID', 'Date', 'Description', 'Credit', 'Debit', 'Balance')
        self.ledger_tree = ttk.Treeview(self.trans_frame, columns=cols, show='headings', height=15)
        self.ledger_tree.heading('ID', text='ID')
        self.ledger_tree.heading('Date', text='Date')
        self.ledger_tree.heading('Description', text='Description')
        self.ledger_tree.heading('Credit', text='Credit')
        self.ledger_tree.heading('Debit', text='Debit')
        self.ledger_tree.heading('Balance', text='Balance')
        # Hide ID column (but keep it to retrieve the transaction id)
        self.ledger_tree.column('ID', width=0, stretch=False)
        self.ledger_tree.column('Date', width=100)
        self.ledger_tree.column('Description', width=180)
        self.ledger_tree.column('Credit', width=90)
        self.ledger_tree.column('Debit', width=90)
        self.ledger_tree.column('Balance', width=90)
        self.ledger_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        ttk.Button(self.trans_frame, text="Delete Selected Transaction", command=self.delete_transaction).pack(pady=5)
        
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
            # Clear ledger when no customers
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
        messagebox.showinfo("Success", "Transaction recorded.")
    
    def delete_transaction(self):
        if not self.check_admin():
            return
        selected = self.ledger_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a transaction to delete.")
            return
        tid = self.ledger_tree.item(selected[0])['values'][0]  # hidden ID column
        if messagebox.askyesno("Confirm", "Delete this transaction? This cannot be undone."):
            self.conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
            self.conn.commit()
            self.refresh_transaction_list()
            messagebox.showinfo("Success", "Transaction deleted.")
    
    # ---------------- Reports Tab ----------------
    def build_report_tab(self):
        self.report_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.report_frame, text="Reports")
        
        top = ttk.Frame(self.report_frame)
        top.pack(fill='x', padx=10, pady=10)
        ttk.Label(top, text="Customer:").pack(side='left')
        self.report_cust_combo = ttk.Combobox(top, state='readonly', width=30)
        self.report_cust_combo.pack(side='left', padx=5)
        
        ttk.Button(top, text="Generate PDF Statement", command=self.generate_pdf).pack(side='left', padx=20)
        
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
        
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            messagebox.showerror("Error", "reportlab library is required for PDF generation.")
            return
        
        filename = f"statement_{cname.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Paragraph(f"Customer Statement – {cname}", styles['Title']))
        elements.append(Spacer(1, 12))
        
        cur = self.conn.cursor()
        cur.execute("SELECT date, description, type, amount FROM transactions WHERE customer_id=? ORDER BY date, id", (cid,))
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
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-2), 0.5, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
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
        
        messagebox.showinfo("Success", f"PDF generated:\n{filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AccountingApp(root)
    root.mainloop()
