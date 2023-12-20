from datetime import timedelta, datetime
import random, string
import json
from decimal import *

context = getcontext()
context.prec = 128
context.rounding = ROUND_UP

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str('{:f}'.format(o))
        return super().default(o)

def dumps(data):
    return json.dumps(data, sort_keys=True, default=str, cls=DecimalEncoder)

def get_pandas_time(time_unit) -> str:
    return {
        'second': '1s',
        'minute': '1Min',
        'hour': '1H',
        'day': '1Day',
    }[time_unit]

def get_timedelta(time_unit) -> timedelta:
    return {
        'second': timedelta(seconds=1),
        'minute': timedelta(minutes=1),
        'hour': timedelta(hours=1),
        'day': timedelta(days=1),
    }[time_unit]

def get_datetime_range(start_date, end_date,time_unit='day') -> list:
    date_range =[]
    delta = get_timedelta(time_unit)
    while start_date < end_date:
        date_range.append(start_date)
        start_date += delta
    return date_range

def split_float(num) -> tuple:
    if isinstance(num, float) or isinstance(num, str) or isinstance(num, int) or isinstance(num, Decimal):
        try:
            return format(num, '.33f').split('.')
        except:
            return (num,0)
    else:
        return(0,0)
        # raise TypeError('num must be a float, int, string, or Decimal')

def prec(num, places=18, rounding='up') -> Decimal:
    """
    Set the precision of a Decimal `num` to a number of `places`.
    The `rounding` argument can be set to 'up' or 'down' to specify the rounding mode.
    """
    if type(num) is float:
        raise TypeError('num cannot accept floats, it must be an int, string, or Decimal')
    if type(num) is int:
        num = str(num)
    
    if rounding == 'up':
        rounding_mode = ROUND_UP
    elif rounding == 'down':
        rounding_mode = ROUND_DOWN
    else:
        raise ValueError("rounding must be set to 'up' or 'down'")
    
    return Decimal(num).quantize(Decimal(10) ** -places, rounding=rounding_mode)

def non_zero_prec(num, places=18) -> Decimal:
    """
    Set the precision of a Decimal `num` to a number of `places`.
     
    Always round down first.
    If rounding down will result in zero, round up instead.
    """
    result = prec(num, places, rounding='down')
    if result == 0:
        result = prec(num, places, rounding='up')
    return result

def get_minimum(places: int) -> Decimal:
    """
    Returns the smallest decimal possible for the given number of places.
    """
    smallest_num = Decimal(1) / (10 ** places)
    return prec(smallest_num, places, rounding='down')

def to_sub_unit(self, amount, precision=8) -> int:
    """
    Converts primary units to subunits i.e. `BTC -> sats` , `ETH -> wei`
    """
    self.logger.debug('to_sub_unit', amount, precision)
    amount_decimal = str(amount).split('.') 
    if len(amount_decimal) == 2:
        amount_places = len(amount_decimal[1])
        if amount_places > precision:
            return FloatingPointError(f"amount {str(amount)} cannot have more than {precision} decimal places") 
    return int(float(amount) * (10 ** precision ))

def to_primary_unit(self, amount, precision=8) -> Decimal:
    """
    Converts subunits to primary units i.e. `sats -> BTC`, `wei -> ETH`
    """
    amount_len = len(str(amount))
    if amount_len > 15:
        return(Decimal(str(amount)[:-8]+'.'+str(amount)[-8:]))
    return prec(str(amount / (10 ** precision )), precision)

def convert_unit(self, amount, base_precision=8) -> int:
    """
    Converts between units i.e. `sats -> cents`, `wei -> sats`

    Args:
        amount (int): the amount of base unit to convert to quote unit
        base_precision (int, optional): the precision of the base unit. Defaults to 8.
    """
    return prec(str(amount / (10 ** base_precision )), 0)

def get_random_string(length=9) -> str:
    x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))
    return x

def format_dataframe_rows_to_dict(df) -> list:
    result_list = []
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        if(isinstance(index, datetime)):
            row_dict['dt'] = index.strftime("%m/%d/%Y, %H:%M:%S")
        result_list.append(row_dict)
    return result_list

def string_to_time(string) -> datetime:
    if(type(string) is datetime): return string
    return datetime.strptime(string, '%Y-%m-%d %H:%M:%S')

def generate_names(num_to_gen=20) -> list:
    """
    A function that randomly generates one to five letter names
    """
    names = []
    for i in range(num_to_gen):
        name = ''
        for j in range(random.randint(1,5)):
            name += random.choice(string.ascii_letters)
        if name not in names:    
            names.append(name)
        else:
            i -= 1
    return names

def generate_address() -> str:
    """
    Generates a random string of letters and numbers to represent a wallet address
    """
    length = random.randint(26, 35)
    if not isinstance(length, int) or length < 1:
        raise ValueError("Length must be a positive integer")
    characters = string.ascii_letters + string.digits
    return '0x'+''.join(random.choice(characters) for _ in range(length))    

def validate_address(address:str) -> bool:
    """
    Validates a wallet address
    """
    if not isinstance(address, str):
        raise TypeError("Address must be a string")
    return len(address[2:]) > 26 or len(address[2:]) < 35 and address[:2] == '0x'

def convert_sci_to_str(num):
    return "{:f}".format(num)