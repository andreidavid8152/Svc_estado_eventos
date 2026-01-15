# Non functional tests (cronjob service)

Simple response time checks for the cronjob service endpoint.

Examples (PowerShell)
- `python non_functional_tests\observe_cronjob_response_time.py`
- `python non_functional_tests\observe_cronjob_response_time.py --base-url http://127.0.0.1:8001 --path /health`
- `python non_functional_tests\observe_cronjob_response_time.py --count 10 --pause-ms 200`

Notes
- Default URL: `CRONJOB_URL` + `/health`.
- Use `--url` to pass a full URL if needed.
