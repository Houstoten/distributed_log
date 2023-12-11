# distributed_log
Distributed Log app

Iterations 2 and 3 are easily testable, however for third iteration it's required to run master and secondaries without docker-compose.

It can be done like so:

`python run.py -m -s localhost:50051 localhost:50052` - for master

`python run.py` - for secondaries.

The app is designed to run in docker via port-forwarding, so port for secondaries must be changed by hand if wanted to run manually. (In `run_replica.py` for REST endpoint and in `replica_service.py` for GRPC)
