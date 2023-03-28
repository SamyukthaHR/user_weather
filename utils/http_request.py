import requests


def make_get_request(url):
    headers = {'Accept': 'application/json'}
    try:
        response = requests.get(url,
                                headers=headers)
        print(response)
        data = response.json()
        return data
    except Exception as e:
        print(f'Exception occurred due to: {e}')
        return {}
