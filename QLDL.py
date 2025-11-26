import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import sqlite3

class AppFullCRUD_English:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Inventory Management: PO & Project View")
        self.root.geometry("1350x750")
        
        self.init_db()
        self.current_po = None
        
        # --- 1. SEARCH TOOLBAR ---
        frame_search = ttk.LabelFrame(root, text="🔍 Search Tools", padding=10)
        frame_search.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_search, text="Enter Keyword:").pack(side=tk.LEFT)
        self.entry_search = ttk.Entry(frame_search, width=30)
        self.entry_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_search, text="🔎 Search", command=self.perform_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_search, text="🔄 Reset", command=self.reset_views).pack(side=tk.LEFT, padx=20)

        # --- 2. NOTEBOOK (TABS) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: PO View
        self.tab_po = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_po, text="📦 PO Management")
        self.setup_po_tab()

        # Tab 2: Project View
        self.tab_project = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_project, text="🏗️ Project Management")
        self.setup_project_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # ================= DATABASE =================
    def init_db(self):
        # We use the same database file so you don't lose data
        self.conn = sqlite3.connect("data_po_final.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS purchase_orders (po_number TEXT PRIMARY KEY, pic_name TEXT)')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS po_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT,
                item_name TEXT,
                quantity INTEGER,
                project_name TEXT,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY(po_number) REFERENCES purchase_orders(po_number)
            )
        ''')
        self.conn.commit()

    # ================= TAB 1: PO INTERFACE =================
    def setup_po_tab(self):
        paned = ttk.PanedWindow(self.tab_po, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- LEFT: LIST PO ---
        f_left = ttk.LabelFrame(paned, text="Purchase Orders (PO)", padding=5)
        paned.add(f_left, weight=1)
        
        # Add PO Area
        f_add = ttk.Frame(f_left)
        f_add.pack(fill=tk.X)
        self.e_po_num = ttk.Entry(f_add, width=12)
        self.e_po_num.pack(side=tk.LEFT, padx=2)
        ttk.Button(f_add, text="Create PO", command=self.add_po).pack(side=tk.LEFT)

        # Table PO
        self.tree_po = ttk.Treeview(f_left, columns=("po", "pic"), show="headings", height=20)
        self.tree_po.heading("po", text="PO Number")
        self.tree_po.column("po", width=100)
        self.tree_po.heading("pic", text="PIC")
        self.tree_po.column("pic", width=100)
        self.tree_po.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree_po.bind("<<TreeviewSelect>>", self.on_po_select)

        # Action Buttons PO
        f_act_po = ttk.Frame(f_left)
        f_act_po.pack(fill=tk.X, pady=5)
        ttk.Button(f_act_po, text="❌ Delete PO", command=self.delete_po).pack(side=tk.RIGHT, padx=2)
        ttk.Button(f_act_po, text="✏️ Edit PIC", command=self.edit_po_pic).pack(side=tk.RIGHT, padx=2)

        # --- RIGHT: ITEMS ---
        f_right = ttk.LabelFrame(paned, text="Item Details", padding=5)
        paned.add(f_right, weight=3)
        
        # === INPUT AREA (WITH COMBOBOX) ===
        f_item = ttk.Frame(f_right)
        f_item.pack(fill=tk.X, pady=5)
        
        tk.Label(f_item, text="Item:").pack(side=tk.LEFT)
        self.e_itm_name = ttk.Entry(f_item, width=15)
        self.e_itm_name.pack(side=tk.LEFT, padx=2)
        
        tk.Label(f_item, text="Qty:").pack(side=tk.LEFT)
        self.e_itm_qty = ttk.Entry(f_item, width=5)
        self.e_itm_qty.pack(side=tk.LEFT, padx=2)
        
        tk.Label(f_item, text="Project:").pack(side=tk.LEFT)
        
        # Combobox for Projects
        self.e_itm_proj = ttk.Combobox(f_item, width=15)
        self.e_itm_proj.pack(side=tk.LEFT, padx=2)
        self.e_itm_proj.configure(postcommand=self.update_project_suggestions) 
        
        ttk.Button(f_item, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=5)

        # Table Items
        cols = ("id", "proj", "name", "qty", "status")
        self.tree_po_items = ttk.Treeview(f_right, columns=cols, show="headings")
        self.tree_po_items.heading("id", text="ID"); self.tree_po_items.column("id", width=30)
        self.tree_po_items.heading("proj", text="Project"); self.tree_po_items.column("proj", width=100)
        self.tree_po_items.heading("name", text="Item Name")
        self.tree_po_items.heading("qty", text="Qty"); self.tree_po_items.column("qty", width=50)
        self.tree_po_items.heading("status", text="Status"); self.tree_po_items.column("status", width=100)
        
        self.tree_po_items.tag_configure('received', foreground='green', font=('Arial', 9, 'bold'))
        self.tree_po_items.pack(fill=tk.BOTH, expand=True)

        # Item Action Buttons
        f_act_item = ttk.Frame(f_right)
        f_act_item.pack(fill=tk.X, pady=5)
        
        ttk.Button(f_act_item, text="✅ Mark Received", command=lambda: self.mark_received(self.tree_po_items)).pack(side=tk.RIGHT, padx=2)
        ttk.Button(f_act_item, text="✏️ Edit Item", command=lambda: self.open_edit_item_dialog(self.tree_po_items)).pack(side=tk.RIGHT, padx=2)
        ttk.Button(f_act_item, text="❌ Delete Item", command=lambda: self.delete_item(self.tree_po_items)).pack(side=tk.RIGHT, padx=2)
        
        self.load_po_list()

    # --- HELPER: Update Combobox ---
    def update_project_suggestions(self):
        """Fetch unique project names from DB for autocomplete"""
        self.cursor.execute("SELECT DISTINCT project_name FROM po_items WHERE project_name != '' ORDER BY project_name ASC")
        projects = [row[0] for row in self.cursor.fetchall()]
        self.e_itm_proj['values'] = projects

    # ================= TAB 2: PROJECT INTERFACE =================
    def setup_project_tab(self):
        paned = ttk.PanedWindow(self.tab_project, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left: Project List
        f_left = ttk.LabelFrame(paned, text="Project List", padding=5)
        paned.add(f_left, weight=1)
        self.tree_projects = ttk.Treeview(f_left, columns=("proj",), show="headings")
        self.tree_projects.heading("proj", text="Project Name")
        self.tree_projects.pack(fill=tk.BOTH, expand=True)
        self.tree_projects.bind("<<TreeviewSelect>>", self.on_project_select)

        # Right: Items
        f_right = ttk.LabelFrame(paned, text="Project Summary", padding=5)
        paned.add(f_right, weight=3)
        
        cols = ("id", "po", "name", "qty", "status")
        self.tree_proj_items = ttk.Treeview(f_right, columns=cols, show="headings")
        self.tree_proj_items.heading("id", text="ID"); self.tree_proj_items.column("id", width=30)
        self.tree_proj_items.heading("po", text="From PO")
        self.tree_proj_items.heading("name", text="Item Name")
        self.tree_proj_items.heading("qty", text="Qty")
        self.tree_proj_items.heading("status", text="Status")
        self.tree_proj_items.tag_configure('received', foreground='green', font=('Arial', 9, 'bold'))
        self.tree_proj_items.pack(fill=tk.BOTH, expand=True)

        # Project View Actions
        f_act_item = ttk.Frame(f_right)
        f_act_item.pack(fill=tk.X, pady=5)
        ttk.Button(f_act_item, text="✅ Mark Received", command=lambda: self.mark_received(self.tree_proj_items)).pack(side=tk.RIGHT, padx=2)
        ttk.Button(f_act_item, text="✏️ Edit Item", command=lambda: self.open_edit_item_dialog(self.tree_proj_items)).pack(side=tk.RIGHT, padx=2)
        ttk.Button(f_act_item, text="❌ Delete Item", command=lambda: self.delete_item(self.tree_proj_items)).pack(side=tk.RIGHT, padx=2)

    # ================= LOGIC & CRUD FUNCTIONS =================

    def add_po(self):
        po = self.e_po_num.get().strip()
        if not po: return
        try:
            self.cursor.execute("INSERT INTO purchase_orders (po_number, pic_name) VALUES (?, ?)", (po, ""))
            self.conn.commit()
            self.load_po_list()
            self.e_po_num.delete(0, tk.END)
        except sqlite3.IntegrityError: messagebox.showerror("Error", "PO Number already exists!")

    def delete_po(self):
        sel = self.tree_po.selection()
        if not sel: return
        po_to_del = self.tree_po.item(sel[0])['values'][0]
        confirm = messagebox.askyesno("Warning", f"Are you sure you want to delete PO: {po_to_del}?\n\nALL items inside this PO will also be deleted!")
        if confirm:
            try:
                self.cursor.execute("DELETE FROM po_items WHERE po_number = ?", (po_to_del,))
                self.cursor.execute("DELETE FROM purchase_orders WHERE po_number = ?", (po_to_del,))
                self.conn.commit()
                self.load_po_list()
                for row in self.tree_po_items.get_children(): self.tree_po_items.delete(row)
                messagebox.showinfo("Success", "PO and related items deleted.")
            except Exception as e: messagebox.showerror("Error", str(e))

    def edit_po_pic(self):
        sel = self.tree_po.selection()
        if not sel: return
        po_num = self.tree_po.item(sel[0])['values'][0]
        dialog = Toplevel(self.root)
        dialog.title(f"Edit PIC for PO {po_num}")
        dialog.geometry("300x150")
        tk.Label(dialog, text="Enter new PIC Name:").pack(pady=10)
        e_new_pic = ttk.Entry(dialog)
        e_new_pic.pack(pady=5); e_new_pic.focus()
        def save_pic():
            new_name = e_new_pic.get().strip()
            self.cursor.execute("UPDATE purchase_orders SET pic_name = ? WHERE po_number = ?", (new_name, po_num))
            self.conn.commit()
            self.load_po_list()
            dialog.destroy()
        ttk.Button(dialog, text="Save", command=save_pic).pack(pady=10)

    def add_item(self):
        if not self.current_po: 
            messagebox.showwarning("Notice", "Please select a PO first!")
            return
        name, qty, proj = self.e_itm_name.get().strip(), self.e_itm_qty.get().strip(), self.e_itm_proj.get().strip()
        if name and qty.isdigit() and proj:
            self.cursor.execute("INSERT INTO po_items (po_number, item_name, quantity, project_name, status) VALUES (?,?,?,?,?)",
                                (self.current_po, name, int(qty), proj, "Pending"))
            self.conn.commit()
            self.load_po_items()
            self.e_itm_name.delete(0, tk.END); self.e_itm_qty.delete(0, tk.END)

    def delete_item(self, treeview):
        sel = treeview.selection()
        if not sel: return
        item_id = treeview.item(sel[0])['values'][0]
        item_name = treeview.item(sel[0])['values'][2]
        if messagebox.askyesno("Confirm", f"Delete item: {item_name}?"):
            self.cursor.execute("DELETE FROM po_items WHERE id = ?", (item_id,))
            self.conn.commit()
            self.refresh_current_view()

    def open_edit_item_dialog(self, treeview):
        sel = treeview.selection()
        if not sel: return messagebox.showwarning("Error", "No row selected for editing")
        vals = treeview.item(sel[0])['values']
        item_id = vals[0]
        self.cursor.execute("SELECT item_name, quantity, project_name FROM po_items WHERE id = ?", (item_id,))
        old_data = self.cursor.fetchone()
        
        dialog = Toplevel(self.root)
        dialog.title("Edit Item Details")
        dialog.geometry("300x250")
        
        tk.Label(dialog, text="Item Name:").pack(pady=2)
        e_name = ttk.Entry(dialog); e_name.pack(); e_name.insert(0, old_data[0])
        
        tk.Label(dialog, text="Quantity:").pack(pady=2)
        e_qty = ttk.Entry(dialog); e_qty.pack(); e_qty.insert(0, old_data[1])
        
        tk.Label(dialog, text="Project:").pack(pady=2)
        e_proj = ttk.Combobox(dialog) 
        e_proj.pack()
        e_proj.insert(0, old_data[2])
        # Load suggestions for popup
        self.cursor.execute("SELECT DISTINCT project_name FROM po_items WHERE project_name != ''")
        e_proj['values'] = [row[0] for row in self.cursor.fetchall()]

        def save_edit():
            self.cursor.execute("UPDATE po_items SET item_name=?, quantity=?, project_name=? WHERE id=?", 
                                (e_name.get(), e_qty.get(), e_proj.get(), item_id))
            self.conn.commit()
            self.refresh_current_view()
            dialog.destroy()
            messagebox.showinfo("Success", "Updated successfully!")
        ttk.Button(dialog, text="Save Changes", command=save_edit).pack(pady=15)

    def mark_received(self, treeview):
        sel = treeview.selection()
        if not sel: return
        item_id = treeview.item(sel[0])['values'][0]
        # Change status from 'Pending' (or Vietnamese 'Chưa nhận') to 'Received'
        self.cursor.execute("UPDATE po_items SET status = 'Received' WHERE id = ?", (item_id,))
        self.conn.commit()
        self.refresh_current_view()

    def perform_search(self):
        keyword = self.entry_search.get().strip()
        if not keyword: return
        
        # Search PO
        self.cursor.execute("SELECT po_number, pic_name FROM purchase_orders WHERE po_number LIKE ?", ('%' + keyword + '%',))
        po_res = self.cursor.fetchall()
        if po_res:
            self.notebook.select(0)
            for row in self.tree_po.get_children(): self.tree_po.delete(row)
            for row in po_res: self.tree_po.insert("", tk.END, values=row)
            return
        
        # Search Project
        self.cursor.execute("SELECT DISTINCT project_name FROM po_items WHERE project_name LIKE ?", ('%' + keyword + '%',))
        proj_res = self.cursor.fetchall()
        if proj_res:
            self.notebook.select(1)
            for row in self.tree_projects.get_children(): self.tree_projects.delete(row)
            for row in proj_res: self.tree_projects.insert("", tk.END, values=row)
            return
        
        messagebox.showinfo("Result", "No matching data found.")

    def reset_views(self):
        self.entry_search.delete(0, tk.END)
        self.load_po_list()
        self.load_project_list()

    def refresh_current_view(self):
        if self.notebook.index("current") == 0: self.load_po_items()
        else: self.on_project_select(None)

    def load_po_list(self):
        for row in self.tree_po.get_children(): self.tree_po.delete(row)
        self.cursor.execute("SELECT po_number, pic_name FROM purchase_orders")
        for row in self.cursor.fetchall(): self.tree_po.insert("", tk.END, values=row)

    def on_po_select(self, event):
        sel = self.tree_po.selection()
        if not sel: return
        self.current_po = self.tree_po.item(sel[0])['values'][0]
        self.load_po_items()

    def load_po_items(self):
        for row in self.tree_po_items.get_children(): self.tree_po_items.delete(row)
        self.cursor.execute("SELECT id, project_name, item_name, quantity, status FROM po_items WHERE po_number=?", (self.current_po,))
        for row in self.cursor.fetchall():
            item_id = self.tree_po_items.insert("", tk.END, values=row)
            # Check for both English 'Received' and Vietnamese 'Đã nhận' (for compatibility)
            if row[4] in ["Received", "Đã nhận"]: 
                self.tree_po_items.item(item_id, tags=('received',))

    def load_project_list(self):
        for row in self.tree_projects.get_children(): self.tree_projects.delete(row)
        self.cursor.execute("SELECT DISTINCT project_name FROM po_items WHERE project_name != ''")
        for row in self.cursor.fetchall(): self.tree_projects.insert("", tk.END, values=row)

    def on_project_select(self, event):
        sel = self.tree_projects.selection()
        if not sel: return
        self.current_project = self.tree_projects.item(sel[0])['values'][0]
        for row in self.tree_proj_items.get_children(): self.tree_proj_items.delete(row)
        self.cursor.execute("SELECT id, po_number, item_name, quantity, status FROM po_items WHERE project_name=?", (self.current_project,))
        for row in self.cursor.fetchall():
            item_id = self.tree_proj_items.insert("", tk.END, values=row)
            if row[4] in ["Received", "Đã nhận"]: 
                self.tree_proj_items.item(item_id, tags=('received',))

    def on_tab_change(self, event):
        if self.notebook.index("current") == 1: self.load_project_list()
        else: self.load_po_list()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = AppFullCRUD_English(root)
    root.mainloop()