from openpyxl import load_workbook

from utilities import *


def validate_file(invoice_path)
    facility = get_facility(invoice_path)
    pharmacy, facility_pharmacy_map = get_pharmacy(facility)
    invoice_reader_settings = get_reader_settings(facility_pharmacy_map)

    if not invoice_reader_settings:
        raise exception("Reader setting is not available")

    # download invoice
    invoice_path = get_s3_client().download_file(get_s3_bucket(), invoice_path)

    source = 's3'
    invoice_dt = datetime.now()

    # parse invoice
    wb = load_workbook(invoice_path)
    sheet_name = wb[0]
    if not invoice_reader_settings.sheet_name:
        sheet_name = wb.column_names[invoice_reader_settings.sheet_name]

    if not sheet_name:
        raise exception(String.Format("Required Sheet '{0}' not found.", sheetName));

    ws = wb[sheet_name]
    # get meta info from [pharmacy_invoice_reader_settings]
    start_index = invoice_reader_settings.header_row_index + invoice_reader_settings.skip_rows_after_header + 1
    size = ws.rows - invoice_reader_settings.skip_ending_rows

    nrows = get_valid_rows_count(ws)

    data = []
    # validate each row using field validator
    for row in range(1, nrows):
        # country = sheet.cell(row+1, col).value
        if is_valid(row):
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
        result.append(record)

    sql = '''
        INSERT INTO [Ancillary_data_warehouse].[dbo].[pharmacy_invoices](
            [invoice_batch_id],
            [pharmacy_id],
            [facility_id],
            [payer_group_id],
            [invoice_dt],
            [first_nm],
            [last_nm],
            [ssn],
            [dob],
            [gender],
            [dispense_dt],
            [product_category],
            [drug_nm],
            [doctor],
            [rx_nbr],
            [ndc],
            [reject_cd],
            [quantity],
            [days_supplied],
            [charge_amt],
            [copay_amt],
            [copay_flg],
            [census_match_cd],
            [status_cd],
            [charge_confirmed_flg],
            [duplicate_flg],
            [note],
            [request_credit_flg],
            [credit_request_dt],
            [credit_request_cd],
            [days_overbilled],
        ) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    '''
    # bulk insert
    cursor.executemany(sql, result)
    cursor.commit()
    
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

    return record
