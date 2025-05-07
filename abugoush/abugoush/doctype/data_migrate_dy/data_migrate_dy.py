# Copyright (c) 2025, abugoush and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests

class DataMigrateDY(Document):
    pass

def get_old_data(url, doctype, api_key, api_secret, fields):
    if not api_key or not api_secret:
        return None, "❌ API key or secret is empty"

    headers = {
        "Authorization": f"token {api_key}:{api_secret}"
    }
    fields_param = str(fields).replace("'", '"')  
    full_url = f"{url}/api/resource/{doctype}?limit_page_length=1000&fields={fields_param}"

    response = requests.get(full_url, headers=headers)
    if response.status_code != 200:
        return None, f"Error: {response.status_code} - {response.text}"

    return response.json().get("data", []), "Success"

@frappe.whitelist()
def transfer_data(docname):
    doc = frappe.get_doc("Data Migrate DY", docname)

    fields = []
    for row in doc.field_map:
        if row.source_field:
            fields.append(row.source_field)

    if not fields:
        doc.log = "❌ No fields mapped in Field Map table"
        doc.save()
        frappe.msgprint(doc.log)
        return

    data, status = get_old_data(doc.old_erp_url, doc.doctype_to_pull, doc.api_key, doc.api_secret, fields)

    if status != "Success":
        doc.log = f"❌ FAILD GET DATA : {status}"
        doc.save()
        frappe.msgprint(doc.log)
        return

    if not data:
        doc.log = "❌ THERE IS NO DATA TO TRANSFER"
        doc.save()
        frappe.msgprint(doc.log)
        return

    count = 0
    skipped = 0  
    for row in data:
        try:
            filters = {}
            for map_row in doc.field_map:
                if map_row.source_field and map_row.target_field:
                    filters[map_row.target_field] = row.get(map_row.source_field)

            if frappe.db.exists(doc.target_doctype, filters):
                skipped += 1
                frappe.log_error(
                    title="Skipped duplicate",
                    message=f"Duplicate data detected and skipped:\n{frappe.as_json(row)}"
)
                continue

            new_doc = frappe.new_doc(doc.target_doctype)
            for map_row in doc.field_map:
                if map_row.source_field and map_row.target_field:
                    new_doc.set(map_row.target_field, row.get(map_row.source_field))
            new_doc.insert()
            count += 1

        except Exception as e:
            frappe.log_error(f"Error in row: {row}\n{str(e)}")
            doc.log = f"❌ FAILED TO TRANSFER DATA: {str(e)}"
            doc.save()
            frappe.msgprint(doc.log)
            return

    if skipped > 0:
        doc.log = f"✅ DONE {count} from {doc.doctype_to_pull} to {doc.target_doctype}. ⚠️ Skipped {skipped} due to duplicates."
    else:
        doc.log = f"✅ DONE {count} from {doc.doctype_to_pull} to {doc.target_doctype}."
    doc.save()
    frappe.msgprint(doc.log)

@frappe.whitelist()
def test_connection(old_erp_url, doctype_to_pull, api_key, api_secret):
    headers = {
        "Authorization": f"token {api_key}:{api_secret}"
    }
    try:
        test_url = f"{old_erp_url}/api/resource/{doctype_to_pull}?limit=1"
        response = requests.get(test_url, headers=headers)
        if response.status_code == 200:
            return "✅ Connection successful with old ERPNext system"
        else:
            return f"❌ Connection failed: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
