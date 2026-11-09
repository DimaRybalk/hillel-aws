import time
import json
import importlib.util
import pytest

spec = importlib.util.spec_from_file_location("url_shortener", "lambda/url_shortener.py")
url_shortener = importlib.util.module_from_spec(spec)
spec.loader.exec_module(url_shortener)

@pytest.fixture(autouse=True)
def mock_dynamo(monkeypatch):
    store = {}
    class FakeTable:
        def put_item(self, Item):
            store[Item['short_key']] = Item
        def get_item(self, Key):
            item = store.get(Key['short_key'])
            return {'Item': item} if item else {}
    monkeypatch.setattr(url_shortener, 'table', FakeTable())
    return store

def test_shorten_url_success():
    event = {
        'httpMethod': 'POST',
        'path': '/shorten',
        'body': json.dumps({'url': 'https://aws.amazon.com'})
    }
    res = url_shortener.lambda_handler(event, None)
    assert res['statusCode'] in (200, 201)
    data = json.loads(res['body'])
    assert 'short_key' in data

def test_redirect_active_link():
    post_event = {
        'httpMethod': 'POST',
        'path': '/shorten',
        'body': json.dumps({'url': 'https://github.com'})
    }
    post_res = url_shortener.lambda_handler(post_event, None)
    key = json.loads(post_res['body'])['short_key']

    get_event = {'httpMethod': 'GET', 'path': f'/{key}'}
    res = url_shortener.lambda_handler(get_event, None)
    assert res['statusCode'] == 301
    assert res['headers']['Location'] == 'https://github.com'

def test_links_expire(monkeypatch):
    post_event = {
        'httpMethod': 'POST',
        'path': '/shorten',
        'body': json.dumps({'url': 'https://python.org'})
    }
    post_res = url_shortener.lambda_handler(post_event, None)
    data = json.loads(post_res['body'])
    
    assert 'expires_at' in data, "expires_at must be in POST response"
    key = data['short_key']

    monkeypatch.setattr(time, 'time', lambda: data['expires_at'] + 60)

    get_event = {'httpMethod': 'GET', 'path': f'/{key}'}
    res = url_shortener.lambda_handler(get_event, None)
    assert res['statusCode'] == 404, "Expired link must return 404"