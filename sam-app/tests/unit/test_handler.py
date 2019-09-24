import json

import pytest

from src import app


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "Records": [
            {
                "cf": {
                    "config": {
                        "distributionId": "EXAMPLE"
                    },
                    "request": {
                        "uri": "/baked/02776133-d49d-49cb-bfaa-67c7f61b25a1@8.14:301d5176-9ace-4219-b44b-85dcf781e1e3.html",
                        "method": "GET",
                        "clientIp": "2001:cdba::3257:9652",
                        "headers": {
                            "user-agent": [
                                {
                                    "key": "User-Agent",
                                    "value": "Test Agent"
                                }
                            ],
                            "host": [
                                {
                                    "key": "Host",
                                    "value": "d123.cf.net"
                                }
                            ],
                            "cookie": [
                                {
                                    "key": "Cookie",
                                    "value": "SomeCookie=1; AnotherOne=A; X-Experiment-Name=B"
                                }
                            ]
                        }
                    }
                }
            }
        ]
    }


# FIX ME: Get this test actually testing something useful
def test_lambda_handler(apigw_event, mocker):
    ret = app.lambda_handler(apigw_event, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert "message" in ret["body"]
    assert data["message"] == "hello world"
    # assert "location" in data.dict_keys()
