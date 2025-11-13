import os 
import sys

os.environ["SNS_SECURITY_TOPIC_ARN"] = "arn:aws:sns:fake-security"
os.environ["SNS_COST_TOPIC_ARN"] = "arn:aws:sns:fake-cost"
os.environ["SNS_INFRA_TOPIC_ARN"] = "arn:aws:sns:fake-infra"
os.environ["BEDROCK_REGION"] = "eu-north-1"

from unittest.mock import MagicMock, patch 
import json
import pytest 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import handler


fake_event = {
    "source": "aws.ec2",
    "detail-type": "AWS API Call via CloudTrail",
    "detail": {
        "eventName": "StartInstances",
        "userIdentity": {
            "type": "IAMUser",
            "userName": "test-user"
        }
    }
}

@pytest.fixture
def mock_bedrock_invoke():
    with patch('handler.bedrock_client') as mock_bedrock:
        mock_invoke = mock_bedrock.invoke_model
        mock_invoke.return_value = {
            "body": MagicMock(read=lambda: b'{"results":[{"outputText":"{\\"category\\": \\"infra\\", \\"confidence\\":0.9, \\"reason\\":\\"EC2 start event\\"}"}]}')
        }
        yield mock_invoke

@pytest.fixture
def mock_sns_publish():
    with patch('handler.sns') as mock_sns:
        mock_publish = mock_sns.publish
        yield mock_publish

def test_classify_event(mock_bedrock_invoke):
    result = handler.classify_event(fake_event)
    assert result["category"] == "infra"
    assert result["confidence"] == 0.9
    assert "ec2 start event" in result["reason"]

def test_lambda_handler(mock_bedrock_invoke, mock_sns_publish):
    response = handler.lambda_handler(fake_event, None)
    
    mock_bedrock_invoke.assert_called_once()
    
    mock_sns_publish.assert_called_once()

    assert response["category"] == "infra"