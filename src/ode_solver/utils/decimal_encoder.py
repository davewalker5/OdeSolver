import decimal
import json


class DecimalEncoder(json.JSONEncoder):
    """
    JSON encoder that's able to encode Decimal values
    """

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)
