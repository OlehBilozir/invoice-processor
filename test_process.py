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


# -- both work
# def test_pharmscripts_portal():
#     file_name = '2020/October/Deer Meadows NEW/Portal/Boyd April Untouched Invoice.xlsx'
#     file_name = '2020/October/Deer Meadows NEW/Portal/Pharmscripts Portal Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

# -- invalid Bed
# def test_pharmscripts_email():
#     file_name = '2020/October/Deer Meadows NEW/Email/Pharmscripts Emailed Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == False

#     # result = invoice_process.process_invoice(invoice_info, log_file, True)
#     # assert result == True

# -- both work
# def test_process_row_omnicare_general():
#     file_name = '2020/October/Beacon/General/Holland September Untouched Invoice.xlsx'
#     file_name = '2020/October/Beacon/General/Omnicare Email.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True

# -- work
# def test_pharmerica_email():
#     file_name = '2020/October/Ridgewood/Email/Cartersville May Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True


# def test_pharmerica_portal():
#     file_name = '2020/October/Ridgewood/Portal/Pharmerica Portal Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == False


# not working
def test_geriscript_general():
    file_name = '2020/October/Green Acres/General/Geriscript invoice.xlsx'

    result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
    assert result == True

    result = invoice_process.process_invoice(invoice_info, log_file, True)
    assert result == True


# def test_speciality_rx_email():
#     file_name = '2020/October/Ashbrook/Email/Specialty Emailed Version.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True


# def test_speciality_rx_portal():
#     file_name = '2020/October/Ashbrook/Portal/Specialty Portal Invoice.xlsx'

#     result, log_file, invoice_info = invoice_process.validate_file(file_name, True)
#     assert result == True

#     result = invoice_process.process_invoice(invoice_info, log_file, True)
#     assert result == True
