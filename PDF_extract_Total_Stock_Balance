import aspose.words as aw
from parsel import Selector
import csv

#from bs4 import BeautifulSoup
#import urllib3
#import re
#import mechanize

# extract monthly return urls from faf_doc, stor in List(url)
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

        # save web file to html (idk if there are any other method that do not require file saving)
        # packages used: aw
        loadOptions = aw.loading.PdfLoadOptions()
        loadOptions.skip_pdf_images = True
        webFile = aw.Document(url[y], loadOptions)
        webFile.save('output.html')

        #file open and read
        #file content saved as String (content)
        with open('output.html', 'r') as file:
            content = file.read()

        # List (description) is the text extracted from the html script
        html_selector = Selector(text=content)
        description = html_selector.css('span::text').getall()


        # Extracting Part II data from the html(pdf) file
        # stored in List (Filtered)
        Filtered = []
        isData = False
        
        for x in description:
            if 'Movements in Issued Shares' in x:
                isData = True
            if 'Details of Movements in Issued Shares' in x:
                isData = False
                
            if (isData == True):
                dataElement = x.replace('\xa0', '')
                Filtered.append(dataElement)
                
        # Extract Stock Balance from List(Filtered)
        # save to CSV file
        for x in range(len(Filtered)):
            if (Filtered[x] == 'Balance at close of the month'):
                cleanedData = [companyCode[y] + ',' + Filtered[x+1].replace(",", "")]
                #print(cleanedData)
                spamwriter.writerows(cleanedData)

