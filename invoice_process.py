from openpyxl import load_workbook

from utilities import *


def validate_file(invoice_path):
    facility = get_facility(invoice_path)
    source = get_source(invoice_path)
    facility_pharmacy_map = get_pharmacy(facility)
    pharmacy = facility_pharmacy_map.pharmacy
    invoice_reader_settings = get_reader_settings(pharmacy, source)

    if not invoice_reader_settings:
        raise exception("Reader setting is not available")

    # download invoice
    # invoice_path = get_s3_client().download_file(get_s3_bucket(), invoice_path)

    invoice_dt = datetime.datetime.now().date()

    # parse invoice
    wb = load_workbook(invoice_path)

    try:
        sheet_name = invoice_reader_settings.sheet_name or wb.sheetnames[0]

        ws = wb[sheet_name]
    except Exception as e:
        raise exception(f"Required Sheet '{sheetName}' not found.");

    # get meta info from [pharmacy_invoice_reader_settings]
    start_index = invoice_reader_settings.header_row_index + invoice_reader_settings.skip_rows_after_header + 1
    nrows = get_valid_rows_count(ws) - invoice_reader_settings.skip_ending_rows

    data = []
    # validate each row using field validator
    for row in range(1, nrows):
        # country = sheet.cell(row+1, col).value
        if is_valid_row(row):
            data.append(row)

    if nrows != len(data):
        raise exception("The file is invalid.")

    return facility_pharmacy_map, invoice_reader_settings, data


def process_invoice(facility_pharmacy_map, invoice_reader_settings, invoice_data, cursor):
    # create a log
    invoice_batch_log_id = start_batch_logging(facility_pharmacy_map, invoice_dt, source)
    pharmacy_id = facility_pharmacy_map['pharmacy_id']
    facility_id = facility_pharmacy_map['facility_id']
    payer_group_id = get_payer_group(pharmacy_id, source)
    process_invoice_func = getattr(globals(), f'_process_row_{pharmacy}')

    result = []
    for row in invoice_data:
        record = process_invoice_func(row)
    
    res = stop_batch_logging(invoice_batch_log_id)

    return res


def _process_row_speciality_rx(row):
    first_nm = get_first_name(row['patient'])
    last_nm = get_last_name(row['patient'])
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
    }

    pharmacy_invoice = PharmacyInvoice(**record)
    session.add(pharmacy_invoice)
    session.commit()


def _process_row_pharmscripts(row):
    first_nm = get_first_name(row['patient'])
    last_nm = get_last_name(row['patient'])
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
    }

    pharmacy_invoice = PharmacyInvoice(**record)
    session.add(pharmacy_invoice)
    session.commit()
