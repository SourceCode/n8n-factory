import logging
from n8n_factory.logger import SecretFilter

def test_secret_masking():
    filter = SecretFilter()
    
    # Test 1: Simple assignment
    record = logging.LogRecord("name", logging.INFO, "path", 1, "api_key=123456", (), None)
    filter.filter(record)
    assert "api_key=***MASKED***" in record.msg
    
    # Test 2: Password
    record = logging.LogRecord("name", logging.INFO, "path", 1, "password: mypassword", (), None)
    filter.filter(record)
    assert "password=***MASKED***" in record.msg
    
    # Test 3: SK Key
    record = logging.LogRecord("name", logging.INFO, "path", 1, "sk-12345678901234567890", (), None)
    filter.filter(record)
    assert "sk-***MASKED***" in record.msg 
    assert "1234567890" not in record.msg