import json

# TODO: Ming: Complete the crawl monthly return function and returns a json object, also use beautifulsoup instead of parsel for consistancy

def crawl_monthly_return(url):
    """
    Crawls the provided URL to extract total shares on the monthly return report

    Args:
        url (str): The base URL for the pdf to be crawled.

    Returns:
        json: A json object containing the stock code and the total shares
    """
    
    record = {"stock_code": "01477", "total_shares": 690903850}
    
    """ JSON Example: 
        {
            "stock_code": "01477",
            "total_shares": 690903850
        }
    """
    return record


data = crawl_monthly_return("https://www1.hkexnews.hk/listedco/listconews/sehk/2024/0103/2024010302045.pdf")
print(json.dumps(data, indent=4))