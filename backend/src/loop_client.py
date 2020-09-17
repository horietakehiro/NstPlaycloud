from transfer.client import transfer_client
import time

if __name__ == "__main__":
    # loop client's main function
    while True:
        resp = transfer_client.main()
        print(resp)

        time.sleep(10)



