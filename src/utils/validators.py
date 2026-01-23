"""Validation utilities for stock picks and trading"""

def validate_ticker(ticker):
    """Validate stock ticker format"""
    if not ticker:
        return False
    
    # Ticker should be 1-5 uppercase letters
    if not isinstance(ticker, str):
        return False
    
    if len(ticker) < 1 or len(ticker) > 5:
        return False
    
    if not ticker.isalpha() or not ticker.isupper():
        return False
    
    return True

def validate_confidence(confidence):
    """Validate confidence score (0.0-1.0)"""
    try:
        conf = float(confidence)
        return 0.0 <= conf <= 1.0
    except (ValueError, TypeError):
        return False

def validate_weight(weight):
    """Validate portfolio weight percentage"""
    if weight is None:
        return True  # Weight is optional
    
    try:
        w = float(weight)
        return 0.0 < w <= 100.0
    except (ValueError, TypeError):
        return False

def validate_pick(pick):
    """Validate a complete stock pick dictionary"""
    required_fields = ['ticker', 'action', 'confidence', 'option_type', 'urgency', 'sentiment', 'reasoning']
    
    # Check required fields
    for field in required_fields:
        if field not in pick:
            return False, f"Missing required field: {field}"
    
    # Validate ticker
    if not validate_ticker(pick['ticker']):
        return False, f"Invalid ticker: {pick['ticker']}"
    
    # Validate action
    if pick['action'] not in ['BUY', 'SELL', 'HOLD']:
        return False, f"Invalid action: {pick['action']}"
    
    # Validate confidence
    if not validate_confidence(pick['confidence']):
        return False, f"Invalid confidence: {pick['confidence']}"
    
    # Validate weight if present
    if not validate_weight(pick.get('weight')):
        return False, f"Invalid weight: {pick.get('weight')}"
    
    # Validate option_type
    if pick['option_type'] not in ['STOCK', 'CALL', 'PUT']:
        return False, f"Invalid option_type: {pick['option_type']}"
    
    # Validate urgency
    if pick['urgency'] not in ['LOW', 'MEDIUM', 'HIGH']:
        return False, f"Invalid urgency: {pick['urgency']}"
    
    # Validate sentiment
    if pick['sentiment'] not in ['BULLISH', 'BEARISH', 'NEUTRAL']:
        return False, f"Invalid sentiment: {pick['sentiment']}"
    
    return True, None
