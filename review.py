import aiohttp
import asyncio
import async_timeout
from flask import Flask, request, abort


loop = asyncio.new_event_loop()
app = Flask(__name__)


# REVIEW COMMENT: incoming_2_outgoing_payload -> incoming_to_outgoing_payload.
async def incoming_2_outgoing_payload(payload):

    # REVIEW COMMENT: Incorrect spelling for `Convert`.
    """Conveert json to xml."""
    from decoder import Dict2XML
    # need to convert int keys to str, dict2xml can't handle int values
    return Dict2XML().parse({
        "vacation": {k: str(v) for k, v in payload.items()}})


async def fetch(url, payload):
    print("Triggering url {}".format(url))
    # REVIEW COMMENT: This conversion should not happen in fetch function, fetch should only be responsible for
    # sending request, the caller should give the final payload to be sent.
    body = incoming_2_outgoing_payload(payload)

    async with aiohttp.ClientSession() as session, \
            async_timeout.timeout(10):  # REVIEW COMMENT: There should be no magic numbers, it should be defined as a constant e.g - TIMEOUT_IN_SECONDS
        async with session.post(url, data=body) as response:
            return await response.text()
    return None


def notified(responses):
    # REVIEW COMMENT: Incorrect spelling of `notified`
    return "I notifed everyone - you are ready to go on vacation 🏖"


# REVIEW COMMENT this function is never used, can be removed?
def ensure_future(tasks):
    if not asyncio.futures.isfuture(tasks):
        return None
    return asyncio.gather(tasks)


def is_valid_vacation_request(payload):
    return (payload["employee"] is not None and
            payload["end"] > payload["start"])  # REVIEW COMMENT: null check for "start" and "end" missing.


@app.route("/health")
def health():
    return "Ok"


@app.route("/vacation", methods=["POST"])
def index():
    # REVIEW COMMENT - Incorrect spelling for `employee`.
    """Employe can send a webrequest to this endpoint to request vacation. 

    The request will be forwarded to internal systems to register the
    vacation. The format of the reuqest should be

    Example:
        $ curl \
            -XPOST \
            -H "Content-Type: application/json" \
            localhost:5000/vacation \
            -d '{"employee":"tom", "start": 1549381557, "end": 1549581523}'

    """
    payload = request.json
    if not is_valid_vacation_request(payload):
        # REVIEW COMMENT - Since the error is on client side the code used should be `400`, the Http standard for BAD_REQUEST
        # REVIEW COMMENT - it would be even better to use a library with HTTP constants rather than raw numbers.
        abort(404, "Invalid vacation request!")

    # perform multiple async requests concurrently
    # to notify webhooks
    responses = loop.run_until_complete(asyncio.gather(
        # REVIEW COMMENT - Convert the payload before calling fetch (see the above comments).
        fetch("https://api.hr-management.com/webhook", payload),
        # It will also ensure that you convert it only once not and not for each call.
        fetch("https://api.hr-management.com/webhook", payload),
        fetch("https://api.sprintboard.com/notify", payload)
    ))
    # do something with the results
    return notified(responses)


app.run(debug=False, use_reloader=False)
