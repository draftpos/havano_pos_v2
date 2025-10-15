import frappe
from frappe import _
from havano_pos_integration.utils import create_response

@frappe.whitelist()
def update_item_price(item_code, price_list="Standard Selling", price_list_rate=0, name=None):
    """
    Update item price for a specific item and price list
    Expected parameters:
    - item_code: Item code to update price for
    - price_list: Price list name
    - price_list_rate: New price rate
    - name (optional): Specific Item Price document name to update
    """
    try:
        # Get parameters from request
        # data = frappe.form_dict
        
        
        
        item_code = item_code
        price_list = price_list or frappe.defaults.get_default("selling_price_list")
        price_list_rate = float(price_list_rate)
        item_price_name = name
        
        # Validate item exists
        if not frappe.db.exists("Item", item_code):
            create_response("404", f"Item {item_code} not found")
            return
            
        # Validate price list exists
        if not frappe.db.exists("Price List", price_list):
            create_response("404", f"Price List {price_list} not found")
            return
        
        # Check if Item Price document exists
        if item_price_name:
            # Update existing Item Price document
            if not frappe.db.exists("Item Price", item_price_name):
                create_response("404", f"Item Price {item_price_name} not found")
                return
                
            doc = frappe.get_doc("Item Price", item_price_name)
            doc.price_list_rate = price_list_rate
            doc.save()
            frappe.db.commit()
            
            create_response("200", f"Item Price {item_price_name} updated successfully", {
                "name": doc.name,
                "item_code": doc.item_code,
                "price_list": doc.price_list,
                "price_list_rate": doc.price_list_rate
            })
        else:
            # Find existing Item Price for this item and price list
            existing_price = frappe.get_value("Item Price", 
                {"item_code": item_code, "price_list": price_list}, 
                "name")
            
            if existing_price:
                # Update existing price
                doc = frappe.get_doc("Item Price", existing_price)
                doc.price_list_rate = price_list_rate
                doc.save()
                frappe.db.commit()
                
                create_response("200", f"Item Price updated successfully", {
                    "name": doc.name,
                    "item_code": doc.item_code,
                    "price_list": doc.price_list,
                    "price_list_rate": doc.price_list_rate
                })
            else:
                # Create new Item Price document
                doc = frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item_code,
                    "price_list": price_list,
                    "price_list_rate": price_list_rate
                })
                doc.insert()
                frappe.db.commit()
                
                create_response("201", f"Item Price created successfully", {
                    "name": doc.name,
                    "item_code": doc.item_code,
                    "price_list": doc.price_list,
                    "price_list_rate": doc.price_list_rate
                })
        
    except ValueError as e:
        create_response("400", f"Invalid price value: {str(e)}")
        return
    except Exception as e:
        create_response("500", f"Error updating item price: {str(e)}")
        frappe.log_error(message=str(e), title="Error updating item price")
        return  