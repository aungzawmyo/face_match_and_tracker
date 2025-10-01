#!/usr/bin/env python3
from db import connect, add_person, get_person_by_name_legacy

def test_add_person_field_mapping():
    """Test that fields are stored in correct database columns"""
    con = connect()
    
    # Test data with unique values to verify field mapping
    test_name = "test_person_mapping"
    test_phone = "123-456-7890" 
    test_dob = "1990-01-01"
    test_link = "https://example.com"
    test_info = "general info test"
    test_social_link = "https://social.example.com"
    test_info1 = "additional info test"
    test_note = "note test"
    
    # Add person with keyword arguments (like in the fixed code)
    person_id = add_person(con, test_name, None,
                         phone=test_phone, dob=test_dob, link=test_link,
                         info=test_info, social_link=test_social_link,
                         info1=test_info1, note=test_note)
    
    # Retrieve and verify
    person_data = get_person_by_name_legacy(con, test_name)
    
    if person_data:
        print("Field mapping test results:")
        print(f"ID: {person_data[0]}")
        print(f"Name: {person_data[1]}")
        print(f"Phone: {person_data[2]} (expected: {test_phone})")
        print(f"DOB: {person_data[3]} (expected: {test_dob})")
        print(f"Link: {person_data[4]} (expected: {test_link})")
        print(f"Info: {person_data[5]} (expected: {test_info})")
        print(f"Social Link: {person_data[6]} (expected: {test_social_link})")
        print(f"Info1: {person_data[7]} (expected: {test_info1})")
        print(f"Note: {person_data[8]} (expected: {test_note})")
        
        # Check if fields match expected values
        mapping_correct = (
            person_data[2] == test_phone and
            person_data[3] == test_dob and
            person_data[4] == test_link and
            person_data[5] == test_info and
            person_data[6] == test_social_link and
            person_data[7] == test_info1 and
            person_data[8] == test_note
        )
        
        print(f"\nField mapping is {'CORRECT' if mapping_correct else 'INCORRECT'}")
        
        # Clean up test data
        con.execute("DELETE FROM people WHERE name=?", (test_name,))
        con.commit()
        
    else:
        print("Failed to retrieve test person data")
    
    con.close()

if __name__ == "__main__":
    test_add_person_field_mapping()
