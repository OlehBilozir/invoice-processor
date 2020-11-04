import re

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import boto3
import pyodbc
import dateparser
from sqlalchemy import or_

from models import *
import os



def get_s3_bucket():
    return os.getenv('bucket')


def get_s3_client():
    return boto3.client(
        's3'
    )


def get_sqs_resource():
    return boto3.resource(
        'sqs',
        region_name='us-east-1',
    )


def get_ses_client():
    return boto3.client(
        'ses',
        region_name='us-east-1',
    )


def clean_text(val):
    if val is not None:
        return str(val).strip()


def get_valid_rows_count(ws):
    try:
        for max_row, row in enumerate(ws, 1):
            if all(c.value is None or str(c.value).strip() == '' for c in row):
                return max_row - 1

        return ws.max_row
    except Exception as e:
        pass


def get_valid_cols_count(ws):
    ncols = ws.max_column
    for col in range(1, ncols):
        if not ws.cell(1, col).value:
            return col - 1
    return ncols


def send_email(subject, from_email, to_emails, body, attachment=None):
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_emails
    # message body
    part = MIMEText(body, 'html')
    message.attach(part)
    # attachment
    if attachment:
        attachment_body = open(attachment).read()
        part = MIMEApplication(str.encode(attachment_body))
        part.add_header('Content-Disposition', 'attachment', filename=attachment)
        message.attach(part)

    resp = get_ses_client().send_raw_email(
        Source=message['From'],
        Destinations=to_emails.split(','),
        RawMessage={
            'Data': message.as_string()
        }
    )

    return resp


def get_year(file_name):
    try:
        return int(file_name.split('/')[0])
    except Exception as e:
        pass


def get_month(file_name):
    try:
        return int(file_name.split('/')[1])
    except Exception as e:
        pass


def get_facilities():
    return session.query(Facility).filter(Facility.delete_by==None)


def get_facility(file_name):
    facility_name = file_name.split('/')[2]
    facility = session.query(Facility).filter(Facility.facility_nm==facility_name).first()

    return facility


def get_source(file_name):
    source_name = file_name.split('/')[3]
    source = session.query(InvoiceSource).filter(InvoiceSource.source_nm==source_name).first()

    return source


def get_pharmacy(facility):
    pharmcy_map = session.query(FacilityPharmacyMap).filter(FacilityPharmacyMap.facility_id==facility.id).first()

    return pharmcy_map


def get_payer_group(pharmacy_id, inv_grp, source):
    print(pharmacy_id, inv_grp, source, '&'*10) 
    payer_group = session.query(PayerGroupPharmacyMap).filter(
        PayerGroupPharmacyMap.pharmacy_id==pharmacy_id,
        or_(PayerGroupPharmacyMap.source==None, PayerGroupPharmacyMap.source==source),
        # or_(PayerGroupPharmacyMap.facility_group_id==None, PayerGroupPharmacyMap.facility_group_id==facility_group_id),
        or_(PayerGroupPharmacyMap.name==None, PayerGroupPharmacyMap.name==inv_grp)).first()

    return payer_group.id if payer_group else None


def get_reader_settings(pharmacy):
    reader_settings = session.query(PharmacyInvoiceReaderSetting).filter(
        PharmacyInvoiceReaderSetting.pharmacy_id==pharmacy.id)

    return reader_settings


def get_reader_setting(pharmacy, source):
    source_id = source.id if source else 0
    reader_settings = session.query(PharmacyInvoiceReaderSetting).filter(
        PharmacyInvoiceReaderSetting.pharmacy_id==pharmacy.id,
        PharmacyInvoiceReaderSetting.invoice_source_id==source_id).first()

    return reader_settings


def validate_field(field, val):
    # val is not empty
    is_valid = True
    msg = ''
    _val = None

    if field.field_type in ['int', 'long']:
        try:
            _val = int(val)
        except Exception as e:
            msg = "Invalid number"
            is_valid = False
    elif field.field_type == 'char':
        is_valid = len(val) == 1
        if not is_valid:
            msg = 'Invalid char'
    elif field.field_type == 'decimal':
        try:
            _val = float(val.replace("$", "").replace("(", "").replace(")", ""))
        except Exception as e:
            is_valid = False
            msg = "Invalid decimal"
    elif field.field_type == 'date':
        _val = dateparser.parse(val)
        if not _val:
            is_valid = False
            msg = "Invalid date"

    if field.field_validations:
        for rule in field.field_validations.split(','):
            _msg = ''

            if rule == 'Ssn':
                pat1 = re.compile("^\d{9}|\d{3}-\d{2}-\d{4}$|^$")
                pat2 = re.compile("^___-__-____$|^$")
                is_valid = pat1.match(val) or pat2.match(val)
                if not is_valid:
                    _msg = "Invalid SSN"
            elif rule == 'MorF':
                is_valid = val.upper() in ['M', 'F']
                if not is_valid:
                    _msg = "Should be M or F"
            elif rule == 'BorG':
                is_valid = val.upper() in ['B', 'G']
                if not is_valid:
                    _msg = "Should be B or G"
            elif rule == 'MaxLength50':
                is_valid = len(val) < 50
                if not is_valid:
                    _msg = "Length should be less than 50"
            elif rule == 'MaxLength150':
                is_valid = len(val) < 150
                if not is_valid:
                    _msg = "Length should be less than 150"
            elif rule == 'MaxLength500':
                is_valid = len(val) < 500
                if not is_valid:
                    _msg = "Length should be less than 500"
            elif rule == 'MaxLength1000':
                is_valid = len(val) < 1000
                if not is_valid:
                    _msg = "Length should be less than 1000"
            elif rule == 'Name':
                try:
                    first_name, last_name = val.split(',')
                    is_valid = len(first_name) < 25 and len(last_name) < 25
                except Exception as e:
                    is_valid = False
                    _msg = "Invalid name"

            if _msg:
                msg = msg + ', ' + _msg if msg else _msg

    return is_valid, msg, _val or val


def validate_row(invoice_fields, header, row, row_idx, log_file):
    # type list -> dict
    _row = {}
    is_valid = True
    for field in invoice_fields:
        val = None
        if field.sheet_column_name in header:
            idx = header.index(field.sheet_column_name)
            val = clean_text(row[idx].value)

        if field.sheet_column_name not in header or not val:
            if not field.is_optional and field.field_validations and 'IsNotEmpty' in field.field_validations:
                is_valid = False
                msg = "Should not be empty"
                print("Row:", row_idx, "," , "Column:", field.sheet_column_name, ",", "Msg:", msg, file=log_file)
            else:
                # add column as long as it is not invalid
                _row[field.field_name] = val                
        else:
            _is_valid, msg, val = validate_field(field, val)

            if _is_valid:
                _row[field.field_name] = val
            else:
                is_valid = False
                print("Row:", row_idx, "," , "Column:", field.sheet_column_name, ",", "Msg:", msg, file=log_file)

    return is_valid, _row


def start_batch_logging(facility_pharmacy_map, invoice_dt, source_id):
    log = InvoiceBatchLog(facility_pharmacy_map_id=facility_pharmacy_map.id,
                          invoice_dt=invoice_dt,
                          status_cd=0,
                          source=source_id)
    session.add(log)
    session.commit()

    return log.id


def stop_batch_logging(invoice_batch_log_id):
    log = session.query(InvoiceBatchLog).get(invoice_batch_log_id)
    log.status_cd = 1
    session.commit()


def get_first_name(name):
    first_name = name.split(',')[0].strip()
    return first_name


def get_last_name(name):
    if ',' in name:
        last_name = name.split(',')[1].strip()
        return last_name


def get_clean_header_column(text):
    return ' '.join(re.findall('\S+', str(text)))
