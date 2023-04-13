# openimis-loadtest

This repository contains the load test scripts for OpenIMIS. 
The scripts are written in Python and use the Locust framework.
They were running in legacy mode too but newer addition might not support this dual mode anymore.

## Running the tests

Prepare a venv and install locust.io:

    python3 -m venv venv
    source venv/bin/activate
    pip install locust

Run the web server:
    
    locust
    .../INFO/locust.main: Starting web interface at http://0.0.0.0:8089 (accepting connections from all network interfaces)
    .../INFO/locust.main: Starting Locust 2.15.1

For more specific run options:

    locust -f locustfile.py --host=https://release.openimis.org

Open the web interface in your browser: http://localhost:8089

## Configuring the tests

The beginning of the locustfile.py contains the configuration of the tests:

    LEGACY_LOGIN = True
    SITE_USER = "Admin"
    SITE_PASSWD = "admin123"
    INSUREE_IDS = ["070707071"]
    API_ROOT = "/iapi" if LEGACY_LOGIN else "/api"  # api or ipai, feel free to override if necessary
    HF_UUID = "E4C10505-AFC5-4E44-9E70-C9993B3CEE4B"  # Release
    HF_PARENT_UUID = "1DBB7008-9CF8-4D1E-9AAD-1487DD0E813E"  # Release

## Debugging the tests

To start the tests in the debugger, check the documentation at https://docs.locust.io/en/stable/running-in-debugger.html

For PyCharm, more detailed instructions are to run as a remote debugger:
https://github.com/locustio/locust/issues/613#issuecomment-362735152


