import requests
import os
# translate CUIs into SNOMED Ids
def crosswalk(cui):
    headers = {'Accept': 'application/xml'}
    data = {"data": cui}
    mapping = requests.post(f"{os.environ['METAMAP_WEB_URL']}crosswalk", data = data)
    print(mapping.text)
    return mapping.text.splitlines()
    
