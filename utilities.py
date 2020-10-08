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

from sqlalchemy.engine import url as sa_url
from sqlalchemy import create_engine


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


def get_db_connection():
    # get Redshift configuration values from file
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=LocalHost;"
                          "Database=Omerus;"
                          "Trusted_Connection=yes;")
    cursor = cnxn.cursor()
    return cursor
    cursor.close()
    cnxn.close()

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


def get_pharmacy(file_name):
    return file_name


def get_payer_group(cursor, pharmacy_id, source):
    sql = "SELECT * FROM [Ancillary_data_warehouse].[dbo].[payer_groups] WHERE pharmacy_id=? and source=?"
    res = cursor.execute(sql, (pharmacy_id, source)).fetchone()

    return res
