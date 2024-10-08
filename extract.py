import fitz  # PyMuPDF
import requests
import os

def extract_text_from_pdf_with_keywords(pdf_url, keywords):
    def download_pdf_from_url(url, output_path):
        response = requests.get(url)
        with open(output_path, 'wb') as file:
            file.write(response.content)

    def find_keywords_in_pdf(pdf_path, keywords):
        doc = fitz.open(pdf_path)
        pages_with_keywords = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if any(keyword.lower() in text.lower() for keyword in keywords):
                pages_with_keywords.append(page_num + 1)

        return sorted(set(pages_with_keywords))

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
    pages = find_keywords_in_pdf(pdf_path, keywords)

    # Extract text from the found pages and their next pages
    text_list = extract_text_from_pages(pdf_path, pages)

    # Delete the PDF file after extraction
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    return text_list

import requests
import json

def ask_ollama(text, prompt):
    url = 'http://localhost:11434/api/generate'
    payload = {
        "model": "llama3.1:latest",
        "prompt": prompt,
        "stream": False, 
        'temperature': 0
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    result = response.json()
    return result.get('response', 'No')

def analyze_texts_with_ollama(text_list):
    results = []
    for text in text_list:
        response = ask_ollama(text, f"Indicate if the following text contain information about non-freefloat shareholders? You MUST only answer \"Yes\" or \"No\"c {text}")
        # Process the response to determine if it mentions non-freefloat shareholders
        if 'Yes' in response:
            results.append(True)
        else:
            results.append(False)
    return results

def extract_shareholder_info(text):
    shareholder_info = []
    example_json = [
    {
        "name": "6 Dimensions Capital",
        "shares": 119890000
    },
    {
        "name": "6 Dimensions Affiliates",
        "shares": 6310000
    },
    {
        "name": "6 Dimensions Capital GP, LLC",
        "shares": 126200000
    }
    ]
    response = ask_ollama(text, f"Extract all the information of non-freefloat shareholders and directors, and their respective number of long position shares, from the following text. Only output a JSON object with the format {{'name': 'string', 'shares': number}}: {text}. Please only print the JSON object without any additional texts, the following is an example. {example_json}")
    
    # Extract the JSON part from the response text
    start = response.find('[')
    end = response.rfind(']') + 1
    json_str = response[start:end]
    # Replace single quotes with double quotes to make it valid JSON
    json_str = json_str.replace("'", '"') 
    info = json.loads(json_str)
    shareholder_info.append(info)
    return shareholder_info

pdf_url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2023/0913/2023091300309.pdf'
keywords = ['SFO', 'Securities and Futures Ordinance']  # Add more keywords as needed

# Analyze the string array
texts = extract_text_from_pdf_with_keywords(pdf_url=pdf_url, keywords=keywords)
results = analyze_texts_with_ollama(texts)

# Output the results
for i, result in enumerate(results):
    print(f"Section {i + 1} contains information about non-freefloat shareholders: {result}")

    if result:
        data = extract_shareholder_info(texts[i])
        print(json.dumps(data, indent=4))

