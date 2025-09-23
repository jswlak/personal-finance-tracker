import tkinter as tk
from tkinter import ttk, messagebox
import json
import csv
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta
import os

class PersonalFinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("1200x800")
        
        # Currency exchange rates cache
        self.exchange_rates = {}
        self.base_currency = "USD"
        self.current_currency = "USD"
        
        # Data storage files
        self.data_dir = "data"
        self.income_file = os.path.join(self.data_dir, "income.json")
        self.expenses_file = os.path.join(self.data_dir, "expenses.json")
        self.rates_file = os.path.join(self.data_dir, "exchange_rates.json")
        
        # Initialize data storage
        self.setup_data_storage()
        self.setup_ui()
        self.load_exchange_rates()
        self.refresh_data()

    def setup_data_storage(self):
        """Setup data storage directory and files"""
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Initialize data files if they don't exist
        if not os.path.exists(self.income_file):
            self.save_json_file(self.income_file, [])
        
        if not os.path.exists(self.expenses_file):
            self.save_json_file(self.expenses_file, [])
        
        if not os.path.exists(self.rates_file):
            self.save_json_file(self.rates_file, {})

    def load_json_file(self, filepath):
        """Load data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return [] if 'rates' not in filepath else {}

    def save_json_file(self, filepath, data):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")

    def setup_ui(self):
        """Setup the main UI with tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_transactions_tab()
        self.setup_dashboard_tab()
        self.setup_charts_tab()
        self.setup_settings_tab()

    def setup_transactions_tab(self):
        """Setup the transactions tab for income and expense entry"""
        self.transactions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_frame, text="Transactions")
        
        # Currency selection
        currency_frame = ttk.Frame(self.transactions_frame, padding=10)
        currency_frame.pack(fill=tk.X)
        
        ttk.Label(currency_frame, text="Currency:").pack(side=tk.LEFT, padx=5)
        self.currency_var = tk.StringVar(value="USD")
        self.currency_combo = ttk.Combobox(currency_frame, textvariable=self.currency_var,
                                          values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"], width=10)
        self.currency_combo.pack(side=tk.LEFT, padx=5)
        self.currency_combo.bind("<<ComboboxSelected>>", self.on_currency_change)
        
        # Transaction type selection
        ttk.Label(currency_frame, text="Type:").pack(side=tk.LEFT, padx=(20, 5))
        self.transaction_type_var = tk.StringVar(value="expense")
        self.type_combo = ttk.Combobox(currency_frame, textvariable=self.transaction_type_var,
                                     values=["expense", "income"], width=10)
        self.type_combo.pack(side=tk.LEFT, padx=5)
        
        # Form frame
        form = ttk.Frame(self.transactions_frame, padding=10)
        form.pack(fill=tk.X)
        
        # Date
        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(form, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Category
        ttk.Label(form, text="Category:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form, textvariable=self.category_var, width=15)
        self.category_combo.grid(row=0, column=3, sticky=tk.W, pady=2)
        self.update_categories()
        self.type_combo.bind("<<ComboboxSelected>>", self.update_categories)
        
        # Description
        ttk.Label(form, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.desc_var = tk.StringVar()
        self.desc_entry = ttk.Entry(form, textvariable=self.desc_var, width=40)
        self.desc_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=2)
        
        # Amount
        ttk.Label(form, text="Amount:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(form, textvariable=self.amount_var, width=12)
        self.amount_entry.grid(row=0, column=5, sticky=tk.W, pady=2)
        
        # Add button
        add_btn = ttk.Button(form, text="Add Transaction", command=self.add_transaction)
        add_btn.grid(row=1, column=4, columnspan=2, padx=5, pady=4, sticky=tk.E)
        
        # Transactions list
        list_frame = ttk.Frame(self.transactions_frame, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("date", "type", "category", "description", "amount", "currency")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.tree.heading(col, text=col.title(), command=lambda c=col: self.sort_by(c, False))
            if col == "description":
                self.tree.column(col, width=250)
            elif col in ["amount", "currency"]:
                self.tree.column(col, width=80, anchor=tk.E)
            else:
                self.tree.column(col, width=100)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = ttk.Frame(self.transactions_frame, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Fields", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def setup_dashboard_tab(self):
        """Setup the dashboard tab with financial summary"""
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        
        # Summary frame
        summary_frame = ttk.LabelFrame(self.dashboard_frame, text="Financial Summary", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create summary labels
        self.total_income_label = ttk.Label(summary_frame, text="Total Income: $0.00", font=("Arial", 12, "bold"))
        self.total_income_label.pack(pady=5)
        
        self.total_expenses_label = ttk.Label(summary_frame, text="Total Expenses: $0.00", font=("Arial", 12, "bold"))
        self.total_expenses_label.pack(pady=5)
        
        self.net_worth_label = ttk.Label(summary_frame, text="Net Worth: $0.00", font=("Arial", 14, "bold"))
        self.net_worth_label.pack(pady=10)
        
        # Category breakdown
        breakdown_frame = ttk.LabelFrame(self.dashboard_frame, text="Category Breakdown", padding=10)
        breakdown_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.breakdown_tree = ttk.Treeview(breakdown_frame, columns=("category", "income", "expenses", "net"), show="headings")
        self.breakdown_tree.heading("category", text="Category")
        self.breakdown_tree.heading("income", text="Income")
        self.breakdown_tree.heading("expenses", text="Expenses")
        self.breakdown_tree.heading("net", text="Net")
        
        for col in ["income", "expenses", "net"]:
            self.breakdown_tree.column(col, width=100, anchor=tk.E)
        self.breakdown_tree.column("category", width=150)
        
        breakdown_vsb = ttk.Scrollbar(breakdown_frame, orient="vertical", command=self.breakdown_tree.yview)
        self.breakdown_tree.configure(yscroll=breakdown_vsb.set)
        self.breakdown_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        breakdown_vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_charts_tab(self):
        """Setup the charts tab for spending trends visualization"""
        self.charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.charts_frame, text="Charts")
        
        # Chart controls
        controls_frame = ttk.Frame(self.charts_frame, padding=10)
        controls_frame.pack(fill=tk.X)
        
        ttk.Label(controls_frame, text="Chart Type:").pack(side=tk.LEFT, padx=5)
        self.chart_type_var = tk.StringVar(value="monthly_trends")
        chart_combo = ttk.Combobox(controls_frame, textvariable=self.chart_type_var,
                                 values=["monthly_trends", "category_pie", "income_vs_expenses"], width=20)
        chart_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Generate Chart", command=self.generate_chart).pack(side=tk.LEFT, padx=10)
        
        # Chart frame
        self.chart_frame = ttk.Frame(self.charts_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_settings_tab(self):
        """Setup the settings tab"""
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        
        settings_content = ttk.Frame(self.settings_frame, padding=20)
        settings_content.pack(fill=tk.BOTH, expand=True)
        
        # Base currency setting
        currency_frame = ttk.LabelFrame(settings_content, text="Currency Settings", padding=10)
        currency_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(currency_frame, text="Base Currency:").pack(side=tk.LEFT)
        self.base_currency_var = tk.StringVar(value="USD")
        base_currency_combo = ttk.Combobox(currency_frame, textvariable=self.base_currency_var,
                                         values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"], width=10)
        base_currency_combo.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(currency_frame, text="Update Exchange Rates", command=self.load_exchange_rates).pack(side=tk.LEFT, padx=10)
        
        # Exchange rates display
        rates_frame = ttk.LabelFrame(settings_content, text="Current Exchange Rates", padding=10)
        rates_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.rates_text = tk.Text(rates_frame, height=15, width=50)
        rates_vsb = ttk.Scrollbar(rates_frame, orient="vertical", command=self.rates_text.yview)
        self.rates_text.configure(yscroll=rates_vsb.set)
        self.rates_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rates_vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def update_categories(self, event=None):
        """Update categories based on transaction type"""
        transaction_type = self.transaction_type_var.get()
        
        if transaction_type == "income":
            categories = ["Salary", "Freelance", "Investment", "Bonus", "Other Income"]
        else:
            categories = ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Healthcare", "Education", "Other"]
        
        self.category_combo["values"] = categories

    def load_exchange_rates(self):
        """Load exchange rates from API"""
        try:
            # Using a free API (you might want to use a more reliable one like exchangerate-api.com)
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.exchange_rates = data["rates"]
                
                # Save the rates to file
                self.save_json_file(self.rates_file, {
                    "base_currency": "USD",
                    "rates": self.exchange_rates,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                
                self.update_rates_display()
                messagebox.showinfo("Success", "Exchange rates updated successfully!")
            else:
                messagebox.showerror("Error", "Failed to fetch exchange rates")
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching exchange rates: {e}")

    def update_rates_display(self):
        """Update the exchange rates display in settings"""
        self.rates_text.delete(1.0, tk.END)
        self.rates_text.insert(tk.END, f"Base Currency: {self.base_currency}\n\n")
        
        for currency, rate in sorted(self.exchange_rates.items()):
            self.rates_text.insert(tk.END, f"1 {self.base_currency} = {rate:.4f} {currency}\n")

    def convert_currency(self, amount, from_currency, to_currency):
        """Convert amount from one currency to another"""
        if from_currency == to_currency:
            return amount
        
        if from_currency == self.base_currency:
            return amount * self.exchange_rates.get(to_currency, 1)
        elif to_currency == self.base_currency:
            return amount / self.exchange_rates.get(from_currency, 1)
        else:
            # Convert to base currency first, then to target
            base_amount = amount / self.exchange_rates.get(from_currency, 1)
            return base_amount * self.exchange_rates.get(to_currency, 1)

    def add_transaction(self):
        """Add a new transaction (income or expense)"""
        date = self.date_var.get().strip()
        category = self.category_var.get().strip()
        desc = self.desc_var.get().strip()
        amount_s = self.amount_var.get().strip()
        currency = self.currency_var.get()
        transaction_type = self.transaction_type_var.get()
        
        # Validation
        if not all([date, category, amount_s]):
            messagebox.showerror("Input error", "Date, category, and amount are required")
            return
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input error", "Date must be YYYY-MM-DD")
            return
        
        try:
            amount = float(amount_s)
        except ValueError:
            messagebox.showerror("Input error", "Amount must be a number")
            return
        
        # Create transaction record
        transaction = {
            "id": datetime.now().timestamp(),  # Use timestamp as unique ID
            "date": date,
            "category": category,
            "description": desc,
            "amount": amount,
            "currency": currency,
            "transaction_type": transaction_type
        }
        
        # Save to appropriate file
        if transaction_type == "income":
            income_data = self.load_json_file(self.income_file)
            income_data.append(transaction)
            self.save_json_file(self.income_file, income_data)
        else:
            expenses_data = self.load_json_file(self.expenses_file)
            expenses_data.append(transaction)
            self.save_json_file(self.expenses_file, expenses_data)
        
        self.refresh_data()
        self.clear_fields()

    def refresh_data(self):
        """Refresh all data displays"""
        self.populate_transactions()
        self.update_dashboard()
        self.update_breakdown()

    def populate_transactions(self):
        """Populate the transactions tree with combined income and expenses"""
        # Clear existing items
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Get all transactions
        transactions = []
        
        # Get income
        income_data = self.load_json_file(self.income_file)
        for transaction in income_data:
            transactions.append((
                transaction["id"],
                transaction["date"],
                transaction["category"],
                transaction["description"],
                transaction["amount"],
                transaction["currency"],
                transaction["transaction_type"]
            ))
        
        # Get expenses
        expenses_data = self.load_json_file(self.expenses_file)
        for transaction in expenses_data:
            transactions.append((
                transaction["id"],
                transaction["date"],
                transaction["category"],
                transaction["description"],
                transaction["amount"],
                transaction["currency"],
                transaction["transaction_type"]
            ))
        
        # Sort by date
        transactions.sort(key=lambda x: x[1], reverse=True)
        
        # Insert into tree
        for rid, date, category, desc, amount, currency, trans_type in transactions:
            converted_amount = self.convert_currency(amount, currency, self.base_currency)
            self.tree.insert("", tk.END, iid=str(rid), values=(
                date, trans_type, category, desc, f"{converted_amount:.2f}", currency
            ))

    def update_dashboard(self):
        """Update dashboard with financial summary"""
        # Calculate totals
        total_income = 0
        total_expenses = 0
        
        # Income total
        income_data = self.load_json_file(self.income_file)
        for transaction in income_data:
            amount = transaction["amount"]
            currency = transaction["currency"]
            total_income += self.convert_currency(amount, currency, self.base_currency)
        
        # Expenses total
        expenses_data = self.load_json_file(self.expenses_file)
        for transaction in expenses_data:
            amount = transaction["amount"]
            currency = transaction["currency"]
            total_expenses += self.convert_currency(amount, currency, self.base_currency)
        
        net_worth = total_income - total_expenses
        
        # Update labels
        self.total_income_label.config(text=f"Total Income: ${total_income:.2f}")
        self.total_expenses_label.config(text=f"Total Expenses: ${total_expenses:.2f}")
        
        color = "green" if net_worth >= 0 else "red"
        self.net_worth_label.config(text=f"Net Worth: ${net_worth:.2f}", foreground=color)

    def update_breakdown(self):
        """Update category breakdown"""
        # Clear existing items
        for row in self.breakdown_tree.get_children():
            self.breakdown_tree.delete(row)
        
        # Get all categories
        categories = set()
        
        income_data = self.load_json_file(self.income_file)
        for transaction in income_data:
            categories.add(transaction["category"])
        
        expenses_data = self.load_json_file(self.expenses_file)
        for transaction in expenses_data:
            categories.add(transaction["category"])
        
        # Calculate totals per category
        for category in categories:
            income_total = 0
            expense_total = 0
            
            # Income for this category
            for transaction in income_data:
                if transaction["category"] == category:
                    amount = transaction["amount"]
                    currency = transaction["currency"]
                    income_total += self.convert_currency(amount, currency, self.base_currency)
            
            # Expenses for this category
            for transaction in expenses_data:
                if transaction["category"] == category:
                    amount = transaction["amount"]
                    currency = transaction["currency"]
                    expense_total += self.convert_currency(amount, currency, self.base_currency)
            
            net = income_total - expense_total
            
            self.breakdown_tree.insert("", tk.END, values=(
                category, f"${income_total:.2f}", f"${expense_total:.2f}", f"${net:.2f}"
            ))

    def generate_chart(self):
        """Generate and display charts"""
        chart_type = self.chart_type_var.get()
        
        # Clear existing chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == "monthly_trends":
            self.create_monthly_trends_chart(ax)
        elif chart_type == "category_pie":
            self.create_category_pie_chart(ax)
        elif chart_type == "income_vs_expenses":
            self.create_income_vs_expenses_chart(ax)
        
        # Display chart
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_monthly_trends_chart(self, ax):
        """Create monthly income vs expenses trend chart"""
        # Get monthly data
        months = []
        income_data = []
        expense_data = []
        
        # Get last 12 months
        current_date = datetime.now()
        for i in range(12):
            month_date = current_date.replace(day=1) - timedelta(days=i*30)
            month_str = month_date.strftime("%Y-%m")
            months.insert(0, month_str)
            
            # Calculate income for this month
            month_income = 0
            income_data_file = self.load_json_file(self.income_file)
            for transaction in income_data_file:
                if transaction["date"].startswith(month_str):
                    amount = transaction["amount"]
                    currency = transaction["currency"]
                    month_income += self.convert_currency(amount, currency, self.base_currency)
            income_data.insert(0, month_income)
            
            # Calculate expenses for this month
            month_expenses = 0
            expenses_data_file = self.load_json_file(self.expenses_file)
            for transaction in expenses_data_file:
                if transaction["date"].startswith(month_str):
                    amount = transaction["amount"]
                    currency = transaction["currency"]
                    month_expenses += self.convert_currency(amount, currency, self.base_currency)
            expense_data.insert(0, month_expenses)
        
        # Create chart
        ax.plot(months, income_data, label="Income", marker='o')
        ax.plot(months, expense_data, label="Expenses", marker='s')
        ax.set_title("Monthly Income vs Expenses Trend")
        ax.set_xlabel("Month")
        ax.set_ylabel(f"Amount ({self.base_currency})")
        ax.legend()
        ax.tick_params(axis='x', rotation=45)

    def create_category_pie_chart(self, ax):
        """Create pie chart of expense categories"""
        categories = {}
        
        expenses_data = self.load_json_file(self.expenses_file)
        for transaction in expenses_data:
            category = transaction["category"]
            amount = transaction["amount"]
            currency = transaction["currency"]
            converted_amount = self.convert_currency(amount, currency, self.base_currency)
            categories[category] = categories.get(category, 0) + converted_amount
        
        if categories:
            labels = list(categories.keys())
            sizes = list(categories.values())
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title("Expense Categories Distribution")
        else:
            ax.text(0.5, 0.5, "No expense data available", ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Expense Categories Distribution")

    def create_income_vs_expenses_chart(self, ax):
        """Create bar chart comparing income vs expenses"""
        categories = set()
        
        # Get all categories
        income_data = self.load_json_file(self.income_file)
        for transaction in income_data:
            categories.add(transaction["category"])
        
        expenses_data = self.load_json_file(self.expenses_file)
        for transaction in expenses_data:
            categories.add(transaction["category"])
        
        categories = list(categories)
        income_data_chart = []
        expense_data_chart = []
        
        for category in categories:
            # Income for this category
            income_total = 0
            for transaction in income_data:
                if transaction["category"] == category:
                    amount = transaction["amount"]
                    currency = transaction["currency"]
                    income_total += self.convert_currency(amount, currency, self.base_currency)
            income_data_chart.append(income_total)
            
            # Expenses for this category
            expense_total = 0
            for transaction in expenses_data:
                if transaction["category"] == category:
                    amount = transaction["amount"]
                    currency = transaction["currency"]
                    expense_total += self.convert_currency(amount, currency, self.base_currency)
            expense_data_chart.append(expense_total)
        
        if categories:
            x = range(len(categories))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], income_data_chart, width, label='Income')
            ax.bar([i + width/2 for i in x], expense_data_chart, width, label='Expenses')
            
            ax.set_title("Income vs Expenses by Category")
            ax.set_xlabel("Categories")
            ax.set_ylabel(f"Amount ({self.base_currency})")
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45)
            ax.legend()
        else:
            ax.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax.transAxes)

    def delete_selected(self):
        """Delete selected transaction"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a row to delete")
            return
        
        transaction_id = float(sel[0])
        if messagebox.askyesno("Confirm", "Delete selected transaction?"):
            # Try to delete from both files
            income_data = self.load_json_file(self.income_file)
            income_data = [t for t in income_data if t["id"] != transaction_id]
            self.save_json_file(self.income_file, income_data)
            
            expenses_data = self.load_json_file(self.expenses_file)
            expenses_data = [t for t in expenses_data if t["id"] != transaction_id]
            self.save_json_file(self.expenses_file, expenses_data)
            
            self.refresh_data()
            self.clear_fields()

    def export_csv(self):
        """Export transactions to CSV"""
        try:
            with open("transactions_export.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "date", "type", "category", "description", "amount", "currency"])
                
                # Export income
                income_data = self.load_json_file(self.income_file)
                for transaction in income_data:
                    writer.writerow([
                        transaction["id"],
                        transaction["date"],
                        "income",
                        transaction["category"],
                        transaction["description"],
                        transaction["amount"],
                        transaction["currency"]
                    ])
                
                # Export expenses
                expenses_data = self.load_json_file(self.expenses_file)
                for transaction in expenses_data:
                    writer.writerow([
                        transaction["id"],
                        transaction["date"],
                        "expense",
                        transaction["category"],
                        transaction["description"],
                        transaction["amount"],
                        transaction["currency"]
                    ])
            
            messagebox.showinfo("Exported", "Exported to transactions_export.csv")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def clear_fields(self):
        """Clear input fields"""
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.category_var.set("")
        self.desc_var.set("")
        self.amount_var.set("")

    def on_select(self, event):
        """Handle tree selection"""
        sel = self.tree.selection()
        if not sel:
            return
        
        transaction_id = float(sel[0])
        
        # Try to get from income first
        income_data = self.load_json_file(self.income_file)
        transaction = None
        
        for t in income_data:
            if t["id"] == transaction_id:
                transaction = t
                break
        
        if not transaction:
            # Try expenses
            expenses_data = self.load_json_file(self.expenses_file)
            for t in expenses_data:
                if t["id"] == transaction_id:
                    transaction = t
                    break
        
        if transaction:
            self.date_var.set(transaction["date"])
            self.category_var.set(transaction["category"])
            self.desc_var.set(transaction["description"])
            self.amount_var.set(str(transaction["amount"]))
            self.currency_var.set(transaction["currency"])
            self.transaction_type_var.set(transaction["transaction_type"])

    def sort_by(self, col, descending):
        """Sort tree by column"""
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0]) if col == "amount" else t[0], reverse=descending)
        except Exception:
            data.sort(reverse=descending)
        
        for index, (val, k) in enumerate(data):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda c=col: self.sort_by(c, not descending))

    def on_currency_change(self, event=None):
        """Handle currency change"""
        self.current_currency = self.currency_var.get()
        self.refresh_data()

    def on_quit(self):
        """Clean up and quit"""
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalFinanceTracker(root)
    root.mainloop()