import argparse
import run_master
import run_replica
import logging
logging.basicConfig(level = logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Example script with -m and -s options.")
    parser.add_argument("-m", "--master", action="store_true", help="Master node")
    parser.add_argument("-s", "--secondary", nargs="+", help="Replica nodes")

    args = parser.parse_args()

    if args.master:
        print("Master: True")
        replicas = []

        if args.secondary:
            replicas = args.secondary
            print("Secondaries:", args.secondary)
        
        run_master.setup(replicas)
    else:
        run_replica.setup()
