from source.Messaging import Subscriber
time_puller = Subscriber(5114)

def get_time():
    clock = time_puller.subscribe("time")
    if clock == None: 
        pass
    elif type(clock) is not str:
        pass
    else:
        return clock


if __name__ == '__main__':
    while True:
        time= get_time()
        print(time)