import requests


### Location Search
url = "https://api.content.tripadvisor.com/api/v1/location/search?key=CB94764D7AA2439988928C819D12845A&searchQuery=madrid&category=restaurants&latLong=40.4167047%2C-3.7035825&radius=20&radiusUnit=km&language=es"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)



### Location Details
url = "https://api.content.tripadvisor.com/api/v1/location/2086925/details?key=CB94764D7AA2439988928C819D12845A&language=es&currency=EUR"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)




url = "https://api.content.tripadvisor.com/api/v1/location/2086925/reviews?key=2086925&key=CB94764D7AA2439988928C819D12845A&language=es&limit=10"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)