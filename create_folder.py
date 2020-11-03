from datetime import datetime

from utilities import *


def main():
    year = datetime.now().year
    month = datetime.now().month

    facilities = get_facilities()

    for facility in facilities:
        pharmacy_map = get_pharmacy(facility)
        if not pharmacy_map:
            continue
        pharmacy = pharmacy_map.pharmacy
        reader_settings = get_reader_settings(pharmacy)
        for rs in reader_settings:
            source = 'Portal' if rs.invoice_source_id == 1 else 'Email' if rs.invoice_source_id == 2 else 'General'
            directory_name = f"{year}/{month}/{facility.facility_nm}/{source}/"
            get_s3_client().put_object(Bucket=get_s3_bucket(), Key=(directory_name))


if __name__ == '__main__':
    main()
