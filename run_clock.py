from source.Messaging import Pusher, Router
from source.Clock import Clock
from multiprocessing import Process
from time import sleep

def run_clock() -> None:
    try:
        p = Pusher(5115)
        clock = Clock()
        while True:
            clock.tick()
            msg = p.push({"time": str(clock.dt)})
    
    except KeyboardInterrupt:
        print("attempting to close clock..." )
        return


def route_clock(time_channel) -> None:
    try:
        r = Router(5115, time_channel )
        r.route()
    except Exception as e:
        print(e)
        return None
    except KeyboardInterrupt:
        print("attempting to close clock router..." )
        return None
    
def main() -> None:
    try:
        time_channel = 5114

        clock_process = Process(target=run_clock)
        clock_router = Process(target=route_clock, args=(time_channel, ))

        clock_router.start()
        clock_process.start()

        while True:
            sleep(.1)

    except KeyboardInterrupt:
        print("attempting to close processes..." )
        clock_process.terminate()
        clock_router.terminate()
        clock_process.join()
        clock_router.join()

if __name__ == '__main__':
    main()