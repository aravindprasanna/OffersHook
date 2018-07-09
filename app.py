import json
import os
import requests

from flask import Flask
from flask import request
from flask import make_response

app = Flask(__name__)
url_domain = "http://d7dafd75.ngrok.io/"

#canned responses
FOUND_X_OFFERS = "I found {} offers. Would you like me to refine the search?"
FOUND_SPEC_OFFER = ''' Here is the offer. {} . You can get the next offer by saying "Next". 
'''


@app.route('/webhook',methods=['POST'])
def webhook():
    res = ""
    req = request.get_json(silent=True,force=True)
    print(json.dumps(req,indent=4))

    query_result = req.get("queryResult")
    action = query_result.get("action")

    if action == "FetchOffersGen":
        res = get_offers(req)
    elif action == "FetchOffersGen-No":
        res = get_offer(req)

    res = json.dumps(res,indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'

    return r


def get_offer(req_json):
    session = req_json.get("session")
    print(req_json)
    output_contexts = req_json["queryResult"].get("outputContexts")
    print("output", output_contexts)
    context_name = session + "/contexts/offer_context"
    offers_list = []
    offer_index = 0
    offer_type = ""
    for context_item in output_contexts:
        if context_item.get("name") == context_name:
            offers_list = context_item["parameters"]["offer_list"]
            offer_index = context_item["parameters"]["offer_index"]
            offer_type = context_item["parameters"]["offer_type"]

    selected_offer = offers_list[offer_index+1]

    api_name = "get/offer/{0}/".format(selected_offer)
    resp_json = call_offers_voice(url_domain + api_name)

    offer_details = resp_json["offer_details"]

    context_lifespan = 5
    offer_index += 1
    offer_activities = ""
    offer_card = ""

    #offer_details = selected_offer["offer_details"]
    print(offer_details)
    speech = FOUND_SPEC_OFFER.format(offer_details)
    resp = build_response_json(speech,
                                        context_name,
                                        context_lifespan,
                                        offer_type,
                                        offers_list,
                                        offer_index,
                                        offer_activities,
                                        offer_card)

    return resp

def get_offers(req_json):
    session = req_json.get("session")
    offer_type = req_json["queryResult"]["parameters"]["offer_type"]
    api_name = "get/offers/{0}/all/all".format(offer_type)
    response_json = call_offers_voice(url_domain + api_name)
    offers_list = response_json["offer_list"]
    offer_index = -1
    no_of_offers = len(offers_list)
    context_name = session + "/contexts/offer_context"
    context_lifespan = 5
    offer_index = -1
    offer_activities = ""
    offer_card = ""

    speech = FOUND_X_OFFERS.format(no_of_offers)
    json_response = build_response_json(speech,
                                            context_name,
                                            context_lifespan,
                                            offer_type,
                                            offers_list,
                                            offer_index,
                                            offer_activities,
                                            offer_card
                                            )

    return json_response


def build_response_json(speech,context_name,context_lifespan,offer_type,offers_list,offer_index,
                        offer_activities,offer_card):
    JSON_SPEECH_ONLY = {
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
        },
        "outputContexts": [
            {
                "name": context_name,
                "lifespanCount": context_lifespan,
                "parameters": {
                    "offer_type": offer_type,
                    "offer_list": offers_list,
                    "offer_index": offer_index,
                    "offer_activities": offer_activities,
                    "offer_card": offer_card
                }
            }
        ]
    }

    return JSON_SPEECH_ONLY

def call_offers_voice(url):
    print(url)
    r = requests.get(url)
    json_object = r.json()

    return json_object




if __name__ == '__main__':
    port = int(os.getenv('PORT',5000))
    print("Starting app on port {}".format(port))
    app.run(debug=False,port=port,host='0.0.0.0')
