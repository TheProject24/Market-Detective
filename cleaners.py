# cleaners.py

def clean_price_string(price_text):
    first_part = price_text.split('\n')[0]

    clean_str = first_part.replace('₦', '').replace(',', '').strip()

    try :
        return int(clean_str)
    except:
        return 0