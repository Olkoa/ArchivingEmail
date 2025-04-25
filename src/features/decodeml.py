import os
import pandas as pd
import email
from email.policy import default
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
import duckdb
import streamlit as st
import codecs

def decode_unicode_escape(text):
    return codecs.decode(text, 'unicode_escape')



# Step 2: Parse .eml files
def getcharsets(msg):
    charsets = set({})
    for c in msg.get_charsets():
        if c is not None:
            charsets.update([c])
    return charsets

def getBody(msg):
    while msg.is_multipart():
        msg = msg.get_payload()[0]
    t = msg.get_payload(decode=True)
    for charset in getcharsets(msg):
        try:
            t = t.decode(charset)
        except:
            pass
    return t