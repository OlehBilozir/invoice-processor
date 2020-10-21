import sys

import invoice_process


if __name__ == '__main__':
    # file_name = sys.argv[1]
    file_name = '2020/October/Deer Meadows NEW/Portal/boyd-invoice.xlsx'

    (facility_pharmacy_map, invoice_dt, source, data) = invoice_process.validate_file(file_name)
    if not data:
        raise Exception("The file is invalid.")

    res = invoice_process.process_invoice(facility_pharmacy_map, invoice_dt, source, data)
