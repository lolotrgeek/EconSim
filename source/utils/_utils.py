from datetime import timedelta, datetime
import random, string
import json
from decimal import *

context = getcontext()
context.prec = 36
context.rounding = ROUND_UP

def dumps(data):
    return json.dumps(data, indent=4, sort_keys=True, default=str)

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

def prec(num, places=18) -> Decimal:
    """
    Set the precision of a Decimal `num` to a number of `places`.
    """
    if type(num) is float:
        raise TypeError('num cannot accept floats, it must be a int, string, or Decimal')
    if type(num) is int:
        num = str(num)
    return Decimal(num).quantize(Decimal(10) ** -places)

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