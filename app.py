import json
import os
import requests

from flask import Flask
from flask import request
from flask import make_response

app = Flask(__name__)


@app.route('/webhook',methods=['POST'])
def webhook():
    req = request.get_json(silent=True,force=True)
    print(json.dumps(req,indent=4))

    res = makeResponse(req)
    res = json.dumps(res,indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'

    return r


def makeResponse(req):
    result = req.get("queryResult")
    #output_context_name = result.get("outputContexts")[0].get("name")
    action = result.get("action")
    if action == "OffersByType":
        parameters = result.get("parameters")
        offer_type = parameters.get("type")
        get_url = "http://a408503e.ngrok.io/get/offers/{}/".format(offer_type)
        r = requests.get(get_url)
        json_object = r.json()
        offers = json_object["offer_list"]
        no_of_offers = len(offers)
        speech = ""
        if no_of_offers == 1:
            get_offer_url = "http://a408503e.ngrok.io/get/offer/{}/".format(offers[0])
            r = requests.get(get_offer_url)
            json_object = r.json()
            selected_offer = json_object["offer_details"]
            speech = selected_offer
        else:
            speech = '''I have found {} offers. I can help you refine the search further.
            Would you like me to refine the search?'''
    else:
        parameters = result.get("parameters")
        offer_card = parameters.get("cards")
        offer_type = parameters.get("type")
        offer_activity = parameters.get("activities")
        get_url = "http://a408503e.ngrok.io/get/offers/{}/{}/{}/".format(offer_type,offer_card,offer_activity)
        r = requests.get(get_url)
        json_object = r.json()
        offers = json_object["offer_list"]
        get_offer_url = "http://a408503e.ngrok.io/get/offer/{}/".format(offers[0])
        r = requests.get(get_offer_url)
        json_object = r.json()
        selected_offer = json_object["offer_details"]
        offer_no = 1
        speech = "The offers found are as as follows {}".format(" ".join(offers))
        speech = selected_offer

    return {
        "fulfillmentText": speech,
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        speech
                    ]
                }
            }
        ],
        "payload": {
            "google": {
                "expectUserResponse": True,
                "richResponse": {
                    "items": [
                        {
                            "simpleResponse": {
                                "textToSpeech": speech
                            }
                        }
                    ]
                }
            }
        }
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT',5000))
    print("Starting app on port {}".format(port))
    app.run(debug=False,port=port,host='0.0.0.0')
