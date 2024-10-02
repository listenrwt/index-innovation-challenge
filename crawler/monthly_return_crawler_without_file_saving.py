import csv
import requests
from pdfminer.high_level import extract_text
from io import BytesIO, StringIO

# enter Pdf URL, Stock Code to get the number of total stocks of the company.
def crawl_monthly_return(url,code):
    
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

    print(Filtered)  # test line, prints the Part II text in (List) form

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
                isHshares = 1;
            else:
                isHshares = 0;
        if (Filtered[x] == 'Stock code'):
            if (isHshares == 1 and Filtered[x+1] == ('0'+code).replace('.HK','')):
                isHshares = 1;
            else:
                isHshares = 0;

        if (Filtered[x] == 'Balance at close of the month' and isHshares == 1):
            data["stock_code"] = ('0'+code).replace('.HK','')
            sharesAmount += int(Filtered[x+1].replace(",", ""))

    # store data 
    data["total_shares"] = sharesAmount
    # return function    
    return data
  
# end of function

'''
Main Function, 
Extract PDF urls from the CSV files.
'''
url = []
companyCode = []
with open('index-innovation-challenge-student-s/faf_documents.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in spamreader:
        if 'www1.hkexnews.hk/listedco' in row[1]:
            companyCode.append(row[0])
            url.append(row[1])

'''
Open output csv file, 
call {crawl_monthly_return(url,code)} function, and 
then write the extracted data in 
{stock code: xxxx, total_shares: XXXXXXX} format
'''
with open('Total_shares.csv', 'w', newline='') as SharesFile:
    spamwriter = csv.writer(SharesFile, delimiter = '\0')
            
    # loop for each url
    for y in range(len(companyCode)):
        data = crawl_monthly_return(url[y], companyCode[y])
        output = ['{stock_code:' + data["stock_code"] + ',total_shares:' + str(data["total_shares"]) + '}']
        spamwriter.writerows(output)
        print(output)

