import requests
from bs4 import BeautifulSoup
import json
from pdfminer.high_level import extract_text
from io import BytesIO
import pandas as pd

model_name = 'llama3.2:latest' #"llama3.1:latest"
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

def ask_the_same_name(name1, name2):
        response = ask_ollama(f"Define the company\'s name, or the individual\'s name, as \"Name\". \"Characters\" are substrings delimited by \" \" in \"Name\". Define the two \"Name\"s as \"same\" if and ONLY if the \"Characters\" of the two \"Name\" are equal, but note that the order of \"Character\" can be different. Now, determine if the companies\', or the individual\'s \"Name\"s, which is {name1} and {name2} respectively,  are the \"same\". If \"same\" is obtained, return \"True\", else, return \"False\".")
        return "True" in response

def crawl_monthly_return(url,code):
    """
    Crawls the provided URL to extract total shares on the monthly return report

    Args:
        url (str): The base URL for the pdf to be crawled.
        code (str): The stock code for the PDF to be crawled. ("1787.HK")

    Returns:
        json: A json object containing the stock code and the total shares
    """    

    '''
    Part 1
    # packages used: pdfminer
    # Fetch the PDF from the web and extract text from the file
    '''
    response = requests.get(url)

    # Load the PDF into BytesIO
    pdf_file = BytesIO(response.content)

    # Extract text from PDF
    pdf_contents = extract_text(pdf_file)

    #store contents to list
    contents = list(filter(None, pdf_contents.split('\n')))
        
    '''
    Part 2
    Extracting Part II data from the PDF string 'contents'
    Extracted raw Part II data is stored in List (Filtered)
    '''
            
    Filtered = []
  
    # Function to Select Part II of the PDF
    isData = False   
    for x in contents:
        if 'Movements in Issued Shares' in x:
            isData = True
        if 'Details of Movements in Issued Shares' in x:
            isData = False
        if (isData == True):
            Filtered.append(x)

    #print(Filtered)  # test line, prints the Part II text in (List) form

    '''
    Part 3
    Filter out the useful data from Part II text
    Extracted data stored in Dictionary (data)
    '''
  
    data = {}
    isHshares = 0    #parameter to check whether the stock is 港股
    sharesAmount = 0

    '''
    Loop through the List of texts in Part II of pdf, and then extract the total number of H shares.
    Extracted data MUST satisfy:
      1. stock type = 'H', or 'Not applicable'
      2. double check the stock code on the PDF, and the code is the same as input
    After finishing the data extraction, add a '0' to Stock code
      E.g. '1477.HK' -> '01477'
    '''
    for x in range(len(Filtered)):
        if (Filtered[x] == 'Type of shares'):
            if (Filtered[x+1] ==  'H' or Filtered[x+1] == 'Not applicable'):
                isHshares = 1
            else:
                isHshares = 0
        if (Filtered[x] == 'Stock code'):
            if (isHshares == 1 and Filtered[x+1] == ('0'+code).replace('.HK','')):
                isHshares = 1
            else:
                isHshares = 0

        if (Filtered[x] == 'Balance at close of the month' and isHshares == 1):
            data["stock_code"] = ('0'+code).replace('.HK','')
            sharesAmount += int(Filtered[x+1].replace(",", ""))

    # store data 
    data["total_issued_shares"] = sharesAmount   

    """ JSON Example: 
        {
            "stock_code": "01477",
            "total_issued_shares": 690903850
        }
    """
    return data

#data = crawl_monthly_return("https://www1.hkexnews.hk/listedco/listconews/sehk/2024/0102/2024010201366.pdf", "1787.HK")
#print(data["total_issued_shares"])

# Fetch and extract data from the URLs in the SDI column
def crawl_sdi(url):
    """
    Crawls the provided URL to extract data on substantial shareholders and notices.

    Args:
        url (str): The base URL for the sdi page to be crawled.

    Returns:
        json: A json object containing extracted information, including a list of substantial
            shareholders and notices. 

    Raises:
        requests.exceptions.RequestException: If an error occurs during the request.
    """
    def fetch_form(urls, name_field):
        data_list = []
        for url in urls:
            if url:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the data table
                data_table = soup.find('table', {'id': 'grdPaging'})
                if data_table:
                    for sub_row in data_table.find_all('tr')[1:]:  # Skip header
                        sub_cols = sub_row.find_all('td')
                        if len(sub_cols) >= 2:
                            name = sub_cols[1].get_text(strip=True)
                            url = base_url + sub_cols[0].find('a')['href'] if sub_cols[0].find('a') else None
                            
                            shares = None
                            sum_of_derivatives = 0
                            event_date = None
                            
                            if url:
                                url_response = requests.get(url)
                                url_response.raise_for_status()
                                url_soup = BeautifulSoup(url_response.text, 'html.parser')

                                date_span = url_soup.find('span', id='lblDEventDate')
                                event_date = date_span.get_text(strip=True).split('(')[0] if date_span else None

                                shares_table = url_soup.find('table', {'id': 'grdSh_AEvt'})
                                if shares_table:
                                    shares = []
                                    for row in shares_table.find_all('tr')[1:]:  # Skip header
                                        cols = row.find_all('td')
                                        total_number_of_shares = int(cols[1].get_text(strip=True).replace(',', ''))
                                        percentage = float(cols[2].get_text(strip=True))
                                        shares.append({"total_number_of_shares": total_number_of_shares, "percentage_figure": percentage})

                                derivatives_table = url_soup.find('table', {'id': 'grdDer_Dir'})
                                if derivatives_table:
                                    for row in derivatives_table.find_all('tr')[1:]:  # Skip header
                                        cols = row.find_all('td')
                                        derivative_str = cols[len(cols) - 1].get_text(strip=True).replace(',', '')
                                        if derivative_str.lstrip('-').isdigit():
                                            sum_of_derivatives += int(derivative_str)
                                
                            data_list.append({
                                name_field: name,
                                "date_of_relevant_event": event_date,
                                "long_position": shares,
                                "total_number_of_derivatives": sum_of_derivatives,
                            })
        return data_list

    # Base URL for the extracted links
    base_url = 'https://di.hkex.com.hk/di/'
    
    # Prepare lists for extracted information
    substantial_shareholders_urls, notices_urls = [], []
    substantial_shareholders_data, notices_data = [], []
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'grdPaging'})

        if not table:
            print(f"No table found for {url}")
            return 

        for row in table.find_all('tr')[1:]:  # Skip header
            cols = row.find_all('td')
            if len(cols) < 3: continue

            stock_code = cols[0].get_text(strip=True)
            corporation_name = cols[1].get_text(strip=True)
            links = [a['href'] for a in cols[2].find_all('a')]

            substantial_shareholders_urls.append(base_url + links[1] if len(links) > 1 else None)
            notices_urls.append(base_url + links[5] if len(links) > 5 else None)

            # Fetch substantial shareholders data
            substantial_shareholders_data = fetch_form(substantial_shareholders_urls, "name_of_substantial_shareholder")
            # Fetch notices data
            notices_data = fetch_form(notices_urls, "name_of_noticed_shareholder")

            # Prepare the record
            record = {
                'stock_code': stock_code,
                'name_of_listed_corporation': corporation_name,
                'consolidated_list_of_substantial_shareholders': substantial_shareholders_data,
                'list_of_all_notices': notices_data,
            }

        #print(f"Data extracted from {url}.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    
    #print("Data extraction completed. JSON object generated.")

    """ JSON Example: 
        {
            "stock_code": "01477",
            "name_of_listed_corporation": "Ocumension Therapeutics - B",
            "consolidated_list_of_substantial_shareholders": [
                {
                    "name_of_substantial_shareholder": "6 Dimensions Capital GP, LLC",
                    "date_of_relevant_event": "21/12/2021",
                    "long_position": [
                    {
                        "total_number_of_shares": 126200000,
                        "percentage_figure": 18.92
                    }
                    ],
                    "total_number_of_derivatives": 0
                },
                {
                    "name_of_substantial_shareholder": "CHEN Ziqing",
                    "date_of_relevant_event": "21/12/2021",
                    "long_position": [
                    {
                        "total_number_of_shares": 126200000,
                        "percentage_figure": 18.92
                    }
                    ],
                    "total_number_of_derivatives": 0
                },
            ],
            "list_of_all_notices": [
                {
                    "name_of_noticed_shareholder": "Hu Zhaopeng",
                    "date_of_relevant_event": "13/12/2023",
                    "long_position": [
                    {
                        "total_number_of_shares": 4204658,
                        "percentage_figure": 0.6
                    }
                    ],
                    "total_number_of_derivatives": 564885
                },
                {
                    "name_of_noticed_shareholder": "Hu Zhaopeng",
                    "date_of_relevant_event": "11/12/2023",
                    "long_position": [
                    {
                        "total_number_of_shares": 4206585,
                        "percentage_figure": 0.6
                    }
                    ],
                    "total_number_of_derivatives": 564885
                }
            ]
        }  
    """  
    return record

#data = crawl_sdi("https://di.hkex.com.hk/di/NSSrchCorpList.aspx?sa1=cl&scsd=01/07/2023&sced=31/12/2023&sc=1477&src=MAIN&lang=EN&g_lang=en")
#print(json.dumps(data, indent=4))

import pandas as pd
from tqdm import tqdm
from datetime import datetime

# Load the CSV file
data = pd.read_csv('provided_data/faf_documents.csv')
required = pd.read_csv('provided_data/sample_submission.csv')
pdf_data = None
with open('output.json', 'r') as file:
    pdf_data= json.load(file)
required_codes = required['ID'].to_numpy()
stock_codes = []
outputs = []

# Initialize tqdm for the progress bar
for index, row in tqdm(data.iterrows(), total=len(data), desc="Processing"):

    code = row["RIC"]
    
    if not (code in required_codes):
        continue

    pdf_obj = None
    for item in pdf_data:
        if item['code'] == code:
            pdf_obj = item['data']
            break   


    stock_codes.append(code)
    # crawl data
    total_issued_shares = crawl_monthly_return(row["Monthly Return"], code)["total_issued_shares"]
    sdi_data = crawl_sdi(row["SDI"])

    # calculate threshold
    threshold_shares = total_issued_shares * 0.05

    # initialize answer
    freefloat = total_issued_shares

    # Get substantial 
    for substantial_shareholder in sdi_data["consolidated_list_of_substantial_shareholders"]:
        original_shares = substantial_shareholder["long_position"][0]["total_number_of_shares"] - substantial_shareholder["total_number_of_derivatives"]
        # Check if the code exists in pdf_data and matches the current shareholder
        if pdf_obj:
            for pdf_entry in pdf_obj:
                if ask_the_same_name(pdf_entry["name"], substantial_shareholder["name_of_substantial_shareholder"]):
                    # Check if the date exists and is in the correct format
                    try:
                        if pdf_entry["date"] == '':
                            pdf_entry["date"] = '30/06/2023'
                        pdf_date = datetime.strptime(pdf_entry["date"], "%d/%m/%Y")
                        sdi_date = datetime.strptime(substantial_shareholder["date_of_relevant_event"], "%d/%m/%Y")
                        
                        # Use pdf_data shares if sdi_date is older and shares exist in pdf_data
                        if sdi_date < pdf_date and "shares" in pdf_entry:
                            shares = int(pdf_entry["shares"])  
                        else:
                            shares = original_shares
                    except ValueError:
                        # Date format is incorrect, use original shares
                        shares = original_shares
                    break
            else:
                # Shareholder not found in pdf_data, use original shares
                shares = original_shares
        else:
            # Code doesn't match or doesn't exist, use original shares
            shares = original_shares
        
        if shares >= threshold_shares:
            freefloat -= shares
            if freefloat <= 0:
                freefloat += shares
                continue

    # Get unique notices
    # Dictionary to store the most recent notice for each shareholder
    notices_dict = {} 
    for notice in sdi_data["list_of_all_notices"]:
        name = notice["name_of_noticed_shareholder"]
        if notice["date_of_relevant_event"] is None:
            continue
        date = datetime.strptime(notice["date_of_relevant_event"], "%d/%m/%Y")
        if name not in notices_dict or date > notices_dict[name]["date"]:
            notices_dict[name] = notice
            notices_dict[name]["date"] = date
            
    # Convert the dictionary back to a list
    unique_notices = list(notices_dict.values())
    for notice in unique_notices:
        shares = notice["long_position"][0]["total_number_of_shares"] - notice["total_number_of_derivatives"]
        if shares >= total_issued_shares * 0.35:
            freefloat -= shares 
            if freefloat <= 0:
                freefloat += shares
                continue 

    freefloat /= total_issued_shares
    
    outputs.append(freefloat)

# Create a DataFrame with the collected data
result_df = pd.DataFrame({
    "ID": stock_codes,
    "outputs": outputs
})

# Save the DataFrame to a CSV file
result_df.to_csv('output.csv', index=False)
