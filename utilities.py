import re
import configparser

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import boto3
import pyodbc
import dateparser
from sqlalchemy import or_

from models import *


def get_s3_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['s3']


def get_s3_bucket():
    s3_config = get_s3_config()
    return s3_config['bucket']


def get_s3_client():
    s3_config = get_s3_config()

    return boto3.client(
        's3',
        aws_access_key_id=s3_config['access_key_id'],
        aws_secret_access_key=s3_config['secret_access_key']
    )


def get_sqs_resource():
    s3_config = get_s3_config()

    return boto3.resource(
        'sqs',
        region_name='us-east-1',
        aws_access_key_id=s3_config['access_key_id'],
        aws_secret_access_key=s3_config['secret_access_key']
    )


def get_ses_client():
    s3_config = get_s3_config()

    return boto3.client(
        'ses',
        region_name='us-west-2',
        aws_access_key_id=s3_config['access_key_id'],
        aws_secret_access_key=s3_config['secret_access_key']
    )


def clean_text(val):
    if val is not None:
        return str(val).strip()


def get_valid_rows_count(ws):
    for max_row, row in enumerate(ws, 1):
        if all(c.value is None or str(c.value).strip() == '' for c in row):
            return max_row - 1

    return ws.max_row


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
    payer_group = session.query(PayerGroupPharmacyMap).filter(
        PayerGroupPharmacyMap.pharmacy_id==pharmacy_id,
        or_(PayerGroupPharmacyMap.source==None, PayerGroupPharmacyMap.source==source),
        or_(PayerGroupPharmacyMap.name==None, PayerGroupPharmacyMap.name==inv_grp)).first()

    return payer_group.id


def get_reader_settings(pharmacy, source):
    reader_settings = session.query(PharmacyInvoiceReaderSetting).filter(
        PharmacyInvoiceReaderSetting.pharmacy_id==pharmacy.id,
        PharmacyInvoiceReaderSetting.invoice_source_id==source.id).first()

    return reader_settings


def validate_field(field, val):
    is_valid = True
    msg = ''

    if val:
        if field.field_type in ['int', 'long']:
            try:
                _val = int(val)
            except Exception as e:
                msg = str(e) + '\n'
                is_valid = False
        elif field.field_type == 'char':
            is_valid = len(val) == 1
            msg = 'Invalid char'
        elif field.field_type == 'decimal':
            try:
                _val = float(val.replace("$", "").replace("(", "").replace(")", ""))
            except Exception as e:
                is_valid = False
                msg = str(e) + '\n'
        elif field.field_type == 'date':
            is_valid = dateparser.parse(val)
            if not is_valid:
                msg = f'{field.sheet_column_name} is invalid.'

    if not is_valid or not field.field_validations:
        return is_valid, msg

    for rule in field.field_validations.split(','):
        if rule == 'IsNotEmpty':
            is_valid = val
        elif rule == 'Ssn':
            pat1 = re.compile("^\d{9}|\d{3}-\d{2}-\d{4}$|^$")
            pat2 = re.compile("^___-__-____$|^$")
            is_valid = pat1.match(val) or pat2.match(val)
        elif rule == 'MorF':
            is_valid = val.upper() in ['M', 'F']
        elif rule == 'BorG':
            is_valid = val.upper() in ['B', 'G']
        elif rule == 'MaxLength50':
            is_valid = len(val) < 50
        elif rule == 'MaxLength150':
            is_valid = len(val) < 150
        elif rule == 'MaxLength500':
            is_valid = len(val) < 500
        elif rule == 'MaxLength1000':
            is_valid = len(val) < 1000
        elif rule == 'Name':
            try:
                first_name, last_name = val.split(',')
                is_valid = len(first_name) < 25 and len(last_name) < 25
            except Exception as e:
                msg = str(e)
                is_valid = False

        if not is_valid:
            return is_valid, msg

    return is_valid, msg


def validate_row(invoice_fields, header, row, row_idx):
    # type list -> dict
    _row = {}
    for field in invoice_fields:
        idx = header.index(field.sheet_column_name)
        val = clean_text(row[idx].value)
        is_valid, msg = validate_field(field, val)
        if not is_valid:
            raise Exception(f'Column ({field.sheet_column_name}), Row ({row_idx}): '+msg)
        _row[field.field_name] = val

    return _row


def start_batch_logging(facility_pharmacy_map, invoice_dt, source):
    log = InvoiceBatchLog(facility_pharmacy_map_id=facility_pharmacy_map.id,
                          invoice_dt=invoice_dt,
                          status_cd=0,
                          source=source.id)
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
