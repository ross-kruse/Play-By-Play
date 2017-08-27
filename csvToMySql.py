import csv
import glob
from datetime import datetime
import mysql.connector
from mysql.connector import Error

"""
This file reads CSV files created by scraping.py and inserts them into
a MySQL database.

Author:
    Ross Kruse
"""
