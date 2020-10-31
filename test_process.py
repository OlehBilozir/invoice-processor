import invoice_process

from utilities import *


def test_get_first_name_0():
    assert get_first_name('John,Doe') == 'John'


def test_get_first_name_1():
    assert get_first_name('John') == 'John'


def test_get_last_name_0():
    assert get_last_name('John,Doe') == 'Doe'


def test_get_last_name_1():
    assert get_last_name('John') == None


def test_validate_field_int():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='int',
        field_validations='',
        is_optional='',
    )

    val = '1234'

    is_valid, msg = validate_field(field, val)

    assert is_valid == True


def test_validate_field_char():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='char',
        field_validations='',
        is_optional='',
    )

    val = 'A'

    is_valid, msg = validate_field(field, val)

    assert is_valid == True


def test_validate_field_decimal():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='decimal',
        field_validations='',
        is_optional='',
    )

    val = '$1234.2156'

    is_valid, msg = validate_field(field, val)

    assert is_valid == True


def test_validate_field_date():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='date',
        field_validations='',
        is_optional='',
    )

    val = '12/14/2020'

    is_valid, msg = validate_field(field, val)

    assert is_valid is not None


def test_validate_field_string():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='string',
        field_validations='',
        is_optional='',
    )

    val = '1234abcd'

    is_valid, msg = validate_field(field, val)

    assert is_valid == True


def test_validate_field_string_50():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='string',
        field_validations='MaxLength50',
        is_optional='',
    )

    val = '1234abcd'

    is_valid, msg = validate_field(field, val)

    assert is_valid == True


def test_validate_field_string_50_1():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='string',
        field_validations='MaxLength50',
        is_optional='',
    )

    val = '='*51

    is_valid, msg = validate_field(field, val)

    assert is_valid == False


def test_validate_field_string_Ssn():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='string',
        field_validations='Ssn',
        is_optional='',
    )

    val = '321-32-1245'

    is_valid, msg = validate_field(field, val)

    assert is_valid is not None


def test_validate_field_string_Name():
    field = RawInvoiceField(
        sheet_column_name='Test',
        field_type='string',
        field_validations='Name',
        is_optional='',
    )

    val = 'John,Doe'

    is_valid, msg = validate_field(field, val)

    assert is_valid == True


def test_pharmscripts_portal():
    file_name = '2020/10/Deer Meadows NEW/Portal/Pharmscripts Portal Invoice.xlsx'

    result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
    assert result == True

    result = invoice_process.process_invoice(invoice_info, log_file, True)
    assert result == True

    row = invoice_info[3][0]
    pharmacy_id = invoice_info[0].pharmacy.id
    facility_id = invoice_info[0].facility.id

    first_nm = get_first_name(row['patient_nm'])
    last_nm = get_last_name(row['patient_nm'])

    record = session.query(PharmacyInvoice).filter(
                PharmacyInvoice.pharmacy_id==pharmacy_id,
                PharmacyInvoice.facility_id==facility_id,
                PharmacyInvoice.first_nm==first_nm,
                PharmacyInvoice.last_nm==last_nm,
                PharmacyInvoice.ssn==row['ssn'],
                PharmacyInvoice.dispense_dt==row['disp_dt'],
                PharmacyInvoice.product_category==row['rx_type'],
                PharmacyInvoice.drug_nm==row['drug'],
                PharmacyInvoice.doctor==row['physician'],
                PharmacyInvoice.rx_nbr==row['rx_no'],
                PharmacyInvoice.ndc==row['ndc'],
                PharmacyInvoice.quantity==row['qty'],
                PharmacyInvoice.days_supplied==row['ds'],
                PharmacyInvoice.charge_amt==row['bill'],
                PharmacyInvoice.note==row['billing_comment'],
                PharmacyInvoice.duplicate_flg==1
            ).first()

    assert record is not None


def test_pharmscripts_portal_missing_name():
    file_name = '2020/10/Deer Meadows NEW/Portal/Pharmscripts Portal Invoice - missing columns.xlsx'

    result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
    assert result == False


def test_pharmscripts_email_invalid_bed():
    file_name = '2020/10/Deer Meadows NEW/Email/Pharmscripts Emailed Invoice - invalid bed.xlsx'

    result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
    assert result == False


# -- invalid Bed
# def test_pharmscripts_email():
#     file_name = '2020/10/Deer Meadows NEW/Email/Pharmscripts Emailed Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

#     row = invoice_info[3][0]
#     pharmacy_id = invoice_info[0].pharmacy.id
#     facility_id = invoice_info[0].facility.id

#     first_nm = get_first_name(row['patient_nm'])
#     last_nm = get_last_name(row['patient_nm'])

#     record = session.query(PharmacyInvoice).filter(
#                 PharmacyInvoice.pharmacy_id==pharmacy_id,
#                 PharmacyInvoice.facility_id==facility_id,
#                 PharmacyInvoice.first_nm==first_nm,
#                 PharmacyInvoice.last_nm==last_nm,
#                 PharmacyInvoice.ssn==row['ssn'],
#                 PharmacyInvoice.dispense_dt==row['disp_dt'],
#                 PharmacyInvoice.product_category==row['rx_type'],
#                 PharmacyInvoice.drug_nm==row['drug'],
#                 PharmacyInvoice.doctor==row['physician'],
#                 PharmacyInvoice.rx_nbr==row['rx_no'],
#                 PharmacyInvoice.ndc==row['ndc'],
#                 PharmacyInvoice.quantity==row['qty'],
#                 PharmacyInvoice.days_supplied==row['ds'],
#                 PharmacyInvoice.charge_amt==row['bill'],
#                 PharmacyInvoice.note==row['billing_comment'],
#                 PharmacyInvoice.duplicate_flg==1
#             ).first()

#     assert record is not None


# def test_process_row_omnicare_general():
#     file_name = '2020/10/Beacon/General/Omnicare Email.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

#     row = invoice_info[3][0]
#     pharmacy_id = invoice_info[0].pharmacy.id
#     facility_id = invoice_info[0].facility.id

#     first_nm = row['patient_first_nm']
#     last_nm = row['patient_last_nm']
#     ssn = row['patient_ssn'][:3]+row['patient_ssn'][4:6]+row['patient_ssn'][7:11] if row['patient_ssn'] and row['patient_ssn'][0] != '_' else ''

#     record = session.query(PharmacyInvoice).filter(
#                 PharmacyInvoice.pharmacy_id==pharmacy_id,
#                 PharmacyInvoice.facility_id==facility_id,
#                 PharmacyInvoice.first_nm==first_nm,
#                 PharmacyInvoice.last_nm==last_nm,
#                 PharmacyInvoice.ssn==ssn,
#                 PharmacyInvoice.dispense_dt==row['transaction_dt'],
#                 PharmacyInvoice.product_category==row['inventory_category'],
#                 PharmacyInvoice.drug_nm==row['description'],
#                 PharmacyInvoice.doctor==row['physician'],
#                 PharmacyInvoice.rx_nbr==row['rx'],
#                 PharmacyInvoice.ndc==row['ndc'],
#                 PharmacyInvoice.reject_cd==row['reject_codes'],
#                 PharmacyInvoice.quantity==row['qty'],
#                 PharmacyInvoice.days_supplied==row['days_supply'],
#                 PharmacyInvoice.charge_amt==row['amount'],
#                 PharmacyInvoice.duplicate_flg==1,
#                 PharmacyInvoice.note==row['statement_note']
#             ).first()

#     assert record is not None


# def test_process_row_omnicare_general_invalid_amount():
#     file_name = '2020/10/Beacon/General/Omnicare Email - invalid amount.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == False


# def test_pharmerica_email():
#     file_name = '2020/10/Ridgewood/Email/Cartersville May Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

#     row = invoice_info[3][0]
#     pharmacy_id = invoice_info[0].pharmacy.id
#     facility_id = invoice_info[0].facility.id

#     first_nm = get_first_name(row['patient_nm'])
#     last_nm = get_last_name(row['patient_nm'])

#     record = session.query(PharmacyInvoice).filter(
#                 PharmacyInvoice.pharmacy_id==pharmacy_id,
#                 PharmacyInvoice.facility_id==facility_id,
#                 PharmacyInvoice.first_nm==first_nm,
#                 PharmacyInvoice.last_nm==last_nm,
#                 PharmacyInvoice.ssn==row['ssn'],
#                 PharmacyInvoice.dispense_dt==row['disp_dt'],
#                 PharmacyInvoice.product_category==row['rx_type'],
#                 PharmacyInvoice.drug_nm==row['drug'],
#                 PharmacyInvoice.doctor==row['physician'],
#                 PharmacyInvoice.rx_nbr==row['rx_no'],
#                 PharmacyInvoice.ndc==row['ndc'],
#                 PharmacyInvoice.quantity==row['qty'],
#                 PharmacyInvoice.days_supplied==row['ds'],
#                 PharmacyInvoice.charge_amt==row['bill'],
#                 PharmacyInvoice.note==row['billing_comment'],
#                 PharmacyInvoice.duplicate_flg==1
#             ).first()

#     assert record is not None


# def test_pharmerica_portal():
#     file_name = '2020/10/Ridgewood/Portal/Pharmerica Portal Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

#     row = invoice_info[3][0]
#     pharmacy_id = invoice_info[0].pharmacy.id
#     facility_id = invoice_info[0].facility.id

#     first_nm = get_first_name(row['patient_nm'])
#     last_nm = get_last_name(row['patient_nm'])

#     record = session.query(PharmacyInvoice).filter(
#                 PharmacyInvoice.pharmacy_id==pharmacy_id,
#                 PharmacyInvoice.facility_id==facility_id,
#                 PharmacyInvoice.first_nm==first_nm,
#                 PharmacyInvoice.last_nm==last_nm,
#                 PharmacyInvoice.ssn==row['ssn'],
#                 PharmacyInvoice.dispense_dt==row['disp_dt'],
#                 PharmacyInvoice.product_category==row['rx_type'],
#                 PharmacyInvoice.drug_nm==row['drug'],
#                 PharmacyInvoice.doctor==row['physician'],
#                 PharmacyInvoice.rx_nbr==row['rx_no'],
#                 PharmacyInvoice.ndc==row['ndc'],
#                 PharmacyInvoice.quantity==row['qty'],
#                 PharmacyInvoice.days_supplied==row['ds'],
#                 PharmacyInvoice.charge_amt==row['bill'],
#                 PharmacyInvoice.note==row['billing_comment'],
#                 PharmacyInvoice.duplicate_flg==1
#             ).first()

#     assert record is not None


# # not working
# def test_geriscript_general():
#     file_name = '2020/10/Green Acres/General/Geriscript invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

#     row = invoice_info[3][0]
#     pharmacy_id = invoice_info[0].pharmacy.id
#     facility_id = invoice_info[0].facility.id

#     first_nm = get_first_name(row['patient_nm'])
#     last_nm = get_last_name(row['patient_nm'])

#     record = session.query(PharmacyInvoice).filter(
#                 PharmacyInvoice.pharmacy_id==pharmacy_id,
#                 PharmacyInvoice.facility_id==facility_id,
#                 PharmacyInvoice.first_nm==first_nm,
#                 PharmacyInvoice.last_nm==last_nm,
#                 PharmacyInvoice.ssn==row['ssn'],
#                 PharmacyInvoice.dispense_dt==row['disp_dt'],
#                 PharmacyInvoice.product_category==row['rx_type'],
#                 PharmacyInvoice.drug_nm==row['drug'],
#                 PharmacyInvoice.doctor==row['physician'],
#                 PharmacyInvoice.rx_nbr==row['rx_no'],
#                 PharmacyInvoice.ndc==row['ndc'],
#                 PharmacyInvoice.quantity==row['qty'],
#                 PharmacyInvoice.days_supplied==row['ds'],
#                 PharmacyInvoice.charge_amt==row['bill'],
#                 PharmacyInvoice.note==row['billing_comment'],
#                 PharmacyInvoice.duplicate_flg==1
#             ).first()

#     assert record is not None


# def test_speciality_rx_email():
#     file_name = '2020/10/Ashbrook/Email/Specialty Emailed Version.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

#     row = invoice_info[3][0]
#     pharmacy_id = invoice_info[0].pharmacy.id
#     facility_id = invoice_info[0].facility.id

#     first_nm = get_first_name(row['patient_nm'])
#     last_nm = get_last_name(row['patient_nm'])

#     record = session.query(PharmacyInvoice).filter(
#                 PharmacyInvoice.pharmacy_id==pharmacy_id,
#                 PharmacyInvoice.facility_id==facility_id,
#                 PharmacyInvoice.first_nm==first_nm,
#                 PharmacyInvoice.last_nm==last_nm,
#                 PharmacyInvoice.ssn==row['ssn'],
#                 PharmacyInvoice.dispense_dt==row['disp_dt'],
#                 PharmacyInvoice.product_category==row['rx_type'],
#                 PharmacyInvoice.drug_nm==row['drug'],
#                 PharmacyInvoice.doctor==row['physician'],
#                 PharmacyInvoice.rx_nbr==row['rx_no'],
#                 PharmacyInvoice.ndc==row['ndc'],
#                 PharmacyInvoice.quantity==row['qty'],
#                 PharmacyInvoice.days_supplied==row['ds'],
#                 PharmacyInvoice.charge_amt==row['bill'],
#                 PharmacyInvoice.note==row['billing_comment'],
#                 PharmacyInvoice.duplicate_flg==1
#             ).first()

#     assert record is not None


# def test_speciality_rx_portal():
#     file_name = '2020/10/Ashbrook/Portal/Specialty Portal Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

#     row = invoice_info[3][0]
#     pharmacy_id = invoice_info[0].pharmacy.id
#     facility_id = invoice_info[0].facility.id

#     first_nm = get_first_name(row['patient_nm'])
#     last_nm = get_last_name(row['patient_nm'])

#     record = session.query(PharmacyInvoice).filter(
#                 PharmacyInvoice.pharmacy_id==pharmacy_id,
#                 PharmacyInvoice.facility_id==facility_id,
#                 PharmacyInvoice.first_nm==first_nm,
#                 PharmacyInvoice.last_nm==last_nm,
#                 PharmacyInvoice.ssn==row['ssn'],
#                 PharmacyInvoice.dispense_dt==row['disp_dt'],
#                 PharmacyInvoice.product_category==row['rx_type'],
#                 PharmacyInvoice.drug_nm==row['drug'],
#                 PharmacyInvoice.doctor==row['physician'],
#                 PharmacyInvoice.rx_nbr==row['rx_no'],
#                 PharmacyInvoice.ndc==row['ndc'],
#                 PharmacyInvoice.quantity==row['qty'],
#                 PharmacyInvoice.days_supplied==row['ds'],
#                 PharmacyInvoice.charge_amt==row['bill'],
#                 PharmacyInvoice.note==row['billing_comment'],
#                 PharmacyInvoice.duplicate_flg==1
#             ).first()

#     assert record is not None
