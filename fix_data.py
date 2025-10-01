#!/usr/bin/env python3
from db import connect

def fix_dway_data():
    """Fix the incorrect data for person 'dway'"""
    con = connect()
    cur = con.cursor()
    
    # Fix the data for 'dway' - moving data to correct fields
    cur.execute('''
    UPDATE people SET 
        phone = '',  -- Clear wrong phone data
        dob = '',    -- Clear wrong dob data  
        link = 'www.apple.com',  -- Move from phone to link
        info = 'add info',       -- Keep existing info
        social_link = 'fb.link', -- Move from link to social_link
        info1 = 'Not provided',  -- Set default value
        note = 'this is the sample note'  -- Move from social_link to note
    WHERE name = 'dway'
    ''')
    
    con.commit()
    
    # Verify the fix
    cur.execute('SELECT id, name, phone, dob, link, info, social_link, info1, note FROM people WHERE name=?', ('dway',))
    data = cur.fetchone()
    print('Fixed data for dway:')
    print(f'ID: {data[0]}')
    print(f'Name: {data[1]}')
    print(f'Phone: {data[2]}')
    print(f'DOB: {data[3]}')
    print(f'Link: {data[4]}')
    print(f'Info: {data[5]}')
    print(f'Social Link: {data[6]}')
    print(f'Info1: {data[7]}')
    print(f'Note: {data[8]}')
    con.close()

if __name__ == "__main__":
    fix_dway_data()
