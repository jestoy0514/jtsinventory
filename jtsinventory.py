#!/usr/bin/env python3
#
# jtsinventory.py - a simple inventory management software.
# Copyright (c) 2016 | Jesus Vedasto Olazo | jessie@jestoy.frihost.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""A simple inventory management software for small business."""

try:
    import tkinter as tk
    import tkinter.messagebox as mb
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
except:
    import Tkinter as tk
    import tkMessageBox  as mb
    import ttk
    from ScrolledText import ScrolledText

from PIL import Image, ImageTk
from fpdf import FPDF
import sys
import os
import sqlite3
import time
import hashlib
import csv
import json

__version__ = "1.0.0"

class Application(tk.Tk):
    pass

class MainWindow(tk.Frame):

    def __init__(self, master=None, **options):
        tk.Frame.__init__(self, master, **options)
        self.pack()
        # Initialize database
        # This part will test if the software run for the first time.
        # If so create the necessary config file for the software.
        # For now the config file consist of default database name.
        if not os.path.isfile('config.json'):
            first = NewDBWindow(self.master)
            self.wait_window(first)
            if not first.status:
                self._close()
                sys.exit()

        # This part will now try to load the database name using config.
        with open('config.json', 'r') as cf:
            data = json.load(cf)
            
        default_db = data['default_db']
        # Then this will check whether the database is available or not.
        # If not create the database and tables and then close it.
        if not os.path.isfile(default_db):
            self.db = Database()
            self.db.openDB(default_db)
            self.db.closeDB()
        # This will prompt a username and password to be able to continue
        # using the software. Default username "ADMIN" and password "ADMIN"
        # is provided upon using the software for the first time.
        self.login = LoginWindow(self.master)
        # This part right here will not execute other codes unless the login
        # window has been closed to be able to get the login status of the
        # user.
        self.wait_window(self.login)
        # Check if the username and password match from the database. If so
        # initialize graphical user interface.
        if self.login.status:
            self.setupUI()
        
    def setupUI(self):
        # This code sets the title of the window.
        title = ["JTS-Inventory", __version__]
        self.master.title(" ".join(title))
        self.master.iconbitmap('jtsinventory_icon.ico')
        # Sets the default position of the application.
        self.master.geometry("+10+10")
        # Remove resize function to the window.
        self.master.resizable(False, False)
        # Create an event which will trigged with control + either Q or q.
        self.master.event_add("<<QuitApp>>", "<Control-Q>", "<Control-q>")
        self.master.event_add("<<Menus>>",
                              "<Control-Shift-p>", "<Control-Shift-P>")
        # Bind the event to the root window.
        self.master.bind("<<QuitApp>>", self._closeEvent)
        self.master.bind("<<Menus>>", self.eventHandler)
        # Create protocol for self.master.
        self.master.protocol("WM_DELETE_WINDOW", self._close)

        # Sets the style of the application.
        self.style = ttk.Style()
        self.style.configure("Main.TButton",
                             background="orange",
                             font=("Tahoma", 12, "bold"),
                             width=15,
                             foreground="blue"
                             )
        # Create menubars and menus.
        menubar = tk.Menu(self.master)
        self.master["menu"] = menubar

        filemenu = tk.Menu(menubar, tearoff=0)
        optionmenu = tk.Menu(menubar, tearoff=0)
        helpmenu = tk.Menu(menubar, tearoff=0)

        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Option", menu=optionmenu)
        menubar.add_cascade(label="Help", menu=helpmenu)

        filemenu.add_command(label="Products",
                             command=lambda: self.menuHandler("PRODUCT"))
        filemenu.add_command(label="Incoming",
                             command=lambda: self.menuHandler("IN"))
        filemenu.add_command(label="Outgoing",
                             command=lambda: self.menuHandler("OUT"))
        filemenu.add_command(label="Adjustment",
                             command=lambda: self.menuHandler("ADJUST"))
        filemenu.add_command(label="Reports",
                             command=lambda: self.menuHandler("REPORT"))
        filemenu.add_separator()
        filemenu.add_command(label="Quit", accelerator="Ctrl+Q",
                             command=self._close)
        # Check if the user is if type ADMIN, meaning he/she has the
        # authority to change master data from the system. If not ADMIN
        # then disable the option menu to avoid changes.
        if self.login.usertype == "ADMIN":
            optionmenu.add_command(label="User Management",
                                   command=lambda: self.menuHandler("USERS"))
            optionmenu.add_command(label="Cost Centers",
                                   command=lambda: self.menuHandler("CCENTERS"))
            print_trans_menu = tk.Menu(optionmenu, tearoff=0)
            optionmenu.add_cascade(label="Print Transaction", menu=print_trans_menu)
            print_trans_menu.add_command(label="Incoming",
                                         command=lambda: self.menuHandler("PRINT_IN"))
            print_trans_menu.add_command(label="Outgoing",
                                         command=lambda: self.menuHandler("PRINT_OUT"))
            print_trans_menu.add_command(label="Adjustment",
                                         command=lambda: self.menuHandler("PRINT_ADJ"))

        helpmenu.add_command(label="Help",
                             command=lambda: self.menuHandler("HELP"))
        helpmenu.add_command(label="License",
                             command=lambda: self.menuHandler("LICENSE"))
        helpmenu.add_command(label="About",
                             command=lambda: self.menuHandler("ABOUT"))

        # Create 6 buttons for product, in, out, adjustment,
        # reports, & settings.
        in_img_open = Image.open('images/cart-12.png')
        self.in_img = ImageTk.PhotoImage(in_img_open.resize((48, 48)))
        out_img_open = Image.open('images/cashier-1.png')
        self.out_img = ImageTk.PhotoImage(out_img_open.resize((48, 48)))
        rep_img_open = Image.open('images/bar-chart.png')
        self.rep_img = ImageTk.PhotoImage(rep_img_open.resize((48, 48)))
        set_img_open = Image.open('images/settings.png')
        self.set_img = ImageTk.PhotoImage(set_img_open.resize((48, 48)))
        pro_img_open = Image.open('images/barcode.png')
        self.pro_img = ImageTk.PhotoImage(pro_img_open.resize((48, 48)))
        adj_img_open = Image.open('images/tape.png')
        self.adj_img = ImageTk.PhotoImage(adj_img_open.resize((48, 48)))
        
        self.in_btn = ttk.Button(self, text="Incoming",
                                 image=self.in_img,
                                 compound="top",
                                 style="Main.TButton"
                                 )
        self.in_btn.grid(row=1, column=0, sticky="nesw")
        self.in_btn.bind("<Button-1>", self.eventHandler)
        self.out_btn = ttk.Button(self, text="Outgoing",
                                  image=self.out_img,
                                  compound="top",
                                  style="Main.TButton"
                                  )
        self.out_btn.grid(row=1, column=1, sticky="we")
        self.out_btn.bind("<Button-1>", self.eventHandler)
        self.report_btn = ttk.Button(self, text="Reports",
                                     image=self.rep_img,
                                     compound="top",
                                     style="Main.TButton"
                                     )
        self.report_btn.grid(row=2, column=0, sticky="we")
        self.report_btn.bind("<Button-1>", self.eventHandler)
        self.setting_btn = ttk.Button(self, text="Settings",
                                      image=self.set_img,
                                      compound="top",
                                      style="Main.TButton"
                                      )
        self.setting_btn.grid(row=2, column=1, sticky="we")
        self.setting_btn.bind("<Button-1>", self.eventHandler)
        # Check if the user is if type ADMIN, meaning he/she has the
        # authority to change master data from the system. If not ADMIN
        # then disable the setting option to avoid changes.
        if self.login.usertype != "ADMIN":
            self.setting_btn.config(state="disable")
        self.product_btn = ttk.Button(self, text="Products",
                                      image=self.pro_img,
                                      compound="top",
                                      style="Main.TButton"
                                      )
        self.product_btn.grid(row=0, column=0, sticky="we")
        self.product_btn.bind("<Button-1>", self.eventHandler)

        self.adjust_btn = ttk.Button(self, text="Adjustment",
                                      image=self.adj_img,
                                      compound="top",
                                      style="Main.TButton"
                                     )
        self.adjust_btn.grid(row=0, column=1, sticky="we")
        self.adjust_btn.bind("<Button-1>", self.eventHandler)

        # Create the status bar for username, time and date information.
        self.status_var = tk.StringVar()
        self.status_var.set("")
        self.status_bar = tk.Label(self,
                                   textvariable=self.status_var,
                                   relief="sunken",
                                   anchor="w",
                                   fg="blue",
                                   bd=3,
                                   font=("Tahoma", 8, "bold"))
        self.status_bar.grid(row=3, column=0, columnspan=2, sticky="we")
        # The function below will update the status bar every second to be
        # able to update the clock.
        self.updateStatusBar()

    def updateStatusBar(self):
        """This method takes no argument and use only to update the statusbar."""
        mytime = time.strftime("%I:%M:%S %p | %A | %d-%b-%y | ")
        self.status_var.set(mytime+self.login.username.title())
        self.status_bar.after(1000, self.updateStatusBar)

    def menuHandler(self, data):
        """This method is use for menubar bar commands handler."""
        if data.title() == "Product":
            ProductWindow(self)
        elif data.title() == "In":
            IncomingWindow(self)
        elif data.title() == "Out":
            OutgoingWindow(self)
        elif data.title() == "Adjust":
            AdjustmentWindow(self)
        elif data.title() == "Report":
            ReportWindow(self)
        elif data.title() == "Users":
            UsersWindow(self)
        elif data.title() == "Ccenters":
            CostCenterWindow(self)
        elif data.title() == "Help":
            HelpWindow(self)
        elif data.title() == "License":
            LicenseWindow(self)
        elif data.title() == "About":
            AboutWindow(self)
        else:
            pass

    def eventHandler(self, event):
        """This method is use for button event handling."""
        command = event.widget.cget('text')
        if command == "Products":
            ProductWindow(self)
        elif command == "Reports":
            ReportWindow(self)
        elif event == "USERS":
            UsersWindow(self)
        elif event == "LICENSE":
            LicenseWindow(self)
        elif event == "ABOUT":
            AboutWindow(self)
        elif event == "HELP":
            HelpWindow(self)
        elif command == "Incoming":
            IncomingWindow(self)
        elif command == "Outgoing":
            OutgoingWindow(self)
        elif event == "CCENTERS":
            CostCenterWindow(self)
        elif command == "Adjustment":
            AdjustmentWindow(self)
        else:
            pass

    def _closeEvent(self, event):
        """Event handler for closing the application."""
        self._close()

    def _close(self):
        """This method is use for properly cling the application."""
        # Ask first if user wants to quit or not. If so close the app.
        askquit = mb.askokcancel("Quit?", "Close the application?")
        if askquit:
            self.master.destroy()
        else:
            return

# Start of ReportWindow class.
class ReportWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        # Open the config file using json module.
        with open('config.json', 'r') as cf:
            data = json.load(cf)
        # Initialize database.
        self.db = Database()
        db = data['default_db']
        self.db.openDB(db)
        # Load the grahical user interface.
        self.setupUI()

    def setupUI(self):
        self.title("Reports")
        self.grab_set()
        self.geometry("200x200")
        self.protocol("WM_DELETE_WINDOW", self._close)
        mainframe = tk.Frame(self)
        mainframe.pack(expand=True, fill="both")
        rep_config = ["Current_Stock", "Stock_Ledger",
                      "Closing_Stock", "Reorder_Level",
                      "Incoming", "Outgoing",
                      "Adjustment", "Consumption"
                      ]
        rep_config.sort()
        self.option_list = tk.Listbox(mainframe, activestyle='none',
                                      relief="flat", selectforeground="white",
                                      selectbackground="orange")
        self.option_list.pack(expand=True, fill='x')
        for elem in rep_config:
            self.option_list.insert('end', elem)
            
        self.option_list.bind("<Double-Button-1>", self.eventHandler)
        self.option_list.focus_set()
        self.option_list.selection_set(0)
        self.option_list.config(font=("Times", 12, 'bold'))

    def eventHandler(self, event):
        pos = event.widget.curselection()[0]
        list_value = event.widget.get(pos)
        stock = """
                Select
                products.id,
                code,
                description,
                unit,
                (Select Avg(price) From in_transaction Where product_id=products.id),
                (Select Sum(quantity) From in_transaction Where product_id=products.id),
                (Select Sum(quantity) From out_transaction Where product_id=products.id),
                (Select Sum(quantity) From adjust_trans Where product_id=products.id)
                From products
                Left Outer Join in_transaction On products.id = in_transaction.product_id
                Left Outer Join out_transaction On products.id = out_transaction.product_id
                Left Outer Join adjust_trans On products.id = adjust_trans.product_id
                Group By products.id
                """
        query = self.db.cur.execute(stock)
        data = query.fetchall()
        if list_value == "Current_Stock":
            amount = 0
            options = {'mode': "currentstock"}
            pdf = PDF(**options)
            pdf.alias_nb_pages()
            pdf.add_page()
            # The rest of the report will be inserted here.
            pdf.set_font('Courier', '', 10)
            for item in data:
                rate = item[4]
                rec_qty = item[5]
                iss_qty = item[6]
                adj_qty = item[7]
                if item[5] == None:
                    rec_qty = 0.0
                if item[4] == None:
                    rate = 0.0
                if item[6] == None:
                    iss_qty = 0.0
                if item[7] == None:
                    adj_qty = 0.0
                qty = rec_qty - iss_qty + adj_qty
                value = qty * rate
                amount += value
                pdf.cell(15, 10, str(item[0]), 0, 0, 'C')
                pdf.cell(30, 10, item[1], 0, 0, 'C')
                pdf.cell(60, 10, item[2][0:25])
                pdf.cell(15, 10, item[3], 0, 0, 'C')
                pdf.cell(20, 10, format(qty, '0.2f'), 0, 0, 'R')
                pdf.cell(20, 10, format(rate, '0.2f'), 0, 0, 'R')
                pdf.cell(30, 10, format(value, '0,.2f'), 0, 0, 'R')
                pdf.ln(5)
            pdf.ln(25)
            pdf.set_font('Courier', 'B', 10)
            pdf.cell(0, 7, "Total Amount: " + format(amount, '0,.2f'), 1, 0, 'R')
            pdf.output('reports/currentstock.pdf', 'F')

            try:
                os.system('start '+'reports/currentstock.pdf')
                self._close()
            except:
                print("Error Printing")
        elif list_value == "Stock_Ledger":
            mb.showinfo("Information", "Available Soon!")
            self._close()
        elif list_value == "Closing_Stock":
            mb.showinfo("Information", "Available Soon!")
            self._close()
        elif list_value == "Reorder_Level":
            mb.showinfo("Information", "Available Soon!")
            self._close()
        elif list_value == "Incoming":
            mb.showinfo("Information", "Available Soon!")
            self._close()
        elif list_value == "Outgoing":
            mb.showinfo("Information", "Available Soon!")
            self._close()
        elif list_value == "Adjustment":
            mb.showinfo("Information", "Available Soon!")
            self._close()
        elif list_value == "Consumption":
            mb.showinfo("Information", "Available Soon!")
            self._close()
        else:
            return

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        try:
            if self.db.status:
                self.db.closeDB()
        finally:
            self.grab_release()
            self.destroy()
# End of ReportWindow class.

# Start of IncomingWindow class.
class IncomingWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        with open('config.json', 'r') as cf:
            data = json.load(cf)
        self.db = Database()
        db = data['default_db']
        self.db.openDB(db)
        self.setupUI()

    def setupUI(self):
        self.title("Incoming")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()

        in_img_open = Image.open('images/cart-12.png')
        self.in_img = ImageTk.PhotoImage(in_img_open.resize((36, 36)))

        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        in_label = tk.Label(mainframe, text="Incoming", fg="white",
                          font=("Tahoma", 12, "bold"), bg="orange",
                          image=self.in_img, compound="left")
        in_label.pack(fill="x", padx=15, pady=15)

        top_frame = ttk.Frame(mainframe)
        top_frame.pack(fill="x")
        middle_frame = ttk.Frame(mainframe)
        middle_frame.pack(fill="x")
        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(expand=True, fil="both")
        total_frame = ttk.Frame(mainframe)
        total_frame.pack(fill="x")

        transid_lbl = ttk.Label(top_frame, text="Transaction ID:")
        transid_lbl.grid(row=0, column=0)
        dnote_lbl = ttk.Label(top_frame, text="DN/INV No.:")
        dnote_lbl.grid(row=1, column=0)
        datefor_lbl = ttk.Label(top_frame, text="(DD-MM-YYYY)")
        datefor_lbl.grid(row=0, column=3)
        date_lbl = ttk.Label(top_frame, text="Date:")
        date_lbl.grid(row=1, column=2)
        supp_lbl = ttk.Label(top_frame, text="Supplier:")
        supp_lbl.grid(row=2, column=0)
        rem_lbl = ttk.Label(top_frame, text="Remarks:")
        rem_lbl.grid(row=3, column=0)

        self.transid_entry = tk.Entry(top_frame, width=12)
        self.transid_entry.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.transid_entry.config(state="disable")
        
        self.dnote_entry = tk.Entry(top_frame)
        self.dnote_entry.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        self.dnote_entry.focus_set()
        self.date_entry = tk.Entry(top_frame, width=12)
        self.date_entry.grid(row=1, column=3, padx=2, pady=2)
        self.date_entry.insert('end', time.strftime("%d-%m-%Y"))
        self.supp_entry = tk.Entry(top_frame, width=35)
        self.supp_entry.grid(row=2, column=1, sticky="w", padx=2, pady=2)
        self.rem_entry = tk.Entry(top_frame, width=60)
        self.rem_entry.grid(row=3, column=1, sticky="w", padx=2, pady=2)

        # Add 3 buttons for add, edit, and delete product/s.
        self.add_btn = ttk.Button(middle_frame, text="Add")
        self.add_btn.grid(row=0, column=0)
        self.add_btn.bind("<Button-1>", self.buttonHandler)
        self.edit_btn = ttk.Button(middle_frame, text="Edit")
        self.edit_btn.grid(row=0, column=1)
        self.edit_btn.bind("<Button-1>", self.buttonHandler)
        self.del_btn = ttk.Button(middle_frame, text="Delete")
        self.del_btn.grid(row=0, column=2)
        self.del_btn.bind("<Button-1>", self.buttonHandler)

        # Add the product view and 3 buttons for print, save
        # and close. After transaction has been save the
        # save button will be disabled to avoid saving the
        # transaction twice.
        left_frame = ttk.Frame(bottom_frame)
        left_frame.pack(side="left", expand=True, fill="both")
        right_frame = ttk.Frame(bottom_frame)
        right_frame.pack(fill="y")

        self.product_view = ttk.Treeview(left_frame)
        self.product_view.pack(expand=True, fill="both", side="left")
        self.scroll = ttk.Scrollbar(left_frame, orient="vertical")
        self.scroll.pack(side="right", fill="y")
        self.product_view.config(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.product_view.yview)

        column = ("itemcode", "description", "unit", "quantity", "price", "amount")
        self.product_view['columns'] = column
        self.product_view['show'] = 'headings'
        
        for col in column:
            self.product_view.heading(col, text=col.title())

        self.product_view.column(column[0], width=60)
        self.product_view.column(column[1], width=175)
        self.product_view.column(column[2], width=20)
        self.product_view.column(column[3], width=50)
        self.product_view.column(column[4], width=50)
        self.product_view.column(column[5], width=50)

        self.save_btn = ttk.Button(right_frame, text="Save")
        self.save_btn.pack(anchor="n")
        self.save_btn.bind("<Button-1>", self.buttonHandler)
        self.print_btn = ttk.Button(right_frame, text="Print")
        self.print_btn.pack(anchor="n")
        self.print_btn.bind("<Button-1>", self.buttonHandler)
        self.close_btn = ttk.Button(right_frame, text="Close")
        self.close_btn.pack(anchor="s")
        self.close_btn.bind("<Button-1>", self.buttonHandler)

        self.total_var = tk.StringVar()
        self.total_var.set('Total: %s' % format(0.0, '0.2f'))
        self.total_value_lbl = tk.Label(total_frame,
                                        textvariable=self.total_var,
                                        anchor='w',
                                        bg="orange",
                                        font=("Tahoma", 10, "bold"),
                                        fg="blue", relief="groove",
                                        padx=5, pady=5
                                        )
        self.total_value_lbl.pack(fill="x")

    def buttonHandler(self, event):
        command = event.widget.cget('text')
        if command == "Add":
            add = AddItemWindow(self)
            self.wait_window(add)
            if add.product_id is None:
                return
            self.product_view.insert('', 'end', add.product_id, text=add.product_id)
            self.product_view.set(add.product_id, 'itemcode', add.product_select[1])
            self.product_view.set(add.product_id, 'description', add.product_select[2])
            self.product_view.set(add.product_id, 'unit', add.product_select[3])
            self.product_view.set(add.product_id, 'quantity', add.quantity)
            self.product_view.set(add.product_id, 'price', add.price)
            self.product_view.set(add.product_id, 'amount', add.amount)
            self.updateTotal()
        elif command == "Edit":
            if self.product_view.focus() == '':
                return
            edit = EditItemWindow(self)
            self.wait_window(edit)
            self.product_view.delete(edit.product_id)
            self.product_view.insert('', 'end', edit.product_id, text=edit.product_id)
            self.product_view.set(edit.product_id, 'itemcode', edit.product_select[1])
            self.product_view.set(edit.product_id, 'description', edit.product_select[2])
            self.product_view.set(edit.product_id, 'unit', edit.product_select[3])
            self.product_view.set(edit.product_id, 'quantity', edit.quantity)
            self.product_view.set(edit.product_id, 'price', edit.price)
            self.product_view.set(edit.product_id, 'amount', edit.amount)
            self.updateTotal()
        elif command == "Delete":
            item_focus = self.product_view.focus()
            answer = mb.askokcancel("information", "Delete this item?")
            if answer:
                self.product_view.delete(item_focus)
                self.updateTotal()
        elif command == "Save":
            # Check first if items were available for saving else pop up warning.
            children = self.product_view.get_children()
            if len(children) == 0:
                mb.showwarning("Warning", "Add at least one item in the table.")
                return
            try:
                # Insert details in incoming table.
                date = self.date_entry.get()
                dn_number = self.dnote_entry.get()
                supplier = self.supp_entry.get()
                remarks = self.rem_entry.get()
                receipt = {'table': 'incoming', 'date': date, 'dn_number': dn_number,
                           'supplier': supplier, 'remarks': remarks
                           }
                self.db.insertRecord(**receipt)
                # Insert details into in_transaction table.
                self.transid_entry.config(state="normal")
                record_id = self.checkRecordID()
                record_id = record_id[0]
                self.transid_entry.insert('end', record_id)
                main_list = []
                sub_list = ()
                record_id = int(record_id)
                for child in children:
                    pro_id = int(child)
                    quantity = float(self.product_view.item(child)['values'][3])
                    price = float(self.product_view.item(child)['values'][4])
                    sub_list += (record_id, pro_id, quantity, price)
                    main_list.append(sub_list)
                    sub_list = ()

                receipt_items = {'table': 'in_transaction',
                                'itemlist': main_list}
                self.db.insertRecord(**receipt_items)
            finally:
                event.widget.config(state="disable")
        elif command == "Print":
            children = self.product_view.get_children()
            date = self.date_entry.get()
            dn_number = self.dnote_entry.get()
            supplier = self.supp_entry.get()
            remarks = self.rem_entry.get()
            self.transid_entry.config(state="normal")
            transid = self.transid_entry.get()
            self.transid_entry.config(state="disable")

            item_list = []
            counter = 1
            amount = 0
            for child in children:
                serial = counter
                itemcode = self.product_view.item(child)['values'][0]
                if isinstance(itemcode, int):
                    itemcode = format(itemcode, '0>10')
                desc = self.product_view.item(child)['values'][1]
                unit = self.product_view.item(child)['values'][2]
                quantity = float(self.product_view.item(child)['values'][3])
                price = float(self.product_view.item(child)['values'][4])
                value = float(self.product_view.item(child)['values'][5])
                amount += float(value)
                item_list.append((str(serial), itemcode, desc, unit,
                                  quantity, price, value))
                counter += 1
            options = {'mode': "incoming",
                       'transid': transid,
                       'date': date,
                       'dn_number': dn_number,
                       'supplier': supplier}
            pdf = PDF(**options)
            pdf.alias_nb_pages()
            pdf.add_page()
            # The rest of the report will be inserted here.
            pdf.set_font('Courier', '', 10)
            for item in item_list:
                pdf.cell(15, 10, item[0])
                pdf.cell(30, 10, item[1])
                pdf.cell(60, 10, item[2][0:25])
                pdf.cell(15, 10, item[3], 0, 0, 'C')
                pdf.cell(20, 10, format(item[4], '0.2f'))
                pdf.cell(20, 10, format(item[5], '0.2f'))
                pdf.cell(30, 10, format(item[6], '0,.2f'))
                pdf.ln(5)
            pdf.ln(25)
            pdf.set_font('Courier', 'B', 10)
            pdf.cell(105, 7, "Remarks: "+remarks)
            pdf.cell(15, 7, "")
            pdf.cell(40, 7, "Total Amount:", 0, 0, 'C')
            pdf.cell(30, 7, format(amount, '0,.2f'), 1, 0, 'C')
            pdf.output('reports/incoming.pdf', 'F')

            try:
                os.system('start '+'reports/incoming.pdf')
            except:
                print("Error Printing")
        elif command == "Close":
            self._close()

    def checkRecordID(self):
        query = self.db.cur.execute("""SELECT id FROM incoming""")
        data = query.fetchall()
        if len(data) == 0:
            return str(1)
        else:
            return str(data[-1][0])

    def updateTotal(self):
        amount = 0
        children = self.product_view.get_children()
        if len(children) != 0:
            for child in children:
                amount += float(self.product_view.item(child)['values'][5])
        amount = "Total: %s" % format(amount, '0.2f')
        self.total_var.set(amount)

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        try:
            if self.db.status:
                self.db.closeDB()
        finally:
            self.grab_release()
            self.destroy()
# End of IncomingWindow class.

# Start of AddItemWindow class.
class AddItemWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.product_id = None
        self.price = None
        self.quantity = None
        self.amount = None
        self.product_select = None
        self.setupUI()

    def setupUI(self):
        self.title("Add")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        mainframe = ttk.Frame(self, padding="0.2i")
        mainframe.pack(expand=True, fill="both")

        ttk.Label(mainframe, text="Itemcode:").grid(row=0, column=0, sticky="e")
        ttk.Label(mainframe, text="Quantity:").grid(row=1, column=0, sticky="e")
        ttk.Label(mainframe, text="Price:").grid(row=2, column=0, sticky="e")

        self.pro_entry = tk.Entry(mainframe, validate="focusout",
                                  validatecommand=self.loadPrice)
        self.pro_entry.grid(row=0, column=1, sticky='w', padx=2, pady=2)
        self.pro_entry.focus_set()
        
        self.quantity_entry = tk.Entry(mainframe, width=5)
        self.quantity_entry.grid(row=1, column=1, sticky='w', padx=2, pady=2)
        self.price_entry = tk.Entry(mainframe, width=7)
        self.price_entry.grid(row=2, column=1, sticky='w', padx=2, pady=2)

        btn_frame = ttk.Frame(mainframe)
        btn_frame.grid(row=3, column=0, columnspan=2,
                       sticky="we", padx=5, pady=5)

        self.add_btn = ttk.Button(btn_frame, text="Add")
        self.add_btn.grid(row=3, column=1, padx=2, pady=2)
        self.add_btn.bind("<Button-1>", self.buttonHandler)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel")
        self.cancel_btn.grid(row=3, column=0, padx=2, pady=2)
        self.cancel_btn.bind("<Button-1>", self.buttonHandler)

    def buttonHandler(self, event):
        command = event.widget.cget('text')
        if command == "Add":
            product = self.pro_entry.get()
            quantity = self.quantity_entry.get()
            price = self.price_entry.get()
            if product == '':
                mb.showwarning("Invalid", "Invalid item code.")
            elif quantity == '':
                mb.showwarning("Invalid", "Invalid quantity.")
            elif price == '':
                mb.showwarning("Invalid", "Invalid price.")
            else:
                query = self.master.db.cur.execute(
                    """SELECT * FROM products WHERE code=?""", (product,))
                data = query.fetchone()
                self.product_select = data
                self.product_id = str(data[0])
                self.price = str(price)
                self.quantity = str(quantity)
                self.amount = str(float(price) * float(quantity))
                self._close()
        elif command == "Cancel":
            self._close()

    def loadPrice(self):
        code = self.pro_entry.get()
        query = self.master.db.cur.execute(
            """SELECT price FROM products WHERE code=?""", (code,))
        data = query.fetchone()
        if len(data) != 0:
            self.price_entry.insert('end', format(data[0], '0.2f'))
        else:
            mb.showwarning("Invalid", "Invalid item code.\nPlease try again.")

    def _closeEvent(self):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()
# End of AddItemWindow class.

# Start of EditItemWindow class.
class EditItemWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.product_id = self.master.product_view.focus()
        self.price = self.master.product_view.item(self.product_id)['values'][4]
        self.quantity = self.master.product_view.item(self.product_id)['values'][3]
        self.amount = self.master.product_view.item(self.product_id)['values'][5]
        self.pro_code = self.master.product_view.item(self.product_id)['values'][0]
        self.product_select = None
        self.setupUI()

    def setupUI(self):
        self.title("Edit")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        mainframe = ttk.Frame(self, padding="0.2i")
        mainframe.pack(expand=True, fill="both")

        ttk.Label(mainframe, text="Itemcode:").grid(row=0, column=0, sticky="e")
        ttk.Label(mainframe, text="Quantity:").grid(row=1, column=0, sticky="e")
        ttk.Label(mainframe, text="Price:").grid(row=2, column=0, sticky="e")

        self.pro_entry = tk.Entry(mainframe)
        self.pro_entry.grid(row=0, column=1, sticky='w', padx=2, pady=2)
        self.pro_entry.insert('end', self.pro_code)
        self.pro_entry.focus_set()
        self.quantity_entry = tk.Entry(mainframe, width=5)
        self.quantity_entry.grid(row=1, column=1, sticky='w', padx=2, pady=2)
        self.quantity_entry.insert('end', self.quantity)
        self.price_entry = tk.Entry(mainframe, width=7)
        self.price_entry.grid(row=2, column=1, sticky='w', padx=2, pady=2)
        self.price_entry.insert('end', self.price)

        btn_frame = ttk.Frame(mainframe)
        btn_frame.grid(row=3, column=0, columnspan=2,
                       sticky="we", padx=5, pady=5)

        self.save_btn = ttk.Button(btn_frame, text="Save")
        self.save_btn.grid(row=3, column=1, padx=2, pady=2)
        self.save_btn.bind("<Button-1>", self.buttonHandler)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel")
        self.cancel_btn.grid(row=3, column=0, padx=2, pady=2)
        self.cancel_btn.bind("<Button-1>", self.buttonHandler)

    def buttonHandler(self, event):
        command = event.widget.cget('text')
        if command == "Save":
            product = self.pro_entry.get()
            quantity = self.quantity_entry.get()
            price = self.price_entry.get()
            if product == '':
                mb.showwarning("Invalid", "Invalid item code.")
            elif quantity == '':
                mb.showwarning("Invalid", "Invalid quantity.")
            elif price == '':
                mb.showwarning("Invalid", "Invalid price.")
            else:
                query = self.master.db.cur.execute(
                    """SELECT * FROM products WHERE code=?""", (product,))
                data = query.fetchone()
                print(data)
                print(data[1])
                print(type(data))
                self.product_select = data
                self.product_id = str(data[0])
                self.price = str(price)
                self.quantity = str(quantity)
                self.amount = str(float(price) * float(quantity))
                self._close()
        elif command == "Cancel":
            self._close()

    def _closeEvent(self):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()
# End of EditItemWindow class.

class ProductWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.title("Products")
        self.geometry("800x480+100+100")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        self.search_status = False
        self.usertype = self.master.login.usertype
        self.style = ttk.Style()
        self.style.configure(".", background="orange")
        with open('config.json', 'r') as cf:
            data = json.load(cf)
        self.db = Database()
        db = data['default_db']
        self.db.openDB(db)
        self.setupUI()

    def setupUI(self):
        pro_img_open = Image.open('images/barcode.png')
        self.pro_img = ImageTk.PhotoImage(pro_img_open.resize((36, 36)))
        
        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")
        pro_label = tk.Label(mainframe, text="Products", fg="white",
                             font=("Tahoma", 12, "bold"), bg="orange",
                             image=self.pro_img, compound="left")
        pro_label.pack(fill="x", padx=15, pady=15)
        top_frame = ttk.Frame(mainframe)
        top_frame.pack(fill="x")
        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(expand=True, fill="both")
        left_frame = tk.Frame(bottom_frame, bg="orange")
        left_frame.pack(side="left", expand=True, fill="both")
        right_frame = tk.Frame(bottom_frame, bg="orange")
        right_frame.pack(fill="y", padx=5, pady=5)

        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.grid(row=0, column=0, padx=3, pady=3)
        self.search_entry.focus_set()
        self.search_btn = ttk.Button(top_frame, text="Search",
                                     command=lambda: self.buttonHandler("SEARCH"))
        self.search_btn.grid(row=0, column=1)

        self.product_view = ttk.Treeview(left_frame)
        self.product_view.pack(expand=True, fill="both", side="left")
        self.scroll = ttk.Scrollbar(left_frame, orient="vertical")
        self.scroll.pack(side="right", fill="y")
        self.product_view.config(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.product_view.yview)

        column = ("itemcode", "description", "unit", "price", "max", "min")
        self.product_view['columns'] = column
        self.product_view.heading('#0', text="Item Id")
        for col in column:
            self.product_view.heading(col, text=col.title())

        self.product_view.column('#0', width=20)
        self.product_view.column(column[0], width=50)
        self.product_view.column(column[1], width=175)
        self.product_view.column(column[2], width=20)
        self.product_view.column(column[3], width=20)
        self.product_view.column(column[4], width=50)
        self.product_view.column(column[5], width=50)

        self.updateView()

        self.new_btn = ttk.Button(right_frame, text="New",
                                  command=lambda: self.buttonHandler("NEW"))
        self.new_btn.pack()
        self.edit_btn = ttk.Button(right_frame, text="Edit",
                                   command=lambda: self.buttonHandler("EDIT"))
        self.edit_btn.pack()
        self.del_btn = ttk.Button(right_frame, text="Delete",
                                  command=lambda: self.buttonHandler("DELETE"))
        self.del_btn.pack()
        self.expt_btn = ttk.Button(right_frame, text="Export",
                                   command=lambda: self.buttonHandler("EXPORT"))
        self.expt_btn.pack()
        self.close_btn = ttk.Button(right_frame, text="Close",
                                    command=lambda: self.buttonHandler("CLOSE"))
        self.close_btn.pack()
        if self.usertype != "ADMIN":
            self.del_btn.config(state="disable")
            self.edit_btn.config(state="disable")
            self.expt_btn.config(state="disable")
            self.new_btn.config(state="disable")

    def updateView(self):
        if len(self.product_view.get_children()) != 0:
            items = self.product_view.get_children()
            for item in items:
                self.product_view.delete(item)
        query = self.db.cur.execute("""SELECT * FROM products""")
        data = query.fetchall()
        if len(data) == 0:
            return
        for product in data:
            price = str(format(product[4], '.2f'))
            max_qty = str(format(product[5], '.2f'))
            min_qty = str(format(product[6], '.2f'))
            self.product_view.insert('', 'end', str(product[0]), text=str(product[0]))
            self.product_view.set(str(product[0]), 'itemcode', str(product[1]))
            self.product_view.set(str(product[0]), 'description', str(product[2]))
            self.product_view.set(str(product[0]), 'unit', str(product[3]))
            self.product_view.set(str(product[0]), 'price', price)
            self.product_view.set(str(product[0]), 'max', max_qty)
            self.product_view.set(str(product[0]), 'min', min_qty)

    def buttonHandler(self, data):
        if data == "NEW":
            NewProduct(self, bg="orange")
            
        elif data == "EDIT":
            if self.product_view.focus() != '':
                self.selectproduct = int(self.product_view.focus())
                EditProduct(self, bg="orange")
                
        elif data == "EXPORT":
            temp_list = []
            children = self.product_view.get_children()
            for child in children:
                item = self.product_view.item(child)['values']
                temp_list.append(item)
            
            with open('product_list.csv', 'w', newline='') as csvfile:
                for row in temp_list:
                    csvwriter = csv.writer(csvfile, delimiter=",")
                    csvwriter.writerow(row)

        elif data == "DELETE":
            mb.showinfo("Information", "Available Soon")
        
        elif data == "SEARCH":
            if self.search_status:
                self.updateView()
                self.search_status = False
            counter = 0
            search_item = self.search_entry.get().split("*")
            if search_item[0] == "ALL" or search_item[0] == "all" and len(search_item) == 1:
                self.updateView()
                self.search_entry.delete('0', 'end')
                self.search_entry.focus_set()
                return
            children = self.product_view.get_children()
            for child in children:
                items = self.product_view.item(child)['values']
                for search in search_item:
                    for item in items:
                        if search in item:
                            counter += 1
                if counter == 0:
                    self.product_view.delete(child)
                counter = 0
            if len(self.product_view.get_children()) == 0:
                mb.showinfo("Information", "No Results. Please try again.")
                self.updateView()
            self.search_status = True
            self.search_entry.select_range('0', 'end')
            self.search_entry.focus_set()
                        
        elif data == "CLOSE":
            self._close()

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        try:
            if self.db.status:
                self.db.closeDB()
        finally:
            self.grab_release()
            self.destroy()

class NewProduct(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.setupUI()

    def setupUI(self):
        self.title("New Product")
        self.grab_set()
        self.lift()
        self.protocol("WM_DELETE_WINDOW", self._close)
        
        mainframe = tk.Frame(self, bg="orange")
        mainframe.pack(expand=True, fill="both", padx=15, pady=15)

        pro_code_lbl = tk.Label(mainframe, text="Item Code:",
                                bg="orange")
        pro_code_lbl.grid(row=0, column=0, sticky="e")
        pro_desc_lbl = tk.Label(mainframe, text="Description:",
                                bg="orange")
        pro_desc_lbl.grid(row=1, column=0, sticky="e")
        pro_unit_lbl = tk.Label(mainframe, text="Unit:",
                                bg="orange")
        pro_unit_lbl.grid(row=1, column=4, sticky="e")
        pro_price_lbl = tk.Label(mainframe, text="Price:",
                                 bg="orange")
        pro_price_lbl.grid(row=2, column=0, sticky="e")
        pro_max_lbl = tk.Label(mainframe, text="Max:",
                               bg="orange")
        pro_max_lbl.grid(row=2, column=2, sticky="e")
        pro_min_lbl = tk.Label(mainframe, text="Min:",
                               bg="orange")
        pro_min_lbl.grid(row=2, column=4, sticky="e")

        self.code_entry = tk.Entry(mainframe)
        self.code_entry.grid(row=0, column=1)
        query = self.master.db.cur.execute("SELECT rowid FROM products")
        data = query.fetchall()
        if len(data) == 0:
            self.code_entry.insert('end', format(1, '0>10'))
        else:
            self.code_entry.insert('end', format(data[-1][0]+1, '0>10'))
        self.desc_entry = tk.Entry(mainframe)
        self.desc_entry.grid(row=1, column=1, columnspan=3, sticky="we")
        self.desc_entry.focus_set()
        self.unit_entry = tk.Entry(mainframe, width=6)
        self.unit_entry.grid(row=1, column=5)
        self.price_entry = tk.Entry(mainframe)
        self.price_entry.grid(row=2, column=1)
        self.max_entry = tk.Entry(mainframe, width=6)
        self.max_entry.grid(row=2, column=3, sticky="we")
        self.min_entry = tk.Entry(mainframe, width=6)
        self.min_entry.grid(row=2, column=5)

        self.cancel_btn = ttk.Button(mainframe, text="Cancel",
                                     command=self._close)
        self.cancel_btn.grid(row=3, column=2, columnspan=2,
                             padx=5, pady=5)
        self.save_btn = ttk.Button(mainframe, text="Save",
                                   command=self.saveRecord)
        self.save_btn.grid(row=3, column=4, columnspan=2,
                           padx=5, pady=5)

    def saveRecord(self):
        itemcode = self.code_entry.get()
        description = self.desc_entry.get()
        unit = self.unit_entry.get()
        price = self.price_entry.get()
        max_qty = self.max_entry.get()
        min_qty = self.min_entry.get()
        
        if itemcode != '' and description != '':
            self.master.db.insertRecord(table="products", itemcode=itemcode,
                                        description=description, unit=unit,
                                        price=price, max_qty=max_qty,
                                        min_qty=min_qty)
            self.master.updateView()
            self._close()
        
    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()

class EditProduct(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.productid = self.master.selectproduct
        self.setupUI()

    def setupUI(self):
        self.title("Edit Product")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)
        
        mainframe = tk.Frame(self, bg="orange")
        mainframe.pack(expand=True, fill="both", padx=15, pady=15)

        pro_code_lbl = tk.Label(mainframe, text="Item Code:",
                                bg="orange")
        pro_code_lbl.grid(row=0, column=0, sticky="e")
        pro_desc_lbl = tk.Label(mainframe, text="Description:",
                                bg="orange")
        pro_desc_lbl.grid(row=1, column=0, sticky="e")
        pro_unit_lbl = tk.Label(mainframe, text="Unit:",
                                bg="orange")
        pro_unit_lbl.grid(row=1, column=4, sticky="e")
        pro_price_lbl = tk.Label(mainframe, text="Price:",
                                 bg="orange")
        pro_price_lbl.grid(row=2, column=0, sticky="e")
        pro_max_lbl = tk.Label(mainframe, text="Max:",
                               bg="orange")
        pro_max_lbl.grid(row=2, column=2, sticky="e")
        pro_min_lbl = tk.Label(mainframe, text="Min:",
                               bg="orange")
        pro_min_lbl.grid(row=2, column=4, sticky="e")

        self.code_entry = tk.Entry(mainframe)
        self.code_entry.grid(row=0, column=1)
        self.desc_entry = tk.Entry(mainframe)
        self.desc_entry.grid(row=1, column=1, columnspan=3, sticky="we")
        self.desc_entry.focus_set()
        self.unit_entry = tk.Entry(mainframe, width=6)
        self.unit_entry.grid(row=1, column=5)
        self.price_entry = tk.Entry(mainframe)
        self.price_entry.grid(row=2, column=1)
        self.max_entry = tk.Entry(mainframe, width=6)
        self.max_entry.grid(row=2, column=3, sticky="we")
        self.min_entry = tk.Entry(mainframe, width=6)
        self.min_entry.grid(row=2, column=5)
        self.loadProduct()

        self.cancel_btn = ttk.Button(mainframe, text="Cancel",
                                     command=self._close)
        self.cancel_btn.grid(row=3, column=2, columnspan=2,
                             padx=5, pady=5)
        self.save_btn = ttk.Button(mainframe, text="Update",
                                   command=self.updateProduct)
        self.save_btn.grid(row=3, column=4, columnspan=2,
                           padx=5, pady=5)

    def loadProduct(self):
        query = self.master.db.cur.execute("SELECT * FROM products WHERE id=?", (self.productid,))
        data = query.fetchone()
        itemcode = str(data[1])
        description = str(data[2])
        unit = str(data[3])
        price = str(data[4])
        max_qty = str(data[5])
        min_qty = str(data[6])
        self.code_entry.insert('end', itemcode)
        self.desc_entry.insert('end', description)
        self.unit_entry.insert('end', unit)
        self.price_entry.insert('end', price)
        self.max_entry.insert('end', max_qty)
        self.min_entry.insert('end', min_qty)

    def updateProduct(self):
        productid = self.productid
        description = self.desc_entry.get()
        price = self.price_entry.get()
        max_qty = self.max_entry.get()
        min_qty = self.min_entry.get()
        self.master.db.updateRecord(table="products", productid=productid,
                                    description=description, price=price,
                                    max_qty=max_qty, min_qty=min_qty)
        self.master.updateView()
        self._close()

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()

class LoginWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.usertype = None
        self.username = None
        self.counter = 0
        self.status = False
        self.setupUI()
        self.title("Login")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.master.withdraw()
        self.grab_set()
        self._setPositionCtr()

    def setupUI(self):
        self.style = ttk.Style()
        self.style.configure(".", background="orange")

        login_img_open = Image.open("images/businessman.png")
        self.login_img = ImageTk.PhotoImage(login_img_open.resize((48, 48)))
        
        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        top_frame = ttk.Frame(mainframe, padding="0.3i")
        top_frame.pack()
        bottom_frame = ttk.Frame(mainframe, padding=3)
        bottom_frame.pack(fill="x")

        login_lbl = ttk.Label(top_frame, image=self.login_img)
        login_lbl.grid(row=0, column=0, columnspan=2)
        user_lbl = ttk.Label(top_frame, text="Username:")
        user_lbl.grid(row=1, column=0)
        pass_lbl = ttk.Label(top_frame, text="Password:")
        pass_lbl.grid(row=2, column=0)

        self.user_entry = ttk.Entry(top_frame)
        self.user_entry.grid(row=1, column=1, padx=2, pady=2)
        self.pass_entry = ttk.Entry(top_frame, show="*")
        self.pass_entry.grid(row=2, column=1, padx=2, pady=2)
        self.pass_entry.bind("<Return>", self.doLoginEvent)

        self.login_btn = ttk.Button(bottom_frame, text="Login")
        self.login_btn.config(command=self.doLogin)
        self.login_btn.pack(side="right")
        self.login_btn.bind("<Return>", self.doLoginEvent)
        self.cancel_btn = ttk.Button(bottom_frame, text="Cancel")
        self.cancel_btn.config(command=self._close)
        self.cancel_btn.pack(side="right")

        self.user_entry.focus_set()

    def doLoginEvent(self, event):
        self.doLogin()

    def doLogin(self):
        with open("config.json", "r") as cf:
            data = json.load(cf)
        self.db = Database()
        db = data['default_db']
        self.db.openDB(db)
        self.counter += 1
        username = self.user_entry.get()
        password = self.pass_entry.get() + self.db.salt
        password = hashlib.sha224(password.encode("utf-8")).hexdigest()
        
        query = self.db.con.execute(
            """SELECT * FROM users WHERE username=?""", (username,)
            )
        data = query.fetchone()
        self.db.closeDB()
        if data == None:
            if self.counter == 3:
                message = "Maximum login attempts has been reach.\n Please contact your system administrator."
                mb.showerror("Failed!", message)
                self._close()
                self.master.destroy()
            else:
                self.pass_entry.delete(0, 'end')
                mb.showwarning("Invalid", "Invalid username or password.")
                self.user_entry.focus_set()

        elif data[1] == username and data[2] == password:
            self.status = True
            message = " ".join(["You have successfully login.\n",
                                "Welcome back", username.upper(), "."])
            mb.showinfo("Success", message)
            self.username = username
            self.usertype = str(data[3])
            self.master.focus_set()
            self._close()

        else:
            if self.counter == 3:
                message = "Maximum login attempts has been reach.\n Please contact your system administrator."
                mb.showerror("Failed!", message)
                self._close()
            else:
                self.pass_entry.delete(0, 'end')
                mb.showwarning("Invalid", "Invalid username or password.")
                self.user_entry.focus_set()

    def _setPositionCtr(self):
        self.update_idletasks()
        scr_x = self.winfo_screenwidth()
        scr_y = self.winfo_screenheight()
        x = self.winfo_width()
        y = self.winfo_height()
        pos = "+" + str(int(((scr_x-x)/2))) + "+" + str(int(((scr_y-y)/2)))
        self.geometry(pos)

    def _close(self):
        if not self.status:
            self.grab_release()
            self.destroy()
            self.master.iconify()
            self.master.deiconify()
            self.master.destroy()
        else:
            self.grab_release()
            self.master.iconify()
            self.master.deiconify()
            self.destroy()

class UsersWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        try:
            with open('config.json', 'r') as cf:
                data = json.load(cf)
                
            self.db = Database()
            db = data['default_db']
            self.db.openDB(db)
        except:
            print(sys.exc_info()[1])
        self.setupUI()

    def setupUI(self):
        self.title("User Management")
        self.geometry("480x320+100+100")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        self.style = ttk.Style()
        self.style.configure(".", background="orange")

        mainframe = tk.Frame(self, bg="orange")
        mainframe.pack(expand=True, fill="both")
        user_label = tk.Label(mainframe, text="User Management",
                             font=("Tahoma", 12, "bold"),
                             bg="orange")
        user_label.pack(fill="x", padx=15, pady=15)
        top_frame = tk.Frame(mainframe, bg="orange")
        top_frame.pack(fill="x")
        bottom_frame = tk.Frame(mainframe, bg="orange")
        bottom_frame.pack(expand=True, fill="both")
        left_frame = tk.Frame(bottom_frame, bg="orange")
        left_frame.pack(side="left", expand=True, fill="both")
        right_frame = tk.Frame(bottom_frame, bg="orange")
        right_frame.pack(fill="y", padx=5, pady=5)

        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.grid(row=0, column=0, padx=3, pady=3)
        self.search_entry.focus_set()
        self.search_btn = ttk.Button(top_frame, text="Search",
                                     command=lambda: self.buttonHandler("SEARCH"))
        self.search_btn.grid(row=0, column=1)

        self.users_view = ttk.Treeview(left_frame)
        self.scroll = ttk.Scrollbar(left_frame)
        self.users_view.pack(side="left", expand=True, fill="both")
        self.scroll.pack(side="right", fill="y")
        self.users_view.config(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.users_view.yview)

        self.users_view['columns'] = ("username", "password", "usertype")
        self.users_view.heading('#0', text="User ID")
        self.users_view.heading('username', text="Username")
        self.users_view.heading('password', text="Password")
        self.users_view.heading('usertype', text="Type")
        self.users_view.column('#0', width=50)
        self.users_view.column('username', width=75)
        self.users_view.column('password', width=80)
        self.users_view.column('usertype', width=30)
        self.updateView()

        self.new_btn = ttk.Button(right_frame, text="New",
                                  command=lambda: self.buttonHandler("NEW"))
        self.new_btn.pack()
        self.edit_btn = ttk.Button(right_frame, text="Edit",
                                   command=lambda: self.buttonHandler("EDIT"))
        self.edit_btn.pack()
        self.del_btn = ttk.Button(right_frame, text="Delete",
                                  command=lambda: self.buttonHandler("DELETE"))
        self.del_btn.pack()
        self.close_btn = ttk.Button(right_frame, text="Close",
                                    command=lambda: self.buttonHandler("CLOSE"))
        self.close_btn.pack()

    def buttonHandler(self, data):
        if data == "NEW":
            NewUser(self, bg="orange")
        elif data == "EDIT":
            if self.users_view.focus() != '':
                self.selectuser = int(self.users_view.focus())
                EditUser(self, bg="orange")
            else:
                return
        elif data == "DELETE":
            if self.users_view.focus() != '':
                self.selectuser = int(self.users_view.focus())
                self.db.deleteRecord(table="users", userid=self.selectuser)
                self.updateView()
        elif data == "SEARCH":
            mb.showinfo("Information", "Available Soon")
        elif data == "CLOSE":
            self._close()

    def updateView(self):
        if len(self.users_view.get_children()) != 0:
            items = self.users_view.get_children()
            for item in items:
                self.users_view.delete(item)
        query = self.db.cur.execute("""SELECT * FROM users""")
        data = query.fetchall()
        for user in data:
            self.users_view.insert('', 'end', str(user[0]), text=str(user[0]))
            self.users_view.set(str(user[0]), 'username', str(user[1]))
            self.users_view.set(str(user[0]), 'password', str(user[2]))
            self.users_view.set(str(user[0]), 'usertype', str(user[3]))

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        try:
            if self.db.status:
                self.db.closeDB()
        finally:
            self.grab_release()
            self.destroy()

class NewUser(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.setupUI()

    def setupUI(self):
        self.title("New User")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        top_frame = ttk.Frame(mainframe, padding="0.5i")
        top_frame.pack(expand=True, fill="both")
        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(fill="x")

        user_lbl = ttk.Label(top_frame, text="Username:")
        user_lbl.grid(row=0, column=0)
        pass_lbl = ttk.Label(top_frame, text="Password:")
        pass_lbl.grid(row=1, column=0)
        type_lbl = ttk.Label(top_frame, text="Type:")
        type_lbl.grid(row=2, column=0)

        self.user_entry = ttk.Entry(top_frame)
        self.user_entry.grid(row=0, column=1, padx=2, pady=2)
        self.user_entry.focus_set()
        self.pass_entry = ttk.Entry(top_frame)
        self.pass_entry.grid(row=1, column=1, padx=2, pady=2)
        self.usertype_entry = ttk.Entry(top_frame)
        self.usertype_entry.grid(row=2, column=1, padx=2, pady=2)

        self.cancel_btn = ttk.Button(bottom_frame, text="Cancel")
        self.cancel_btn.pack(side="right")
        self.cancel_btn.config(command=self._close)
        self.save_btn = ttk.Button(bottom_frame, text="Save")
        self.save_btn.pack(side="right")
        self.save_btn.config(command=self.saveUser)

    def saveUser(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        usertype = self.usertype_entry.get()
        if len(username) != 0 and len(password) != 0:
            self.master.db.insertRecord(table="users",
                                        user=username,
                                        password=password,
                                        usertype=usertype)
            self.master.updateView()
            self._close()

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()

class EditUser(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.userid = self.master.selectuser
        self.setupUI()

    def setupUI(self):
        self.title("Edit User")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        top_frame = ttk.Frame(mainframe, padding="0.5i")
        top_frame.pack(expand=True, fill="both")
        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(fill="x")

        user_lbl = ttk.Label(top_frame, text="Username:")
        user_lbl.grid(row=0, column=0)
        pass_lbl = ttk.Label(top_frame, text="Password:")
        pass_lbl.grid(row=1, column=0)
        type_lbl = ttk.Label(top_frame, text="Type:")
        type_lbl.grid(row=2, column=0)

        self.user_entry = ttk.Entry(top_frame)
        self.user_entry.grid(row=0, column=1, padx=2, pady=2)
        self.user_entry.focus_set()
        self.pass_entry = ttk.Entry(top_frame)
        self.pass_entry.grid(row=1, column=1, padx=2, pady=2)
        self.usertype_entry = ttk.Entry(top_frame)
        self.usertype_entry.grid(row=2, column=1, padx=2, pady=2)
        self.loadUser()

        self.cancel_btn = ttk.Button(bottom_frame, text="Cancel")
        self.cancel_btn.pack(side="right")
        self.cancel_btn.config(command=self._close)
        self.save_btn = ttk.Button(bottom_frame, text="Save")
        self.save_btn.pack(side="right")
        self.save_btn.config(command=self.updateUser)

    def loadUser(self):
        query = self.master.db.cur.execute(
            """SELECT * FROM users WHERE id=?""", (self.userid,))
        data = query.fetchone()
        self.user_entry.insert('end', str(data[1]))
        self.usertype_entry.insert('end', str(data[3]))
        self.pass_entry.focus_set()

    def updateUser(self):
        password = self.pass_entry.get()
        usertype = self.usertype_entry.get()
        if len(password) != 0:
            try:
                self.master.db.updateRecord(table="users",
                                            userid=self.userid,
                                            password=password,
                                            usertype=usertype)
                self.master.updateView()
                self._close()
            except:
                mb.showerror("Error", sys.exc_info())

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()

class OutgoingWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        with open('config.json', 'r') as cf:
            data = json.load(cf)
        self.db = Database()
        db = data['default_db']
        self.db.openDB(db)
        self.setupUI()

    def setupUI(self):
        self.title("Outgoing")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()

        out_img_open = Image.open('images/cashier-1.png')
        self.out_img = ImageTk.PhotoImage(out_img_open.resize((36, 36)))

        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        in_label = tk.Label(mainframe, text="Outgoing", fg="white",
                          font=("Tahoma", 12, "bold"), bg="orange",
                          image=self.out_img, compound="left")
        in_label.pack(fill="x", padx=15, pady=15)

        top_frame = ttk.Frame(mainframe)
        top_frame.pack(fill="x")
        middle_frame = ttk.Frame(mainframe)
        middle_frame.pack(fill="x")
        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(expand=True, fil="both")
        total_frame = ttk.Frame(mainframe)
        total_frame.pack(fill="x")

        transid_lbl = ttk.Label(top_frame, text="Transaction ID:")
        transid_lbl.grid(row=0, column=0)
        datefor_lbl = ttk.Label(top_frame, text="(DD-MM-YYYY)")
        datefor_lbl.grid(row=0, column=3)
        date_lbl = ttk.Label(top_frame, text="Date:")
        date_lbl.grid(row=1, column=2)
        costctr_lbl = ttk.Label(top_frame, text="Cost Center:")
        costctr_lbl.grid(row=1, column=0)
        rem_lbl = ttk.Label(top_frame, text="Remarks:")
        rem_lbl.grid(row=2, column=0)

        self.transid_entry = tk.Entry(top_frame, width=12)
        self.transid_entry.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.transid_entry.config(state="disable")
        
        self.date_entry = tk.Entry(top_frame, width=12)
        self.date_entry.grid(row=1, column=3, padx=2, pady=2)
        self.date_entry.insert('end', time.strftime("%d-%m-%Y"))
        query = self.db.cur.execute("""SELECT code from costcenters""")
        combo_values = []
        data = query.fetchall()
        for code in data:
            combo_values.append(code[0])
        self.costctr_entry = ttk.Combobox(top_frame, values=combo_values)
        self.costctr_entry.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        self.rem_entry = tk.Entry(top_frame, width=60)
        self.rem_entry.grid(row=2, column=1, sticky="w", padx=2, pady=2)

        # Add 3 buttons for add, edit, and delete product/s.
        self.add_btn = ttk.Button(middle_frame, text="Add")
        self.add_btn.grid(row=0, column=0)
        self.add_btn.bind("<Button-1>", self.buttonHandler)
        self.edit_btn = ttk.Button(middle_frame, text="Edit")
        self.edit_btn.grid(row=0, column=1)
        self.edit_btn.bind("<Button-1>", self.buttonHandler)
        self.del_btn = ttk.Button(middle_frame, text="Delete")
        self.del_btn.grid(row=0, column=2)
        self.del_btn.bind("<Button-1>", self.buttonHandler)

        # Add the product view and 3 buttons for print, save
        # and close transaction. After transaction has been save
        # save button will be disabled to avoid saving the transaction
        # twice.
        left_frame = ttk.Frame(bottom_frame)
        left_frame.pack(side="left", expand=True, fill="both")
        right_frame = ttk.Frame(bottom_frame)
        right_frame.pack(fill="y")

        self.product_view = ttk.Treeview(left_frame)
        self.product_view.pack(expand=True, fill="both", side="left")
        self.scroll = ttk.Scrollbar(left_frame, orient="vertical")
        self.scroll.pack(side="right", fill="y")
        self.product_view.config(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.product_view.yview)

        column = ("itemcode", "description", "unit", "quantity", "price", "amount")
        self.product_view['columns'] = column
        self.product_view['show'] = 'headings'
        
        for col in column:
            self.product_view.heading(col, text=col.title())
            self.product_view.column(col, width=60)

        self.save_btn = ttk.Button(right_frame, text="Save")
        self.save_btn.pack(anchor="n")
        self.save_btn.bind("<Button-1>", self.buttonHandler)
        self.print_btn = ttk.Button(right_frame, text="Print")
        self.print_btn.pack(anchor="n")
        self.print_btn.bind("<Button-1>", self.buttonHandler)
        self.close_btn = ttk.Button(right_frame, text="Close")
        self.close_btn.pack(anchor="s")
        self.close_btn.bind("<Button-1>", self.buttonHandler)

        self.total_var = tk.StringVar()
        self.total_var.set('Total: %s' % format(0.0, '0.2f'))
        self.total_value_lbl = tk.Label(total_frame,
                                        textvariable=self.total_var,
                                        anchor='w',
                                        bg="orange",
                                        font=("Tahoma", 10, "bold"),
                                        fg="blue", relief="groove",
                                        padx=5, pady=5
                                        )
        self.total_value_lbl.pack(fill="x")

    def buttonHandler(self, event):
        command = event.widget.cget('text')
        if command == "Add":
            add = AddItemWindow(self)
            self.wait_window(add)
            if add.product_id is None:
                return
            self.product_view.insert('', 'end', add.product_id, text=add.product_id)
            self.product_view.set(add.product_id, 'itemcode', add.product_select[1])
            self.product_view.set(add.product_id, 'description', add.product_select[2])
            self.product_view.set(add.product_id, 'unit', add.product_select[3])
            self.product_view.set(add.product_id, 'quantity', add.quantity)
            self.product_view.set(add.product_id, 'price', add.price)
            self.product_view.set(add.product_id, 'amount', add.amount)
            self.updateTotal()
        elif command == "Edit":
            if self.product_view.focus() == '':
                return
            edit = EditItemWindow(self)
            self.wait_window(edit)
            self.product_view.delete(edit.product_id)
            self.product_view.insert('', 'end', edit.product_id, text=edit.product_id)
            self.product_view.set(edit.product_id, 'itemcode', edit.product_select[1])
            self.product_view.set(edit.product_id, 'description', edit.product_select[2])
            self.product_view.set(edit.product_id, 'unit', edit.product_select[3])
            self.product_view.set(edit.product_id, 'quantity', edit.quantity)
            self.product_view.set(edit.product_id, 'price', edit.price)
            self.product_view.set(edit.product_id, 'amount', edit.amount)
            self.updateTotal()
        elif command == "Delete":
            item_focus = self.product_view.focus()
            answer = mb.askokcancel("information", "Delete this item?")
            if answer:
                self.product_view.delete(item_focus)
                self.updateTotal()
        elif command == "Save":
            # Check first if items were available for saving else pop up warning.
            children = self.product_view.get_children()
            if len(children) == 0:
                mb.showwarning("Warning", "Add at least one item in the table.")
                return
            try:
                # Insert details in incoming table.
                date = self.date_entry.get()
                costctr = self.costctr_entry.get()
                query = self.db.cur.execute(
                    """SELECT id FROM costcenters WHERE code=?""", (costctr,))
                data = query.fetchone()
                costcenter_id = data[0]
                remarks = self.rem_entry.get()
                receipt = {'table': 'outgoing', 'date': date, 'costcenter_id': costcenter_id,
                           'remarks': remarks
                           }
                self.db.insertRecord(**receipt)
                # Insert details into in_transaction table.
                self.transid_entry.config(state="normal")
                record_id = self.checkRecordID()
                record_id = record_id[0]
                self.transid_entry.insert('end', record_id)
                main_list = []
                sub_list = ()
                record_id = int(record_id)
                for child in children:
                    pro_id = int(child)
                    quantity = float(self.product_view.item(child)['values'][3])
                    price = float(self.product_view.item(child)['values'][4])
                    sub_list += (record_id, pro_id, quantity, price)
                    main_list.append(sub_list)
                    sub_list = ()

                receipt_items = {'table': 'out_transaction',
                                'itemlist': main_list}
                self.db.insertRecord(**receipt_items)
            finally:
                event.widget.config(state="disable")
        elif command == "Print":
            children = self.product_view.get_children()
            date = self.date_entry.get()
            costctrcode = self.costctr_entry.get()
            query = self.db.cur.execute(
                """SELECT description FROM costcenters WHERE code=?""", (costctrcode,))
            data = query.fetchone()
            costctrname = data[0]
            remarks = self.rem_entry.get()
            self.transid_entry.config(state="normal")
            transid = self.transid_entry.get()
            self.transid_entry.config(state="disable")

            item_list = []
            counter = 1
            amount = 0
            for child in children:
                serial = counter
                itemcode = self.product_view.item(child)['values'][0]
                if isinstance(itemcode, int):
                    itemcode = format(itemcode, '0>10')
                desc = self.product_view.item(child)['values'][1]
                unit = self.product_view.item(child)['values'][2]
                quantity = float(self.product_view.item(child)['values'][3])
                price = float(self.product_view.item(child)['values'][4])
                value = float(self.product_view.item(child)['values'][5])
                amount += float(value)
                item_list.append((str(serial), itemcode, desc, unit,
                                  quantity, price, value))
                counter += 1
            options = {'mode': "outgoing",
                       'transid': transid,
                       'date': date,
                       'costctrcode': costctrcode,
                       'costctrname': costctrname}
            pdf = PDF(**options)
            pdf.alias_nb_pages()
            pdf.add_page()
            # The rest of the report will be inserted here.
            pdf.set_font('Courier', '', 10)

            for item in item_list:
                pdf.cell(15, 10, item[0])
                pdf.cell(30, 10, item[1])
                pdf.cell(60, 10, item[2][0:25])
                pdf.cell(15, 10, item[3], 0, 0, 'C')
                pdf.cell(20, 10, format(item[4], '0.2f'))
                pdf.cell(20, 10, format(item[5], '0.2f'))
                pdf.cell(30, 10, format(item[6], '0,.2f'))
                pdf.ln(5)
            pdf.ln(25)
            pdf.set_font('Courier', 'B', 10)
            pdf.cell(105, 7, "Remarks: "+remarks)
            pdf.cell(15, 7, "")
            pdf.cell(40, 7, "Total Amount:", 0, 0, 'C')
            pdf.cell(30, 7, format(amount, '0,.2f'), 1, 0, 'C')
            pdf.output('reports/outgoing.pdf', 'F')

            try:
                os.system('start '+'reports/outgoing.pdf')
            except:
                print("Error Printing")
        elif command == "Close":
            self._close()

    def checkRecordID(self):
        query = self.db.cur.execute("""SELECT id FROM outgoing""")
        data = query.fetchall()
        if len(data) == 0:
            return str(1)
        else:
            return str(data[-1][0])

    def updateTotal(self):
        amount = 0
        children = self.product_view.get_children()
        if len(children) != 0:
            for child in children:
                amount += float(self.product_view.item(child)['values'][5])
        amount = "Total: %s" % format(amount, '0.2f')
        self.total_var.set(amount)

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        try:
            if self.db.status:
                self.db.closeDB()
        finally:
            self.grab_release()
            self.destroy()

class AboutWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.setupUI()

    def setupUI(self):
        self.title("About")
        self.grab_set()
        style = ttk.Style()
        style.configure('AppName.TLabel', font=("Tahoma", 12, "bold"),
                        foreground="red")

        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        app_lbl = ttk.Label(mainframe, text="JTS-Inventory", style="AppName.TLabel")
        app_lbl.pack()
        ver_lbl = ttk.Label(mainframe, text="version: "+__version__)
        ver_lbl.pack()
        desc = "A simple inventory software using\nPython, SQLite3 and Tkinter."
        desc_lbl = ttk.Label(mainframe, text=desc, justify='center')
        desc_lbl.pack()
        aut_lbl = ttk.Label(mainframe, text="Author: Jesus Vedasto Olazo")
        aut_lbl.pack()
        email_lbl = ttk.Label(mainframe, text="jessie@jestoy.frihost.net")
        email_lbl.pack()
        lic_lbl = ttk.Label(mainframe, text="License: GPL-3")
        lic_lbl.pack()

        self.close_btn = ttk.Button(mainframe, text="Close", command=self._close)
        self.close_btn.pack()
        self.close_btn.focus_set()

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()

class HelpWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.setupUI()

    def setupUI(self):
        self.title("Help")
        self.geometry("640x480")

        lic_text = ScrolledText(self, bg="gray", fg="white")
        lic_text.pack(expand=True, fill="both")

        with open("docs/Documentation.txt", 'r') as f:
            data = f.read()

        lic_text.insert('1.0', data)
        lic_text.focus_set()
        lic_text.config(state="disable")

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.destroy()

class LicenseWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.setupUI()

    def setupUI(self):
        self.title("License")
        self.geometry("640x480")

        lic_text = ScrolledText(self, bg="gray", fg="white")
        lic_text.pack(expand=True, fill="both")

        with open("LICENSE.txt", 'r') as f:
            data = f.read()

        lic_text.insert('1.0', data)
        lic_text.focus_set()
        lic_text.config(state="disable")

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.destroy()

class NewDBWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.status = False
        self.default_db = None
        self.master.withdraw()
        self.setupUI()
        self._setPositionCtr()

    def setupUI(self):
        self.title("New Database")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)

        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        info_lbl = ttk.Label(mainframe,
                             text="Please enter a name for your database.")
        info_lbl.pack()

        self.default_db_entry = ttk.Entry(mainframe)
        self.default_db_entry.pack()
        self.default_db_entry.focus_set()

        ok_btn = ttk.Button(mainframe, text="Ok")
        ok_btn.pack()
        ok_btn.bind("<Button-1>", self.buttonHandler)

    def buttonHandler(self, event):
        if event.widget.cget('text') == "Ok":
            if os.path.isfile('config.json'):
                self._close()
            else:
                try:
                    default_db = self.default_db_entry.get() + ".db"
                    if default_db == "":
                        default_db = 'default.db'
                    if ' ' in self.default_db_entry.get():
                        default_db = default.db.strip()
                    with open('config.json', 'w') as cf:
                        data = {'default_db': default_db}
                        json.dump(data, cf)
                    self.status = True
                finally:
                    self._close()

    def _setPositionCtr(self):
        self.update_idletasks()
        scr_x = self.winfo_screenwidth()
        scr_y = self.winfo_screenheight()
        x = self.winfo_width()
        y = self.winfo_height()
        pos = "+" + str(int(((scr_x-x)/2))) + "+" + str(int(((scr_y-y)/2)))
        self.geometry(pos)

    def _close(self):
        self.master.iconify()
        self.grab_release()
        self.destroy()

# Start of CostCenterWindow class.
class CostCenterWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        try:
            with open('config.json', 'r') as cf:
                data = json.load(cf)
                
            self.db = Database()
            db = data['default_db']
            self.db.openDB(db)
        except:
            print(sys.exc_info()[1])
        self.setupUI()

    def setupUI(self):
        self.title("Cost Centers")
        self.geometry("480x320+100+100")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        self.style = ttk.Style()
        self.style.configure(".", background="orange")

        mainframe = tk.Frame(self, bg="orange")
        mainframe.pack(expand=True, fill="both")
        cost_ctr_label = tk.Label(mainframe, text="Cost Centers",
                             font=("Tahoma", 12, "bold"),
                             bg="orange")
        cost_ctr_label.pack(fill="x", padx=15, pady=15)
        top_frame = tk.Frame(mainframe, bg="orange")
        top_frame.pack(fill="x")
        bottom_frame = tk.Frame(mainframe, bg="orange")
        bottom_frame.pack(expand=True, fill="both")
        left_frame = tk.Frame(bottom_frame, bg="orange")
        left_frame.pack(side="left", expand=True, fill="both")
        right_frame = tk.Frame(bottom_frame, bg="orange")
        right_frame.pack(fill="y", padx=5, pady=5)

        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.grid(row=0, column=0, padx=3, pady=3)
        self.search_entry.focus_set()
        self.search_btn = ttk.Button(top_frame, text="Search",
                                     command=lambda: self.buttonHandler("SEARCH"))
        self.search_btn.grid(row=0, column=1)

        self.costctr_view = ttk.Treeview(left_frame)
        self.scroll = ttk.Scrollbar(left_frame)
        self.costctr_view.pack(side="left", expand=True, fill="both")
        self.scroll.pack(side="right", fill="y")
        self.costctr_view.config(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.costctr_view.yview)

        self.costctr_view['columns'] = ("code", "name")
        self.costctr_view.heading('#0', text="Cost ID")
        self.costctr_view.heading('code', text="Cost Code")
        self.costctr_view.heading('name', text="Cost Name")

        self.costctr_view.column('#0', stretch=False, width=50)
        self.costctr_view.column('code', stretch=False, width=55)
        self.costctr_view.column('name', width=80)
        self.updateView()

        self.new_btn = ttk.Button(right_frame, text="New",
                                  command=lambda: self.buttonHandler("NEW"))
        self.new_btn.pack()
        self.edit_btn = ttk.Button(right_frame, text="Edit",
                                   command=lambda: self.buttonHandler("EDIT"))
        self.edit_btn.pack()
        self.del_btn = ttk.Button(right_frame, text="Delete",
                                  command=lambda: self.buttonHandler("DELETE"))
        self.del_btn.pack()
        self.close_btn = ttk.Button(right_frame, text="Close",
                                    command=lambda: self.buttonHandler("CLOSE"))
        self.close_btn.pack()

    def buttonHandler(self, data):
        if data == "NEW":
            NewCostCenter(self, bg="orange")
        elif data == "EDIT":
            if self.costctr_view.focus() != '':
                self.selectcode = int(self.costctr_view.focus())
                #EditUser(self, bg="orange")
                mb.showinfo("Information", "Available Soon.")
            else:
                return
        elif data == "DELETE":
            if self.costctr_view.focus() != '':
                self.selectcode = int(self.costctr_view.focus())
                self.db.deleteRecord(table="costcenters", costid=self.selectcode)
                self.updateView()
        elif data == "SEARCH":
            mb.showinfo("Information", "Available Soon")
        elif data == "CLOSE":
            self._close()

    def updateView(self):
        if len(self.costctr_view.get_children()) != 0:
            costcenters = self.costctr_view.get_children()
            for cost in costcenters:
                self.costctr_view.delete(cost)
        
        query = self.db.cur.execute("""SELECT * FROM costcenters""")
        data = query.fetchall()
        if len(data) == 0:
            return
        else:
            for code in data:
                self.costctr_view.insert('', 'end', str(code[0]), text=str(code[0]))
                self.costctr_view.set(str(code[0]), 'code', str(code[1]))
                self.costctr_view.set(str(code[0]), 'name', str(code[2]))

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        try:
            if self.db.status:
                self.db.closeDB()
        finally:
            self.grab_release()
            self.destroy()
# End of CostCenterWindow class.

# Start of NewCostCenter class.
class NewCostCenter(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.setupUI()

    def setupUI(self):
        self.title("New Cost Center")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        top_frame = ttk.Frame(mainframe, padding="0.5i")
        top_frame.pack(expand=True, fill="both")
        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(fill="x")

        code_lbl = ttk.Label(top_frame, text="Code:")
        code_lbl.grid(row=0, column=0, sticky="w")
        name_lbl = ttk.Label(top_frame, text="Description:")
        name_lbl.grid(row=1, column=0, sticky="w")

        self.code_entry = ttk.Entry(top_frame)
        self.code_entry.grid(row=0, column=1, padx=2, pady=2)
        self.code_entry.focus_set()
        self.name_entry = ttk.Entry(top_frame)
        self.name_entry.grid(row=1, column=1, padx=2, pady=2)

        self.cancel_btn = ttk.Button(bottom_frame, text="Cancel")
        self.cancel_btn.pack(side="right")
        self.cancel_btn.config(command=self._close)
        self.save_btn = ttk.Button(bottom_frame, text="Save")
        self.save_btn.pack(side="right")
        self.save_btn.config(command=self.saveCostCenter)

    def saveCostCenter(self):
        code = self.code_entry.get()
        name = self.name_entry.get()
        if len(code) != 0 and len(name) != 0:
            self.master.db.insertRecord(table="costcenters",
                                        code=code,
                                        name=name)
            self.master.updateView()
            self._close()

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()
# End of NewCostCenter class.

class Database:
    
    def __init__(self):
        self.status = False
        self.salt = "mahalKitaPwedeBa@02251980"

    def openDB(self, db_name):
        try:
            if isinstance(db_name, unicode):
                db_name = str(db_name)
        except NameError:
            pass

        if isinstance(db_name, str):
            if os.path.isfile(db_name):
                self.con = sqlite3.connect(db_name)
                self.cur = self.con.cursor()
                self.status = True
            else:
                self.con = sqlite3.connect(db_name)
                self.cur = self.con.cursor()
                self._createDB()
                self.status = True

    def closeDB(self):
        if self.status:
            self.cur.close()
            self.con.close()

    def _createDB(self):
        self.cur.execute("""CREATE TABLE
            users(id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, password TEXT, usertype TEXT)""")
        
        self.cur.execute("""CREATE TABLE
            costcenters(id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT, description TEXT)""")
        
        self.cur.execute("""CREATE TABLE
            products(id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT, description TEXT, unit TEXT, price REAL,
            max REAL, min REAL)""")
        
        self.cur.execute("""CREATE TABLE
            incoming(id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, dn_number TEXT, supplier TEXT,
            remarks TEXT)""")
        
        self.cur.execute("""CREATE TABLE
            in_transaction(id INTEGER PRIMARY KEY AUTOINCREMENT,
            incoming_id INTEGER, product_id INTEGER, quantity REAL,
            price REAL, FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(incoming_id) REFERENCES incoming(id))""")

        self.cur.execute("""CREATE TABLE
            outgoing(id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, costcenter_id Integer, remarks TEXT,
            FOREIGN KEY(costcenter_id) REFERENCES costcenters(id))""")
        
        self.cur.execute("""CREATE TABLE
            out_transaction(id INTEGER PRIMARY KEY AUTOINCREMENT,
            outgoing_id INTEGER, product_id INTEGER, quantity REAL,
            price REAL, FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(outgoing_id) REFERENCES outgoing(id))""")

        self.cur.execute("""CREATE TABLE
            adjustment(id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, remarks TEXT)""")

        self.cur.execute("""CREATE TABLE
            adjust_trans(id INTEGER PRIMARY KEY AUTOINCREMENT,
            adjustment_id INTEGER, product_id INTEGER, quantity REAL,
            price REAL, type TEXT, FOREIGN KEY(product_id)
            REFERENCES products(id), FOREIGN KEY(adjustment_id)
            REFERENCES adjustment(id))""")

        username = "ADMIN"
        password = "ADMIN" + self.salt
        password = hashlib.sha224(password.encode("utf-8")).hexdigest()
        usertype = "ADMIN"

        self.cur.execute("""INSERT INTO users(id, username, password, usertype)
            VALUES(null, ?, ?, ?)""", (username, password, usertype))

        self.con.commit()

    def insertRecord(self, **kwargs):
        if kwargs['table'] == "users":
            username = kwargs['user']
            password = kwargs['password'] + self.salt
            password = hashlib.sha224(password.encode("utf-8")).hexdigest()
            usertype = kwargs['usertype']
            self.cur.execute(
                """INSERT INTO users(id, username, password, usertype)
                VALUES(null, ?, ?, ?)""", (username, password, usertype))
            self.con.commit()
        elif kwargs['table'] == "products":
            itemcode = kwargs['itemcode']
            desc = kwargs['description']
            unit = kwargs['unit']
            price = float(kwargs['price'])
            max_qty = float(kwargs['max_qty'])
            min_qty = float(kwargs['min_qty'])
            self.cur.execute(
                """INSERT INTO
                products(id, code, description,
                unit, price, max, min)
                VALUES(null, ?, ?, ?, ?, ?, ?)
                """, (itemcode, desc, unit, price, max_qty, min_qty)
                )
            self.con.commit()

        elif kwargs['table'] == "incoming":
            tran_date = kwargs['date']
            dn_number = kwargs['dn_number']
            supplier = kwargs['supplier']
            remarks = kwargs['remarks']
            self.cur.execute(
                """INSERT INTO
                incoming VALUES(null, ?, ?, ?, ?)
                """, (tran_date, dn_number, supplier, remarks))
            self.con.commit()

        elif kwargs['table'] == "outgoing":
            tran_date = kwargs['date']
            costctr = kwargs['costcenter_id']
            remarks = kwargs['remarks']
            self.cur.execute(
                """INSERT INTO
                outgoing VALUES(null, ?, ?, ?)
                """, (tran_date, costctr, remarks))
            self.con.commit()

        elif kwargs['table'] == "adjustment":
            tran_date = kwargs['date']
            remarks = kwargs['remarks']
            self.cur.execute(
                """INSERT INTO
                adjustment VALUES(null, ?, ?)
                """, (tran_date, remarks))
            self.con.commit()

        elif kwargs['table'] == "adjust_trans":
            item_list = kwargs['itemlist']
            self.cur.executemany(
                """INSERT INTO
                adjust_trans VALUES(null, ?, ?, ?, ?, ?)
                """, item_list)
            self.con.commit()

        elif kwargs['table'] == "costcenters":
            code = kwargs['code']
            name = kwargs['name']
            self.cur.execute(
                """INSERT INTO
                costcenters VALUES(null, ?, ?)
                """, (code, name))
            self.con.commit()

        elif kwargs['table'] == "in_transaction":
            item_list = kwargs['itemlist']
            self.cur.executemany(
                """INSERT INTO
                in_transaction VALUES(null, ?, ?, ?, ?)
                """, item_list)
            self.con.commit()

        elif kwargs['table'] == "out_transaction":
            item_list = kwargs['itemlist']
            self.cur.executemany(
                """INSERT INTO
                out_transaction VALUES(null, ?, ?, ?, ?)
                """, item_list)
            self.con.commit()

    def deleteRecord(self, **kwargs):
        if kwargs['table'] == "users":
            userid = kwargs['userid']
            check = mb.askokcancel("Warning", "Delete this user?")
            if not check:
                return
            self.cur.execute(
                """DELETE FROM users WHERE id=?""", (userid,))
            self.con.commit()

    def updateRecord(self, **kwargs):
        if kwargs['table'] == "users":
            userid = kwargs['userid']
            password = kwargs['password'] + self.salt
            password = hashlib.sha224(password.encode("utf-8")).hexdigest()
            usertype = kwargs['usertype']
            self.cur.execute(
                """
                UPDATE users SET password=?, usertype=? WHERE id=?
                """, (password, usertype, userid))
            self.con.commit()
        elif kwargs['table'] == "products":
            productid = kwargs['productid']
            description = kwargs['description']
            price = float(kwargs['price'])
            max_qty = float(kwargs['max_qty'])
            min_qty = float(kwargs['min_qty'])
            self.cur.execute(
                """
                UPDATE products SET description=?, price=?, max=?, min=? WHERE id=?
                """, (description, price, max_qty, min_qty, productid))
            self.con.commit()

# Start of AdjustmentWindow class.
class AdjustmentWindow(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        with open('config.json', 'r') as cf:
            data = json.load(cf)
        self.db = Database()
        db = data['default_db']
        self.db.openDB(db)
        self.setupUI()

    def setupUI(self):
        self.title("Adjustment")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()

        adj_img_open = Image.open('images/tape.png')
        self.adj_img = ImageTk.PhotoImage(adj_img_open.resize((36, 36)))

        mainframe = ttk.Frame(self)
        mainframe.pack(expand=True, fill="both")

        adj_label = tk.Label(mainframe, text="Adjustment", fg="white",
                          font=("Tahoma", 12, "bold"), bg="orange",
                          image=self.adj_img, compound="left")
        adj_label.pack(fill="x", padx=15, pady=15)

        top_frame = ttk.Frame(mainframe)
        top_frame.pack(fill="x")
        middle_frame = ttk.Frame(mainframe)
        middle_frame.pack(fill="x")
        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(expand=True, fil="both")
        total_frame = ttk.Frame(mainframe)
        total_frame.pack(fill="x")

        transid_lbl = ttk.Label(top_frame, text="Transaction ID:")
        transid_lbl.grid(row=0, column=0)
        datefor_lbl = ttk.Label(top_frame, text="(DD-MM-YYYY)")
        datefor_lbl.grid(row=0, column=3)
        date_lbl = ttk.Label(top_frame, text="Date:")
        date_lbl.grid(row=1, column=2)
        rem_lbl = ttk.Label(top_frame, text="Remarks:")
        rem_lbl.grid(row=1, column=0)

        self.transid_entry = tk.Entry(top_frame, width=12)
        self.transid_entry.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.transid_entry.config(state="disable")
        
        self.date_entry = tk.Entry(top_frame, width=12)
        self.date_entry.grid(row=1, column=3, padx=2, pady=2)
        self.date_entry.insert('end', time.strftime("%d-%m-%Y"))
        self.rem_entry = tk.Entry(top_frame, width=60)
        self.rem_entry.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        self.rem_entry.focus_set()

        # Add 3 buttons for add, edit, and delete product/s.
        self.add_btn = ttk.Button(middle_frame, text="Add")
        self.add_btn.grid(row=0, column=0)
        self.add_btn.bind("<Button-1>", self.buttonHandler)
        self.edit_btn = ttk.Button(middle_frame, text="Edit")
        self.edit_btn.grid(row=0, column=1)
        self.edit_btn.bind("<Button-1>", self.buttonHandler)
        self.del_btn = ttk.Button(middle_frame, text="Delete")
        self.del_btn.grid(row=0, column=2)
        self.del_btn.bind("<Button-1>", self.buttonHandler)

        # Add the product view and 3 buttons for print, save
        # and close transaction. After transaction has been save
        # save button will be disabled to avoid saving the transaction
        # twice.
        left_frame = ttk.Frame(bottom_frame)
        left_frame.pack(side="left", expand=True, fill="both")
        right_frame = ttk.Frame(bottom_frame)
        right_frame.pack(fill="y")

        self.product_view = ttk.Treeview(left_frame)
        self.product_view.pack(expand=True, fill="both", side="left")
        self.scroll = ttk.Scrollbar(left_frame, orient="vertical")
        self.scroll.pack(side="right", fill="y")
        self.product_view.config(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.product_view.yview)

        column = ("itemcode", "description",
                  "unit", "quantity", "price",
                  "amount", "type")
        self.product_view['columns'] = column
        self.product_view['show'] = 'headings'
        
        for col in column:
            self.product_view.heading(col, text=col.title())

        self.product_view.column(column[0], width=60)
        self.product_view.column(column[1], width=175)
        self.product_view.column(column[2], width=25)
        self.product_view.column(column[3], width=50)
        self.product_view.column(column[4], width=50)
        self.product_view.column(column[5], width=50)
        self.product_view.column(column[6], width=25)

        self.save_btn = ttk.Button(right_frame, text="Save")
        self.save_btn.pack(anchor="n")
        self.save_btn.bind("<Button-1>", self.buttonHandler)
        self.print_btn = ttk.Button(right_frame, text="Print")
        self.print_btn.pack(anchor="n")
        self.print_btn.bind("<Button-1>", self.buttonHandler)
        self.close_btn = ttk.Button(right_frame, text="Close")
        self.close_btn.pack(anchor="s")
        self.close_btn.bind("<Button-1>", self.buttonHandler)

        self.total_var = tk.StringVar()
        self.total_var.set('Total: %s' % format(0.0, '0.2f'))
        self.total_value_lbl = tk.Label(total_frame,
                                        textvariable=self.total_var,
                                        anchor='w',
                                        bg="orange",
                                        font=("Tahoma", 10, "bold"),
                                        fg="blue", relief="groove",
                                        padx=5, pady=5
                                        )
        self.total_value_lbl.pack(fill="x")

    def buttonHandler(self, event):
        command = event.widget.cget('text')
        if command == "Add":
            add = AddItemAdjWin(self)
            self.wait_window(add)
            if add.product_id is None:
                return
            self.product_view.insert('', 'end', add.product_id, text=add.product_id)
            self.product_view.set(add.product_id, 'itemcode', add.product_select[1])
            self.product_view.set(add.product_id, 'description', add.product_select[2])
            self.product_view.set(add.product_id, 'unit', add.product_select[3])
            self.product_view.set(add.product_id, 'quantity', add.quantity)
            self.product_view.set(add.product_id, 'price', add.price)
            self.product_view.set(add.product_id, 'amount', add.amount)
            self.product_view.set(add.product_id, 'type', add.adj_type)
            self.updateTotal()
        elif command == "Edit":
            if self.product_view.focus() == '':
                return
            edit = EditItemWindow(self)
            self.wait_window(edit)
            self.product_view.delete(edit.product_id)
            self.product_view.insert('', 'end', edit.product_id, text=edit.product_id)
            self.product_view.set(edit.product_id, 'itemcode', edit.product_select[1])
            self.product_view.set(edit.product_id, 'description', edit.product_select[2])
            self.product_view.set(edit.product_id, 'unit', edit.product_select[3])
            self.product_view.set(edit.product_id, 'quantity', edit.quantity)
            self.product_view.set(edit.product_id, 'price', edit.price)
            self.product_view.set(edit.product_id, 'amount', edit.amount)
            self.product_view.set(edit.product_id, 'type', edit.adj_type)
            self.updateTotal()
        elif command == "Delete":
            item_focus = self.product_view.focus()
            answer = mb.askokcancel("information", "Delete this item?")
            if answer:
                self.product_view.delete(item_focus)
                self.updateTotal()
        elif command == "Save":
            # Check first if items were available for saving else pop up warning.
            children = self.product_view.get_children()
            if len(children) == 0:
                mb.showwarning("Warning", "Add at least one item in the table.")
                return
            try:
                # Insert details in incoming table.
                date = self.date_entry.get()
                remarks = self.rem_entry.get()
                receipt = {'table': 'adjustment', 'date': date,
                           'remarks': remarks
                           }
                self.db.insertRecord(**receipt)
                # Insert details into in_transaction table.
                self.transid_entry.config(state="normal")
                record_id = self.checkRecordID()
                record_id = record_id[0]
                self.transid_entry.insert('end', record_id)
                main_list = []
                sub_list = ()
                record_id = int(record_id)
                for child in children:
                    pro_id = int(child)
                    price = float(self.product_view.item(child)['values'][4])
                    adj_type = self.product_view.item(child)['values'][6]
                    if adj_type == 'minus':
                        quantity = float(self.product_view.item(child)['values'][3]) * -1
                    else:
                        quantity = float(self.product_view.item(child)['values'][3])
                    sub_list += (record_id, pro_id, quantity, price, adj_type)
                    main_list.append(sub_list)
                    sub_list = ()

                receipt_items = {'table': 'adjust_trans',
                                'itemlist': main_list}
                self.db.insertRecord(**receipt_items)
            finally:
                event.widget.config(state="disable")
        elif command == "Print":
            children = self.product_view.get_children()
            date = self.date_entry.get()
            remarks = self.rem_entry.get()
            self.transid_entry.config(state="normal")
            transid = self.transid_entry.get()
            self.transid_entry.config(state="disable")

            item_list = []
            counter = 1
            amount = 0
            for child in children:
                serial = counter
                itemcode = self.product_view.item(child)['values'][0]
                if isinstance(itemcode, int):
                    itemcode = format(itemcode, '0>10')
                desc = self.product_view.item(child)['values'][1]
                unit = self.product_view.item(child)['values'][2]
                quantity = float(self.product_view.item(child)['values'][3])
                price = float(self.product_view.item(child)['values'][4])
                value = float(self.product_view.item(child)['values'][5])
                adj_type = self.product_view.item(child)['values'][6]
                if adj_type == 'plus':
                    adj_type = '+'
                elif adj_type == 'minus':
                    adj_type = '-'
                else:
                    adj_type = ''
                amount += float(value)
                item_list.append((str(serial), itemcode, desc, unit, adj_type,
                                  quantity, price, value))
                counter += 1
            options = {'mode': "adjustment",
                       'transid': transid,
                       'date': date
                       }
            pdf = PDF(**options)
            pdf.alias_nb_pages()
            pdf.add_page()
            # The rest of the report will be inserted here.
            pdf.set_font('Courier', '', 10)
            for item in item_list:
                pdf.cell(13, 10, item[0])
                pdf.cell(28, 10, item[1])
                pdf.cell(55, 10, item[2][0:20])
                pdf.cell(13, 10, item[3], 0, 0, 'C')
                pdf.cell(13, 10, item[4], 0, 0, 'C')
                pdf.cell(19, 10, format(item[5], '0.2f'))
                pdf.cell(19, 10, format(item[6], '0.2f'))
                pdf.cell(28, 10, format(item[7], '0,.2f'))
                pdf.ln(5)
            pdf.ln(25)
            pdf.set_font('Courier', 'B', 10)
            pdf.cell(105, 7, "Remarks: "+remarks)
            pdf.cell(15, 7, "")
            pdf.cell(40, 7, "Total Amount:", 0, 0, 'C')
            pdf.cell(30, 7, format(amount, '0,.2f'), 1, 0, 'C')
            pdf.output('reports/adjustment.pdf', 'F')

            try:
                os.system('start '+'reports/adjustment.pdf')
            except:
                print("Error Printing")
        elif command == "Close":
            self._close()

    def checkRecordID(self):
        query = self.db.cur.execute("""SELECT id FROM adjustment""")
        data = query.fetchall()
        if len(data) == 0:
            return str(1)
        else:
            return str(data[-1][0])

    def updateTotal(self):
        amount = 0
        children = self.product_view.get_children()
        if len(children) != 0:
            for child in children:
                amount += float(self.product_view.item(child)['values'][5])
        amount = "Total: %s" % format(amount, '0.2f')
        self.total_var.set(amount)

    def _closeEvent(self, event):
        self._close()

    def _close(self):
        try:
            if self.db.status:
                self.db.closeDB()
        finally:
            self.grab_release()
            self.destroy()
# End of AdjustmentWindow class.

# Start of AddItemAdjWin class.
class AddItemAdjWin(tk.Toplevel):

    def __init__(self, master=None, **kwargs):
        tk.Toplevel.__init__(self, master, **kwargs)
        self.product_id = None
        self.price = None
        self.quantity = None
        self.amount = None
        self.product_select = None
        self.adj_type = None
        self.setupUI()

    def setupUI(self):
        self.title("Add")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        mainframe = ttk.Frame(self, padding="0.2i")
        mainframe.pack(expand=True, fill="both")

        ttk.Label(mainframe, text="Itemcode:").grid(row=0, column=0, sticky="w")
        ttk.Label(mainframe, text="Quantity:").grid(row=1, column=0, sticky="w")
        ttk.Label(mainframe, text="Price:").grid(row=2, column=0, sticky="w")

        self.pro_entry = tk.Entry(mainframe, validate="focusout",
                                  validatecommand=self.loadPrice)
        self.pro_entry.grid(row=0, column=1, sticky='w', padx=2, pady=2)
        self.pro_entry.focus_set()
        
        self.quantity_entry = tk.Entry(mainframe, width=5)
        self.quantity_entry.grid(row=1, column=1, sticky='w', padx=2, pady=2)
        self.price_entry = tk.Entry(mainframe, width=7)
        self.price_entry.grid(row=2, column=1, sticky='w', padx=2, pady=2)

        radio_frame = ttk.LabelFrame(mainframe, text="Adjustment Type")
        radio_frame.grid(row=3, column=0, columnspan=2, sticky="w")
        self.radio_var = tk.StringVar()
        self.radio_var.set('minus')
        self.radio_pl_btn = ttk.Radiobutton(radio_frame, text="Plus", value="plus",
                                         variable=self.radio_var)
        self.radio_pl_btn.grid(row=0, column=0)
        self.radio_mi_btn = ttk.Radiobutton(radio_frame, text="Minus", value="minus",
                                         variable=self.radio_var)
        self.radio_mi_btn.grid(row=0, column=1)

        btn_frame = ttk.Frame(mainframe)
        btn_frame.grid(row=4, column=0, columnspan=2,
                       sticky="we", padx=5, pady=5)

        self.add_btn = ttk.Button(btn_frame, text="Add")
        self.add_btn.grid(row=0, column=1, padx=2, pady=2, sticky="e")
        self.add_btn.bind("<Button-1>", self.buttonHandler)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel")
        self.cancel_btn.grid(row=0, column=0, padx=2, pady=2, sticky='e')
        self.cancel_btn.bind("<Button-1>", self.buttonHandler)

    def buttonHandler(self, event):
        command = event.widget.cget('text')
        if command == "Add":
            product = self.pro_entry.get()
            quantity = self.quantity_entry.get()
            price = self.price_entry.get()
            if product == '':
                mb.showwarning("Invalid", "Invalid item code.")
            elif quantity == '':
                mb.showwarning("Invalid", "Invalid quantity.")
            elif price == '':
                mb.showwarning("Invalid", "Invalid price.")
            else:
                query = self.master.db.cur.execute(
                    """SELECT * FROM products WHERE code=?""", (product,))
                data = query.fetchone()
                self.product_select = data
                self.product_id = str(data[0])
                self.price = str(price)
                self.quantity = str(quantity)
                self.adj_type = self.radio_var.get()
                if self.adj_type == 'minus':
                    self.amount = str(float(price) * float(quantity) * -1)
                else:
                    self.amount = str(float(price) * float(quantity))
                self._close()
        elif command == "Cancel":
            self._close()

    def loadPrice(self):
        code = self.pro_entry.get()
        query = self.master.db.cur.execute(
            """SELECT price FROM products WHERE code=?""", (code,))
        data = query.fetchone()
        if data == None:
            print("Sorry no item")
        elif len(data) != 0:
            self.price_entry.insert('end', format(data[0], '0.2f'))
        else:
            mb.showwarning("Invalid", "Invalid item code.\nPlease try again.")

    def _closeEvent(self):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()
# End of AddItemAdjWin class.

class PDF(FPDF):

    def __init__(self, **kwargs):
        FPDF.__init__(self)
        self.mode = kwargs['mode']
        if self.mode == "incoming":
            self.transid = kwargs['transid']
            self.dn_number = kwargs['dn_number']
            self.supplier = kwargs['supplier']
            self.date = kwargs['date']
        elif self.mode == "outgoing":
            self.transid = kwargs['transid']
            self.costctrcode = kwargs['costctrcode']
            self.costctrname = kwargs['costctrname']
            self.date = kwargs['date']
        elif self.mode == "adjustment":
            self.transid = kwargs['transid']
            self.date = kwargs['date']
        else:
            pass

    def header(self):
        if self.mode == "incoming":
            # Set the logo.
            self.image('images/cart-12.png', 10, 8, 33)
            # Set the font.
            self.set_font('Times', 'B', 16)
            # Add the title.
            self.cell(0, 10, 'Incoming Transaction', 0, 0, 'C')
            # Add a line break.
            self.ln(45)
            # Add custom header.
            self.set_font('Courier', 'B', 13)
            self.cell(0, 7, "Trans. No.: IN-"+self.transid, 0, 1, 'R')
            self.set_font('Courier', 'B', 10)
            self.cell(30, 7, "Date: "+self.date, 0, 1)
            self.cell(30, 7, "Supplier Ref: "+self.dn_number, 0, 1)
            self.cell(30, 7, "Supplier: "+self.supplier, 0, 1)
            self.ln(5)
            self.cell(15, 7, "S. No.", 1, 0, 'C')
            self.cell(30, 7, "Item Code", 1, 0, 'C')
            self.cell(60, 7, "Description", 1, 0, 'C')
            self.cell(15, 7, "Unit", 1, 0, 'C')
            self.cell(20, 7, "Quantity", 1, 0, 'C')
            self.cell(20, 7, "Rate", 1, 0, 'C')
            self.cell(30, 7, "Amount", 1, 0, 'C')
            self.ln(10)
        elif self.mode == "outgoing":
            # Set the logo.
            self.image('images/cashier-1.png', 10, 8, 33)
            # Set the font.
            self.set_font('Times', 'B', 16)
            # Add the title.
            self.cell(0, 10, 'Outgoing Transaction', 0, 0, 'C')
            # Add a line break.
            self.ln(45)
            # Add custom header.
            self.set_font('Courier', 'B', 13)
            self.cell(0, 7, "Trans. No.: OUT-"+self.transid, 0, 1, 'R')
            self.set_font('Courier', 'B', 10)
            self.cell(30, 7, "Date: "+self.date, 0, 1)
            self.cell(30, 7, "Cost Ctr. Code: "+self.costctrcode, 0, 1)
            self.cell(30, 7, "Cost Ctr. Name: "+self.costctrname, 0, 1)
            self.ln(5)
            self.cell(15, 7, "S. No.", 1, 0, 'C')
            self.cell(30, 7, "Item Code", 1, 0, 'C')
            self.cell(60, 7, "Description", 1, 0, 'C')
            self.cell(15, 7, "Unit", 1, 0, 'C')
            self.cell(20, 7, "Quantity", 1, 0, 'C')
            self.cell(20, 7, "Rate", 1, 0, 'C')
            self.cell(30, 7, "Amount", 1, 0, 'C')
            self.ln(10)

        elif self.mode == "adjustment":
            # Set the logo.
            self.image('images/tape.png', 10, 8, 33)
            # Set the font.
            self.set_font('Times', 'B', 16)
            # Add the title.
            self.cell(0, 10, 'Adjustment Transaction', 0, 0, 'C')
            # Add a line break.
            self.ln(45)
            # Add custom header.
            self.set_font('Courier', 'B', 13)
            self.cell(0, 7, "Trans. No.: ADJ-"+self.transid, 0, 1, 'R')
            self.set_font('Courier', 'B', 10)
            self.cell(30, 7, "Date: "+self.date, 0, 1)
            self.ln(5)
            self.cell(13, 7, "S. No.", 1, 0, 'C')
            self.cell(28, 7, "Item Code", 1, 0, 'C')
            self.cell(55, 7, "Description", 1, 0, 'C')
            self.cell(13, 7, "Unit", 1, 0, 'C')
            self.cell(13, 7, "Type", 1, 0, 'C')
            self.cell(19, 7, "Quantity", 1, 0, 'C')
            self.cell(19, 7, "Rate", 1, 0, 'C')
            self.cell(28, 7, "Amount", 1, 0, 'C')
            self.ln(10)

        elif self.mode == "currentstock":
            self.set_font('Times', 'B', 16)
            # Add the title.
            self.cell(0, 10, 'Current Stock', 0, 0, 'C')
            # Add a line break.
            self.ln(12)
            # Add custom header.
            self.set_font('Courier', 'B', 10)
            date_of_report = time.strftime("%d-%b-%Y")
            self.cell(0, 7, "Date: %s" % date_of_report, 0, 1, "R") 
            self.cell(15, 7, "S. No.", 1, 0, 'C')
            self.cell(30, 7, "Item Code", 1, 0, 'C')
            self.cell(60, 7, "Description", 1, 0, 'C')
            self.cell(15, 7, "Unit", 1, 0, 'C')
            self.cell(20, 7, "Quantity", 1, 0, 'C')
            self.cell(20, 7, "Rate", 1, 0, 'C')
            self.cell(30, 7, "Amount", 1, 0, 'C')
            self.ln(10)
        else:
            pass

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Times', 'I', 9)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def main():
    processid = str(os.getpid())
    process_dir = "pid"
    process_file = 'jtsinventory.pid'
    process_path = '/'.join([process_dir, process_file])
    
    if not os.path.isdir(process_dir):
        os.mkdir('pid')
    
    if os.path.isfile(process_path):
        mb.showwarning("Warning", "Application is already running.")
        return
    else:
        with open(process_path, 'a') as mf:
            mf.write(processid)
    try:
        app = Application()
        MainWindow(app)
        app.mainloop()
    finally:
        os.unlink(process_path)
        os.rmdir(process_dir)

if __name__ == "__main__":
    main()
