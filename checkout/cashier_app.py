import tkinter as tk
from tkinter import ttk
import psycopg2
import tkinter.messagebox
import re # Not using this yet

class GroceryStore:
    def __init__(self, root):
        self.root = root
        self.create_table()
        self.create_cart()
        self.create_product_entry()
        self.create_buttons()

    def create_table(self):
        # Create scroll bars
        self.xscroll = ttk.Scrollbar(self.root, orient="horizontal")
        self.yscroll = ttk.Scrollbar(self.root, orient="vertical")

        # Configure style
        style = ttk.Style(self.root)
        style.configure('Treeview', font=(None, 14), rowheight=27)
        style.configure('Treeview.Heading', font=(None, 16))
        style.configure('Treeview.Row.highlight', background='blue')

        # Create record table
        self.table = ttk.Treeview(self.root)

        # Configure scroll bar
        self.xscroll.configure(command=self.table.xview)
        self.yscroll.configure(command=self.table.yview)
        self.table.config(
            yscrollcommand=self.yscroll.set,
            xscrollcommand=self.xscroll.set,
            selectmode="extended",
        )

        # Column configurations
        columns = (
            "Product ID", "Product Name", "Category", "Brand", "Price",
            "Stock Quantity", "Supplier", "Expiry Date", "Discount", "Location",
        )
        self.table["columns"] = columns

        # Add column headings
        for col in columns:
            self.table.heading(col, text=col, anchor=tk.CENTER)

        self.populate_table()

        # Display headings
        self.table["show"] = "headings"

        # Place table and scroll bars to fill the entire window
        self.table.pack(fill="both", expand=True)
        self.xscroll.pack(side="bottom", fill="x")
        self.yscroll.pack(side="right", fill="y")

        # Add search functionality
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(self.root, textvariable=self.search_var)
        search_button = ttk.Button(self.root, text="Search", command=self.search_table)

        search_entry.pack(pady=10)
        search_button.pack()

    def populate_table(self):
        # Clear existing items
        self.table.delete(*self.table.get_children())

        # Create count variable for striped rows
        count = 0

        # Create row stripe tags for alternative row colors
        self.table.tag_configure("oddrow", background="#D9D9D6")
        self.table.tag_configure("evenrow", background="white")

        # Connect to PostgreSQL
        connection = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="sigma204"
        )

        # Use the connection to execute SQL queries
        with connection.cursor() as cursor:
            # Example query: select all rows from the "inventory" table
            cursor.execute("SELECT * FROM inventory")
            data = cursor.fetchall()

            # Loop through data to add to the table
            for record in data:
                if count % 2 == 0:
                    self.table.insert(
                        parent="",
                        index="end",
                        iid=count,
                        text=count,
                        values=record,
                        tags=("evenrow"),
                    )
                else:
                    self.table.insert(
                        parent="",
                        index="end",
                        iid=count,
                        text=count,
                        values=record,
                        tags=("oddrow"),
                    )
                count += 1

        # Close the database connection
        connection.close()
        
    def search_table(self):
        # Get the search term
        search_term = self.search_var.get().lower()

        # Clear previous search highlights
        for row in self.table.get_children():
            for col in self.table["columns"]:
                self.table.tag_configure(f"{row}_{col}", background="white")

        # Highlight rows that match the search term and bring the first match into view
        first_match_row = None
        for row in self.table.get_children():
            values = self.table.item(row, 'values')
            if any(search_term in str(value).lower() for value in values):
                first_match_row = row
                for col, value in zip(self.table["columns"], values):
                    self.table.tag_configure(f"{row}_{col}", background="blue")  # Highlight each cell

        # Bring the first match into view
        if first_match_row:
            self.table.see(first_match_row)

                
    def create_cart(self):
        self.cart_label = tk.Label(self.root, text="Shopping Cart", font=("Helvetica", 16, "bold"))
        self.cart_label.pack(pady=10)

        self.cart_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, width=50, height=5)
        self.cart_listbox.pack(pady=10)


    def create_product_entry(self):
        self.product_entry_label = tk.Label(self.root, text="Enter Product ID:")
        self.product_entry_label.pack()

        self.product_entry = ttk.Entry(self.root)
        self.product_entry.pack(pady=5)

    def create_buttons(self):
        self.add_to_cart_button = ttk.Button(self.root, text="Add to Cart", command=self.add_to_cart)
        self.add_to_cart_button.pack(pady=5)

        self.checkout_button = ttk.Button(self.root, text="Checkout", command=self.checkout)
        self.checkout_button.pack(pady=10)

    def add_to_cart(self):
        product_id = self.product_entry.get()
        quantity = 1  # Default quantity is 1 if not specified

        # Check if a quantity is specified in the product ID (e.g., "123x2" for Product ID 123 and quantity 2)
        if 'x' in product_id:
            parts = product_id.split('x', 1)
            product_id = parts[0]
            try:
                quantity = int(parts[1])
            except ValueError:
                tk.messagebox.showinfo("Invalid Quantity", "Invalid quantity specified. Using default quantity 1.")

        if product_id:
            found = False
            for item_id in self.table.get_children():
                values = self.table.item(item_id, 'values')
                if values and values[0] == product_id:
                    found = True
                    product_name = values[1]
                    self.cart_listbox.insert(tk.END, f"{product_name} (ID: {product_id}) - Quantity: {quantity}")
                    self.product_entry.delete(0, tk.END)
                    break

            if not found:
                tk.messagebox.showinfo("Product Not Found", f"No product found with ID: {product_id}")
        else:
            tk.messagebox.showinfo("Empty Product ID", "Please enter a valid product ID.")



    def checkout(self):
        selected_items = self.cart_listbox.get(0, tk.END)
        if selected_items:
            total_price = 0.0
            receipt_content = "Items in Cart:\n"

            # Connect to PostgreSQL for database update
            connection = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="sigma204"
            )

            with connection.cursor() as cursor:
                for item in selected_items:
                    # Extract product ID and quantity from the cart item
                    match = re.search(r'\(ID: (\d+)\) - Quantity: (\d+)', item)
                    if match:
                        product_id, quantity = match.groups()

                        # Fetch the current stock quantity from the database
                        cursor.execute("SELECT stock_quantity FROM inventory WHERE product_id = %s", (product_id,))
                        current_quantity = cursor.fetchone()[0]

                        # Update the stock quantity in the database
                        new_quantity = current_quantity - int(quantity)
                        cursor.execute("UPDATE inventory SET stock_quantity = %s WHERE product_id = %s", (new_quantity, product_id))

                        # Fetch the price of the product from the database
                        cursor.execute("SELECT price FROM inventory WHERE product_id = %s", (product_id,))
                        raw_price = cursor.fetchone()[0]
                        price = float(raw_price.replace('$', ''))  # Remove the dollar sign and convert to float

                        total_price += int(quantity) * price

                        receipt_content += f"{item}\n"

            # Commit the changes to the database
            connection.commit()

            # Close the database connection
            connection.close()
            
            # Refresh the table to reflect the updated data
            self.populate_table()

            receipt_content += f"\nTotal Price: ${total_price:.2f}"
            receipt_content += "\n\nCheckout Successful!"

            # Display the checkout message in a messagebox
            checkout_message = f"Items in Cart:\n{', '.join(selected_items)}\n\nTotal Price: ${total_price:.2f}\n\nCheckout Successful!"
            tk.messagebox.showinfo("Checkout", checkout_message)

            # Open a new window for displaying the receipt
            receipt_window = tk.Toplevel(self.root)
            receipt_window.title("Receipt")

            # Create a Text widget for the receipt
            receipt_text = tk.Text(receipt_window, wrap=tk.WORD, width=60, height=20)
            receipt_text.pack(pady=10)
            receipt_text.insert(tk.END, receipt_content)

            # Add a button to close the receipt window
            close_button = ttk.Button(receipt_window, text="Close", command=receipt_window.destroy)
            close_button.pack(pady=10)

            # Clear the shopping cart
            self.cart_listbox.delete(0, tk.END)
        else:
            tk.messagebox.showinfo("Empty Cart", "Your cart is empty. Please add items before checking out.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GroceryStore(root)
    root.geometry("1000x500")  # Set the initial size of the window
    root.mainloop()
