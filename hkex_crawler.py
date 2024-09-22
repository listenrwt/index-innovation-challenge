import pandas as pd
import requests
from bs4 import BeautifulSoup
import json

# Load the CSV file
data = pd.read_csv('index-innovation-challenge-student-s-1/faf_documents.csv')

# Base URL for the extracted links
base_url = 'https://di.hkex.com.hk/di/'

# Prepare lists for extracted information
stock_codes, corporation_names = [], []
substantial_shareholders_urls, notices_urls = [], []
substantial_shareholders_data, notices_data = [], []

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

# Open JSON file for writing
with open('hkex_data.json', 'w') as json_file:
    # Fetch and extract data from the URLs in the SDI column
    for sdi in data['SDI'].to_numpy():
        try:
            response = requests.get(sdi)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'grdPaging'})

            if not table:
                print(f"No table found for {sdi}")
                continue

            for row in table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) < 3: continue

                stock_code = cols[0].get_text(strip=True)
                corporation_name = cols[1].get_text(strip=True)
                links = [a['href'] for a in cols[2].find_all('a')]

                stock_codes.append(stock_code)
                corporation_names.append(corporation_name)
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

                # Write record to JSON file
                json.dump(record, json_file, indent=4)
                json_file.write(",\n")  # Add a comma for separation

            print(f"Data extracted from {sdi}.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {sdi}: {e}")

print("Data extraction completed. JSON file generated.")