# coding: utf-8
from sqlalchemy import BigInteger, CHAR, Column, Date, DateTime, Float, ForeignKey, Index, Integer, NCHAR, String, TEXT, Time, Unicode, text
from sqlalchemy.dialects.mssql import BIT, MONEY, SMALLMONEY, TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

db_host = os.getenv('db_host')
db_name = os.getenv('db_name')
db_user = os.getenv('db_user')
db_password = os.getenv('db_password')
engine = create_engine(f'mssql+pyodbc://{db_user}:{db_password}@{db_host}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server')
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Facility(Base):
    __tablename__ = 'facilities'

    id = Column(Integer, primary_key=True)
    facility_group_id = Column(Integer)
    invoice_facility_nm = Column(Unicode(150))
    facility_nm = Column(Unicode(150), nullable=False)
    create_by = Column(Integer, nullable=False)
    create_dt = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    update_by = Column(Integer)
    update_dt = Column(DateTime)
    no_contract_on_file = Column(BIT)
    delete_by = Column(Integer)
    delete_dt = Column(DateTime)


class FacilityGroup(Base):
    __tablename__ = 'facility_groups'

    id = Column(Integer, primary_key=True)
    facility_group_nm = Column(String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)


class FacilityPharmacyMap(Base):
    __tablename__ = 'facility_pharmacy_maps'

    id = Column(Integer, primary_key=True)
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))
    start_dt = Column(DateTime, nullable=False)
    through_dt = Column(DateTime)
    create_by = Column(Integer, nullable=False)
    create_dt = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    update_by = Column(Integer)
    update_dt = Column(DateTime)
    delete_by = Column(Integer)
    delete_dt = Column(DateTime)
    pending_days = Column(Integer)
    is_per_diem = Column(BIT)
    otc_dispute_status = Column(Integer)

    pharmacy = relationship("Pharmacy")
    facility = relationship("Facility")


class InvoiceBatchLog(Base):
    __tablename__ = 'invoice_batch_logs'

    id = Column(Integer, primary_key=True)
    facility_pharmacy_map_id = Column(Integer, nullable=False)
    invoice_dt = Column(Date, nullable=False)
    import_start_tm = Column(Time)
    import_end_tm = Column(Time)
    status_cd = Column(TINYINT, nullable=False, server_default=text("((1))"))
    source = Column(TINYINT, server_default=text("((0))"))
    raw_invoice_table_nm = Column(String(80, 'SQL_Latin1_General_CP1_CI_AS'))


class InvoiceSource(Base):
    __tablename__ = 'invoice_sources'

    id = Column(Integer, primary_key=True)
    source_nm = Column(String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    create_dt = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    create_by = Column(Integer, nullable=False)
    update_dt = Column(DateTime)
    update_by = Column(Integer)


class PayerGroupPharmacyMap(Base):
    __tablename__ = 'payer_group_pharmacy_maps'

    id = Column(Integer, primary_key=True)
    payer_group_id = Column(Integer, nullable=False)
    pharmacy_id = Column(Integer, nullable=False)
    facility_group_id = Column(Integer)
    source = Column(TINYINT)
    name = Column(String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    created_date = Column(DateTime, nullable=False, server_default=text("(getdate())"))


class Pharmacy(Base):
    __tablename__ = 'pharmacies'

    id = Column(Integer, primary_key=True, unique=True)
    pharmacy_nm = Column(Unicode(150), nullable=False, unique=True)
    raw_invoice_table_nm = Column(Unicode(150), nullable=False)


class PharmacyInvoiceReaderSetting(Base):
    __tablename__ = 'pharmacy_invoice_reader_settings'

    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, nullable=False)
    invoice_source_id = Column(Integer, nullable=False, server_default=text("((0))"))
    facility_group_id = Column(Integer, nullable=False, server_default=text("((0))"))
    invoice_reader_classname = Column(String(150, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    sheet_name = Column(String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    header_row_index = Column(Integer, server_default=text("((0))"))
    skip_rows_after_header = Column(Integer, server_default=text("((0))"))
    skip_ending_rows = Column(Integer, server_default=text("((0))"))
    bulk_insert_sp_name = Column(String(150, 'SQL_Latin1_General_CP1_CI_AS'))
    delete_by = Column(Integer)
    delete_dt = Column(DateTime)

    raw_invoice_fields = relationship("RawInvoiceField", back_populates="pharmacy_invoice_reader_setting")


class PharmacyInvoice(Base):
    __tablename__ = 'pharmacy_invoices'

    id = Column(Integer, primary_key=True)
    invoice_batch_id = Column(Integer, nullable=False)
    pharmacy_id = Column(Integer, nullable=False)
    facility_id = Column(Integer, nullable=False)
    payer_group_id = Column(Integer, nullable=False)
    invoice_dt = Column(Date, nullable=False)
    first_nm = Column(String(25, 'SQL_Latin1_General_CP1_CI_AS'))
    middle_nm = Column(String(25, 'SQL_Latin1_General_CP1_CI_AS'))
    last_nm = Column(String(25, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    ssn = Column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    dob = Column(Date)
    gender = Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'))
    dispense_dt = Column(Date)
    product_category = Column(String(150, 'SQL_Latin1_General_CP1_CI_AS'))
    drug_nm = Column(String(150, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    doctor = Column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    rx_nbr = Column(Integer)
    ndc = Column(String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    reject_cd = Column(String(150, 'SQL_Latin1_General_CP1_CI_AS'))
    quantity = Column(Float(24))
    days_supplied = Column(Float(24))
    charge_amt = Column(MONEY, nullable=False)
    copay_amt = Column(MONEY)
    copay_flg = Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'))
    census_match_cd = Column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    status_cd = Column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    charge_confirmed_flg = Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'))
    duplicate_flg = Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'))
    note = Column(String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    request_credit_flg = Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'))
    credit_request_dt = Column(Date)
    credit_request_cd = Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'))
    days_overbilled = Column(Float(24))
    dispute_status_id = Column(Integer, nullable=False, server_default=text("((0))"))
    dispute_reason_id = Column(Integer)
    dispute_response = Column(String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    month_received_credit_dt = Column(Date)
    amount_received = Column(MONEY)
    dispute_note = Column(String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    comment = Column(String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    resident_id = Column(Integer)
    amount_overbilled = Column(MONEY)
    transaction_type = Column(String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    is_returnable = Column(BIT, server_default=text("((0))"))
    is_pending = Column(BIT, server_default=text("((0))"))
    dispute_status_by = Column(Integer)
    accurate_charge_by = Column(Integer)


class RawInvoiceField(Base):
    __tablename__ = 'raw_invoice_fields'

    id = Column(Integer, primary_key=True)
    pharmacy_invoice_reader_setting_id = Column(Integer, ForeignKey('pharmacy_invoice_reader_settings.id'))
    field_name = Column(String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    sheet_column_name = Column(String(150, 'SQL_Latin1_General_CP1_CI_AS'))
    field_type = Column(String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    field_validations = Column(String(150, 'SQL_Latin1_General_CP1_CI_AS'))
    is_optional = Column(BIT)

    pharmacy_invoice_reader_setting = relationship("PharmacyInvoiceReaderSetting", back_populates="raw_invoice_fields")
