. activate bifrost
export REPORTER_ADMIN=True
uwsgi -s /tmp/run_checker.sock --processes 3 --manage-script-name --mount /=run_checker:server --http :8051