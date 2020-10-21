import math
import datetime

from openpyxl import load_workbook

from utilities import *


def validate_file(invoice_path):
    facility = get_facility(invoice_path)
    source = get_source(invoice_path)
    facility_pharmacy_map = get_pharmacy(facility)
    pharmacy = facility_pharmacy_map.pharmacy
    invoice_reader_settings = get_reader_settings(pharmacy, source)

    if not invoice_reader_settings:
        raise Exception("Reader setting is not available")

    # download invoice
    file_name = 'invoice.xlsx'
    invoice_path = get_s3_client().download_file(get_s3_bucket(), invoice_path, file_name)

    invoice_dt = datetime.datetime.now().date()

    # parse invoice
    wb = load_workbook(file_name)

    try:
        sheet_name = invoice_reader_settings.sheet_name or wb.sheetnames[0]

        ws = wb[sheet_name]
    except Exception as e:
        raise Exception(f"Required Sheet '{sheetName}' not found.");

    # get meta info from [pharmacy_invoice_reader_settings]
    start_index = invoice_reader_settings.header_row_index + invoice_reader_settings.skip_rows_after_header + 1
    nrows = get_valid_rows_count(ws) - invoice_reader_settings.skip_ending_rows

    header = [ii.value for ii in ws[invoice_reader_settings.header_row_index+1]]

    for field in invoice_reader_settings.raw_invoice_fields:
        if field.sheet_column_name not in header and not field.is_optional:
            raise Exception(f"Sheet Column '{field.sheet_column_name}' not found in invoice file")

    data = []
    # validate each row using field validator
    for row_idx in range(start_index, nrows):
        cleaned_data = validate_row(invoice_reader_settings.raw_invoice_fields, header, ws[row_idx+1], row_idx+1)
        if not cleaned_data:
            raise Exception("The file is invalid.")
        data.append(cleaned_data)

    return facility_pharmacy_map, invoice_dt, source, data


def process_invoice(facility_pharmacy_map, invoice_dt, source, invoice_data):
    # create a log
    source_id = source.id if source else 0
    source_name = source.source_nm.lower() if source else 'general'
    invoice_batch_log_id = start_batch_logging(facility_pharmacy_map, invoice_dt, source_id)
    pharmacy_name = facility_pharmacy_map.pharmacy.pharmacy_nm.lower().replace(' ', '_')
    pharmacy_id = facility_pharmacy_map.pharmacy.id
    facility_id = facility_pharmacy_map.facility.id
    process_invoice_func = globals().get(f'_process_row_{pharmacy_name}_{source_name}')

    process_invoice_func(
        invoice_data,
        invoice_batch_log_id,
        pharmacy_id,
        facility_id,
        invoice_dt,
        source_id
    )
    
    res = stop_batch_logging(invoice_batch_log_id)

    return res


def _process_row_speciality_rx_email(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['patient'])
        last_nm = get_last_name(row['patient'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)
        ssn = row['ssn_no'][:3]+row['ssn_no'][4:6]+row['ssn_no'][7:11] if row['ssn_no'][0] != '_' else 0

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': ssn,
            'dob': None,
            'gender': None,
            'dispense_dt': row['dispdt'],
            'product_category': row['rx_otc'],
            'drug_nm': row['drug'],
            'doctor': None,
            'rx_nbr': row['rx_no'],
            'ndc': row['ndc'],
            'reject_cd': None,
            'quantity': row['qty'],
            'days_supplied': row['ds'],
            'charge_amt': row['billamt'],
            'copay_amt': None,
            'copay_flg': 'Y' if row['copay'].upper() == 'COPAY' else None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': row['comment'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }

        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_speciality_rx_portal(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['resident'])
        last_nm = get_last_name(row['resident'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)
        ssn = row['ssn_no'][:3]+row['ssn_no'][4:6]+row['ssn_no'][7:11] if row['ssn_no'][0] != '_' else 0

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': None,
            'dob': None,
            'gender': None,
            'dispense_dt': row['dispensed'],
            'product_category': row['rx_type'],
            'drug_nm': row['drug_nm'],
            'doctor': None,
            'rx_nbr': row['rx_no'],
            'ndc': None,
            'reject_cd': None,
            'quantity': row['quantity'],
            'days_supplied': row['days_supply'],
            'charge_amt': row['amount'],
            'copay_amt': None,
            'copay_flg': 'Y' if row['is_a_copay'].upper() == 'COPAY' else None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': row['billing_comment'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }

        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_pharmscripts_portal(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['patient_nm'])
        last_nm = get_last_name(row['patient_nm'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': row['ssn'],
            'dob': None,
            'gender': 'M' if row['b_or_g'] == 'B' else 'F' if row['b_or_g'] == 'G' else None,
            'dispense_dt': row['disp_dt'],
            'product_category': row['rx_type'],
            'drug_nm': row['drug'],
            'doctor': row['physician'],
            'rx_nbr': row['rx_no'],
            'ndc': row['ndc'],
            'reject_cd': None,
            'quantity': row['qty'],
            'days_supplied': row['ds'],
            'charge_amt': row['bill'],
            'copay_amt': None,
            'copay_flg': 'Y' if row['copay'].upper() == 'Y' else None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': True,
            'note': row['billing_comment'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None
        }

        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_pharmscripts_email(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['patient'])
        last_nm = get_last_name(row['patient'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': row['ssn'],
            'dob': None,
            'gender': 'M' if row['b_g'] == 'B' else 'F' if row['b_g'] == 'G' else None,
            'dispense_dt': row['disp_dt'],
            'product_category': row['otc_rx'],
            'drug_nm': row['drug'],
            'doctor': row['physician'],
            'rx_nbr': row['rx_no'],
            'ndc': row['ndc'],
            'reject_cd': None,
            'quantity': row['tot_qty_disp'],
            'days_supplied': row['ds'],
            'charge_amt': row['tot_bill_amt'],
            'copay_amt': None,
            'copay_flg': 'Y' if row['is_a_copay'].upper() == 'Y' else None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': None,
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }
        import pdb; pdb.set_trace()
        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_geriscript_general(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['full_nm'])
        last_nm = get_last_name(row['full_nm'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)
        ssn = row['ssn'][:3]+row['ssn'][4:6]+row['ssn'][7:11] if row['ssn'][0] != '_' else ''

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': ssn,
            'dob': row['birth_date'],
            'gender': row['sex'],
            'dispense_dt': row['dispense_dt'],
            'product_category': row['rx_otc'],
            'drug_nm': row['drug_label_nm'],
            'doctor': row['doctor'],
            'rx_nbr': row['rx_no'],
            'ndc': row['ndc'],
            'reject_cd': None,
            'quantity': row['qty'],
            'days_supplied': row['days_supply'],
            'charge_amt': row['bill_amt'],
            'copay_amt': row['copay_amt'],
            'copay_flg': 'Y' if row['copay_amt'] > 0 else None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': row['billing_comment'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }
        import pdb; pdb.set_trace()
        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_medwiz_general(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['name'])
        last_nm = get_last_name(row['name'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': None,
            'dob': None,
            'gender': None,
            'dispense_dt': row['dispense_date'],
            'product_category': row['distribution_code'],
            'drug_nm': row['description'],
            'doctor': None,
            'rx_nbr': row['rx_no'],
            'ndc': row['ndc'],
            'reject_cd': None,
            'quantity': row['qty'],
            'days_supplied': row['days_supply'],
            'charge_amt': row['amount'],
            'copay_amt': None,
            'copay_flg': 'Y' if row['copay'].upper() == 'COPAY' else None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': row['billing_comment'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }
        import pdb; pdb.set_trace()
        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_omnicare_general(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = row['patient_first_nm']
        last_nm = row['patient_last_nm']
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)
        ssn = row['patient_ssn'][:3]+row['patient_ssn'][4:6]+row['patient_ssn'][7:11] if row['patient_ssn'][0] != '_' else ''

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': ssn,
            'dob': None,
            'gender': None,
            'dispense_dt': row['transaction_dt'],
            'product_category': row['inventory_category'],
            'drug_nm': row['description'],
            'doctor': row['physician'],
            'rx_nbr': row['rx'],
            'ndc': row['ndc'],
            'reject_cd': row['reject_codes'],
            'quantity': row['qty'],
            'days_supplied': row['days_supply'],
            'charge_amt': row['amount'],
            'copay_amt': row['amount'] if row['copay'].upper() == 'COPAY' else None,
            'copay_flg': 'Y' if row['copay'].upper() == 'COPAY' else None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': row['statement_note'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }
        import pdb; pdb.set_trace()
        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_pharmerica_email(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['resident_nm'])
        last_nm = get_last_name(row['resident_nm'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)
        ssn = row['res_ssn'][:3]+row['res_ssn'][4:6]+row['res_ssn'][7:11] if row['res_ssn'][0] != '_' else ''

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': ssn,
            'dob': None,
            'gender': None,
            'dispense_dt': row['service_dt'],
            'product_category': ((row['product_category'] or '') + (row['sales_type'] or '')) or None,
            'drug_nm': row['trans_desc'],
            'doctor': row['doctor_nm'],
            'rx_nbr': row['rx_nbr'],
            'ndc': row['ndc_nbr'],
            'reject_cd': None,
            'quantity': row['quantity'],
            'days_supplied': row['days_supply'],
            'charge_amt': row['amount_due'],
            'copay_amt': None,
            'copay_flg': None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': row['task_manager_notes'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }
        import pdb; pdb.set_trace()
        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)


def _process_row_pharmerica_portal(invoice_data, invoice_batch_log_id, pharmacy_id, facility_id, invoice_dt, source):
    for row in invoice_data:
        first_nm = get_first_name(row['resident_nm'])
        last_nm = get_last_name(row['resident_nm'])
        payer_group_id = get_payer_group(pharmacy_id, row['inv_grp'], source)
        ssn = row['res_ssn'][:3]+row['res_ssn'][4:6]+row['res_ssn'][7:11] if row['res_ssn'][0] != '_' else ''

        record = {
            'invoice_batch_id': invoice_batch_log_id,
            'pharmacy_id': pharmacy_id,
            'facility_id': facility_id,
            'payer_group_id': payer_group_id,
            'invoice_dt': invoice_dt,
            'first_nm': first_nm,
            'last_nm': last_nm,
            'ssn': ssn,
            'dob': None,
            'gender': None,
            'dispense_dt': row['service_dt'],
            'product_category': row['product_category'],
            'drug_nm': row['trans_desc'],
            'doctor': row['doctor_nm'],
            'rx_nbr': math.floor(row['rx_nbr']),
            'ndc': row['ndc_nbr'],
            'reject_cd': None,
            'quantity': row['quantity'],
            'days_supplied': row['days_supply'],
            'charge_amt': row['trans_amount'],
            'copay_amt': None,
            'copay_flg': None,
            'census_match_cd': None,
            'status_cd': None,
            'charge_confirmed_flg': None,
            'duplicate_flg': None,
            'note': row['task_manager_notes'],
            'request_credit_flg': None,
            'credit_request_dt': None,
            'credit_request_cd': None,
            'days_overbilled': None,
            'duplicate_flg': True
        }
        import pdb; pdb.set_trace()
        pharmacy_invoice = PharmacyInvoice(**record)
        session.add(pharmacy_invoice)
        session.commit()

    return len(invoice_data)
