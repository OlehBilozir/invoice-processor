import sys

import invoice_process


if __name__ == '__main__':
    file_name = sys.argv[1]

    (facility_pharmacy_map, invoice_reader_settings, data) = invoice_process.validate_file(file_name)
    if not data:
        raise exception("The file is invalid.")

    res = process_invoice(facility_pharmacy_map, invoice_reader_settings, data)
