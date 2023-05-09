from spidey import app
import pytest

@pytest.fixture
def client(): # This function is used to get a test client for the tests
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

"""
Just a simple test to check if the server returns a 200 status code when a new scrape is triggered
GIVEN - Cold start into a new scrape
WHEN - The user triggers a new scrape (using the project's test url)
THEN - The server should return a 200 status code to indicate success
"""
def test_triggerSearch(client):
    response = client.get('/api/triggerScraping/https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm/300')
    assert response.status_code == 200