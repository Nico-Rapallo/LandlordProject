## Does not run in virtual enviorment or on Mac ##

import requests
import urllib.request
from pypdf import PdfReader
import re
from spire.pdf.common import *
from spire.pdf import *
import os
import shutil

BASE_URL = 'https://gis.williamsburgva.gov/vision/'
BASE_PDF = 'src/data/property_data/pdf_temporary/'

import requests
import urllib.request
from pypdf import PdfReader
import re
from spire.pdf.common import *
from spire.pdf import *
import os

BASE_URL = 'https://gis.williamsburgva.gov/vision/'
BASE_PDF = 'src/data/property_data/pdf_temporary/'

def run_scraper(PID:int) -> tuple[int, int, int, str]:
    url = BASE_URL + str(PID) + '.pdf'
    pdf_path = BASE_PDF + str(PID) + '.pdf'
    
    try: 
        urllib.request.urlretrieve(url, pdf_path)
    except Exception as e:
        print(f'Failed reading url\nError Message: {e}')
        return None
    
    text = get_text(pdf_path)
    fields = get_details(text)
    if fields['RentalUnit(s)']>0:
        image_path = get_image(pdf_path, PID)
    else:
        image_path = None
    os.remove(pdf_path)
    return fields | {'img_path':image_path}

### https://www.geeksforgeeks.org/working-with-pdf-files-in-python/ ###
def get_text(pdf_file:str) -> str:
    '''
    Take pdf filepath and output text string 
    '''
    # creating a pdf reader object
    try: 
        reader = PdfReader(pdf_file)
    except Exception as e:
        print(f'Faliure reading file: {pdf_file}\nError message: "{e}"')
        return None

    text = ""
    for page in reader.pages:
        text += page.extract_text(extraction_mode="layout") + "\n"
    return text

def parse_value(value_str, none_tag):
    if none_tag:
        return 0
    elif len(set(value_str)) == 1:
        return int(value_str[0])
    else:
        return int(value_str)

def get_details(text):
    ## Remove Spaces From Text
    clean_text = text.replace(' ', '')

    # Dictionary with property details
    fields = {
        'HalfBaths': 0,
        'FullBaths': 0,
        'Bedrooms': 0,
        'RentalUnit(s)': 0
    }

    ## Loop through dictionary
    for field in fields.keys():
        # If rental units just get value
        if field == 'RentalUnit(s)':
            pattern = rf'{re.escape(field)}(\d+)'
            matches = re.findall(pattern, clean_text)
            fields[field] = sum(int(match) for match in matches)
        # Otherwise run parse_value to avoid errors
        else:
            pattern = rf'{re.escape(field)}(\d+)(None)?'
            matches = re.findall(pattern, clean_text)
            fields[field] = sum(parse_value(num, none) for num, none in matches)
    
    return fields


#Code Copied directly from Medium, link: https://medium.com/@alexaae9/python-how-to-extract-images-from-pdf-documents-9492a767a613 ###
#!pip install Spire.PDF
def get_image(pdf_file:str, PID:int) -> str:
    # Create a PdfDocument object
    doc = PdfDocument()
    
    # Load a PDF document
    doc.LoadFromFile(pdf_file)
    
    # Get a specific page
    page = doc.Pages.get_Item(0)
    
    # Create a PdfImageHelper object
    imageHelper = PdfImageHelper()
    
    # Get all image information from the page 
    imageInfos = imageHelper.GetImagesInfo(page)
    
    # Iterate through the image information
    for i in range(0, len(imageInfos)):
    
        # Specify the output image file name
        image_filename = 'src/data/property_data/image_data/' + str(PID) + '.png'
        imageFileName = image_filename.format(i)
    
        # Get a specific image
        image = imageInfos[i].Image
    
        # Save the image to a png file
        image.Save(imageFileName)
    
    # Dispose resources
    doc.Dispose()
    return image_filename

def delete_images():
    folder_path = 'src/data/property_data/image_data/'
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")