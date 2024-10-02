import csv
import requests
from pdfminer.high_level import extract_text
from io import BytesIO, StringIO


def crawl_monthly_return(url,code):
    
    # packages used: pdfminer
    # Fetch the PDF from the web
    response = requests.get(url)

    # Load the PDF into BytesIO
    pdf_file = BytesIO(response.content)

    # Extract text from PDF
    pdf_contents = extract_text(pdf_file)

    #store contents to list
    contents = list(filter(None, pdf_contents.split('\n')))
        

    # Extracting Part II data from the html(pdf) file
    # stored in List (Filtered)
            
    Filtered = []
    isData = False
        
    for x in contents:
        if 'Movements in Issued Shares' in x:
            isData = True
        if 'Details of Movements in Issued Shares' in x:
            isData = False
        if (isData == True):
            Filtered.append(x)

    print(Filtered)

    # Filter out the useful data
    # Extracted data stored in Dictionary (data)
    data = {}
    isHshares = 0
    sharesAmount = 0
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
                    
    data["total_shares"] = sharesAmount
    # return function    
    return data
# enf of function

''''''

url = []
companyCode = []
with open('index-innovation-challenge-student-s/faf_documents.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in spamreader:
        if 'www1.hkexnews.hk/listedco' in row[1]:
            companyCode.append(row[0])
            url.append(row[1])

# open output csv file
with open('Total_shares.csv', 'w', newline='') as SharesFile:
    spamwriter = csv.writer(SharesFile, delimiter = '\0')
            
    # loop for each url
    for y in range(len(companyCode)):
        data = crawl_monthly_return(url[y], companyCode[y])
        output = ['{stock_code:' + data["stock_code"] + ',total_shares:' + str(data["total_shares"]) + '}']
        spamwriter.writerows(output)
        print(output)













        
