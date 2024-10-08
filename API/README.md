# TimeSpace AI API

## Installation

Recommended to run in a virtual environment, and required to use a python version 3.10.7 or later for GCal scripts

Run `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib` and `pip install semantic_kernel` in your virtual environment to install necessary packages.

## Credentials

Vist https://console.cloud.google.com/apis/credentials?project=timespace-436321 and log in with TimeSpace credentials. Find 'Desktop client 1' under 'OAuth 2.0 Client IDs' and under 'Actions' click the download icon and press 'Download JSON'. Save this file as `credentials.json` in your `API` directory. This should allow authentication, and the first time you run it will bring you to the OAuth consent screen in the browser, and generate a `token.json`, which will authenticate subsequent requests. If you delete this file you will again be redirected to the OAuth consent screen in the browser.

## Running

Run `python events_initializer.py` to run simple init script.
