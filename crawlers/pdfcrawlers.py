import fitz  
import pandas as pd
import requests
import os
import json
from tqdm import tqdm

model_name = 'llama3.1:latest' #"llama3.1:latest"

def extract_pdf(code, pdf_url):

    def extract_text_from_pdf_with_keywords(pdf_url, code):
        def download_pdf_from_url(url, output_path):
            response = requests.get(url)
            with open(output_path, 'wb') as file:
                file.write(response.content)

        """     def find_keywords_in_pdf(pdf_path, keywords):
            doc = fitz.open(pdf_path)
            pages_with_keywords = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if any(keyword.lower() in text.lower() for keyword in keywords):
                    pages_with_keywords.append(page_num + 1)

            return sorted(set(pages_with_keywords)) """

        def get_range_by_code(code):
            # Read the pages.json file
            with open('pages.json', 'r') as file:
                pages = json.load(file)
            
            # Find the object with the matching code
            for page in pages:
                if page['code'] == code:
                    return page['range']
            
            return []  # Return an empty list if the code is not found

        def extract_text_from_pages(pdf_path, page_numbers):
            doc = fitz.open(pdf_path)
            text_list = []
            seen_pages = set()
            i = 0

            while i < len(page_numbers):
                page_num = page_numbers[i] - 1  # adjust for 1-based indexing
                
                if page_num in seen_pages:
                    i += 1
                    continue

                current_text = doc[page_num].get_text()
                next_page_text = ""
                next_next_page_text = ""

                if page_num + 1 < len(doc):
                    next_page_text = doc[page_num + 1].get_text()

                if page_num + 2 < len(doc) and (i + 1 < len(page_numbers) and page_numbers[i + 1] == page_num + 2 + 1):
                    next_next_page_text = doc[page_num + 2].get_text()

                combined_text = current_text + next_page_text + next_next_page_text
                text_list.append(combined_text)

                seen_pages.add(page_num)
                seen_pages.add(page_num + 1)
                seen_pages.add(page_num + 2)
                i += 1

            return text_list

        pdf_path = 'downloaded_pdf_file.pdf'

        # Download PDF from the URL
        download_pdf_from_url(pdf_url, pdf_path)

        # Find pages with the keywords
        #pages = find_keywords_in_pdf(pdf_path, keywords)
        pages = get_range_by_code(code)
        
        # Extract text from the found pages and their next pages
        text_list = extract_text_from_pages(pdf_path, pages)

        # Delete the PDF file after extraction
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        return text_list



    def ask_ollama(prompt):
        url = 'http://localhost:11434/api/generate'
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False, 
            'temperature': 0,
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        result = response.json()
        return result.get('response')

    """     def analyze_texts_with_ollama(text_list):
        results = []
        for text in text_list:
            response = ask_ollama(f"Indicate if the following text contain information about non-freefloat shareholders? You MUST only answer \"Yes\" or \"No\"c {text}")
            # Process the response to determine if it mentions non-freefloat shareholders
            if 'Yes' in response:
                results.append(True)
            else:
                results.append(False)
        return results """

    def extract_shareholder_info(text):
        shareholder_info = []
        example_json = [
            {
                "name": "6 Dimensions Capital",
                "shares": 119890000
            },
            {
                "name": "Employee Share Trust",
                "shares": 34470000,
            },
        ]
        response = ask_ollama(f"Extract all the information of long position shareholders, directors, or corporations, and their respective number of long position shares, from the following text delimited in brackets ():\n\n({text})\n\nBe aware to only extract long position shares. Only output a JSON object with the exact format {{'name': 'string', 'shares': 'integer'}}. Please output strictly only the JSON object formatted without any additional texts exactly like the following example:\n{example_json}")
        
        # Extract the JSON part from the response text
        start = response.find('[')
        end = response.rfind(']') + 1
        json_str = response[start:end]
        # Replace single quotes with double quotes to make it valid JSON
        json_str = json_str.replace("'", '"') 

        # Load the JSON string into a Python object
        info = json.loads(json_str)
        
        # Extend the shareholder_info list with the extracted data
        shareholder_info.extend(info)
        
        return shareholder_info

    def extract_date(text):
        response = ask_ollama(f"Read the following extract delimited by () from a financial report and extract one and only one cutoff date as a string in \"DD/MM/YYYY\" format, and enclose the date in double quotation mark without any additional text. Please follow the instruction format strictly. If you cannot find any valid cutoff date, default it to \"30/06/2023\" to prevent error.\n\n({text}])")
        
        # Extract the JSON part from the response text
        start = response.find('"')
        end = response.rfind('"') + 1
        str = response[start:end]
        # Replace single quotes with double quotes to make it valid JSON
        str = str.replace("\"", '') 

        return str

    #keywords = ['SFO', 'Securities and Futures Ordinance']  # Add more keywords as needed

    # Analyze the string array
    texts = extract_text_from_pdf_with_keywords(pdf_url=pdf_url, code=code)


    # Output the results
    data = []
    for text in enumerate(texts):
        if text:
            date = extract_date(text)
            shareholders_info = extract_shareholder_info(text)
            
            # Add date to each shareholder's info
            for shareholder in shareholders_info:
                shareholder["date"] = date
                data.append(shareholder)
        
    return data

#print(json.dumps(extract_pdf(pdf_url='https://www1.hkexnews.hk/listedco/listconews/sehk/2023/0913/2023091300309.pdf', code="0909.HK"), indent=4))

input_csv = "provided_data/faf_documents.csv"
output_json = "output.json"
error_file = "error.txt"

df = pd.read_csv(input_csv)
data = []
for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing rows"):
    RIC = row["RIC"]
    financial_report_urls = row["Financial report"].split("\n")
    if financial_report_urls:
        pdf_url = financial_report_urls[0].strip()
        try:
            extracted_data = extract_pdf(code=RIC, pdf_url=pdf_url)
            entry = {"code": RIC, "data": extracted_data}
            data.append(entry)
            with open(output_json, "w") as jsonfile:
                json.dump(data, jsonfile, indent=4)
            print(f"Data for {RIC} extracted and written to {output_json}")
        except Exception as e:
            error_message = f"Error processing {RIC}: {str(e)}\n"
            print(error_message)
            with open(error_file, "a") as errorfile:
                errorfile.write(error_message)
            continue

print("All data processed and written to the JSON file") 
 