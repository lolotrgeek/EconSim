from datetime import timedelta, datetime
import random, string


def get_pandas_time(time_unit):
    return {
        'second': '1s',
        'minute': '1Min',
        'hour': '1H',
        'day': '1Day',
    }[time_unit]

def get_timedelta(time_unit):
    return {
        'second': timedelta(seconds=1),
        'minute': timedelta(minutes=1),
        'hour': timedelta(hours=1),
        'day': timedelta(days=1),
    }[time_unit]

def get_datetime_range(start_date, end_date,time_unit='day'):
    date_range =[]
    delta = get_timedelta(time_unit)
    while start_date < end_date:
        date_range.append(start_date)
        start_date += delta
    return date_range


def get_random_string(length=9):
    x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))
    return x

def format_dataframe_rows_to_dict(df):
    result_list = []
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        if(isinstance(index, datetime)):
            row_dict['dt'] = index.strftime("%m/%d/%Y, %H:%M:%S")
        result_list.append(row_dict)
    return result_list