import json
import aspose.words as aw
import urllib.request  
from bs4 import BeautifulSoup

# TODO: Ming: Complete the crawl_monthly_return function and return a JSON object. Also, use BeautifulSoup instead of Parsel for consistency.

def crawl_monthly_return(url):
    """
    Crawls the provided URL to extract total shares from the monthly return report.

    Args:
        url (str): The base URL for the PDF to be crawled.

    Returns:
        json: A JSON object containing the stock code and the total shares.
        
    #
    record = {"stock_code": "01477", "total_shares": 690903850}
    JSON Example: 
        {
            "stock_code": "01477",
            "total_shares": 690903850
        }
    """
    # save web file to html (idk if there are any other method that do not require file saving)
    # packages used: aw
    loadOptions = aw.loading.PdfLoadOptions()
    loadOptions.skip_pdf_images = True
    webFile = aw.Document(url, loadOptions)
    webFile.save('output.html')

    # second approach:

    # Extracting Part II data from the html(pdf) file
    # stored in List (Filtered)
    with open('output.html', 'r') as f:
        contents = f.read()
        soup = BeautifulSoup(contents, "html.parser")
        
        Filtered = []
        isData = False

        for x in soup(['span']):
            if 'Movements in Issued Shares' in x:
                isData = True
            if 'Details of Movements in Issued Shares' in x:
                isData = False
            if (isData == True):
                Filtered.append(x.text)    

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
                    
            if (Filtered[x] == 'Stock code' and isHshares == 1):
                data["stock_code"] = Filtered[x+1]
            if (Filtered[x] == 'Balance at close of the month'and isHshares == 1):
                sharesAmount += int(Filtered[x+1].replace(",", ""))
                
        data["total_shares"] = sharesAmount

    # return function    
    return data


#data = crawl_monthly_return("https://www1.hkexnews.hk/listedco/listconews/sehk/2024/0103/2024010302045.pdf")
data = crawl_monthly_return("https://www1.hkexnews.hk/listedco/listconews/sehk/2024/0102/2024010203048.pdf")

print(json.dumps(data, indent=4))
