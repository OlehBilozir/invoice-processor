import os
import sys
import time
import datetime
import configparser
import pyodbc

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import boto3

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
        region_name='us-west-2',
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


def parse_date(val):
    if val is None:
        return

    if isinstance(val, datetime.datetime):
        return val

    try:
        return datetime.datetime.strptime(val.split(' ')[0], '%m/%d/%Y')
    except Exception as e:
        pass


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
    facility_name = 'Deer Meadows NEW'
    facility = session.query(Facility).filter(Facility.facility_nm==facility_name).first()

    return facility


def get_source(file_name):
    source_name = 'Portal'
    source = session.query(InvoiceSource).filter(InvoiceSource.source_nm==source_name).first()

    return source


def get_pharmacy(facility):
    pharmcy_map = session.query(FacilityPharmacyMap).filter(FacilityPharmacyMap.facility_id==facility.id).first()

    return pharmcy_map


def get_payer_group(cursor, pharmacy_id, source):
    pass


def get_reader_settings(pharmacy, source):
    reader_settings = session.query(PharmacyInvoiceReaderSetting).filter(
        PharmacyInvoiceReaderSetting.pharmacy_id==pharmacy.id,
        PharmacyInvoiceReaderSetting.invoice_source_id==source.id).first()
    print (reader_settings.id, '='*10)

    return reader_settings


def is_valid_row(row):
    return True
