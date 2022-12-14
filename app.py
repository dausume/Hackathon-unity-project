import os
from flask import Flask, jsonify,request
import asyncio
import aiohttp
from flask_restful import Api, Resource

#Creating a flask template
#http://localhost:5000 is the url for this when run locally
app=Flask(__name__)
api=Api(app)
# Define the mock dialog to be returned as json
dialogTextToReturn = [ 
    { "samplePosition": 0, "character": "Ol Red", "fromUser": False, "textStatement": "I've been where I've been I reckon" },
    { "samplePosition": 0, "character": "Ol Red", "fromUser": True, "textStatement": "Well hello there Ol Red, how have you been?"}
]
whisperUrl = "https://whisper.lablab.ai/asr"

@app.route('/api/getDialogText', methods=['GET'])
def get_data():
    # Return the dialog text as a JSON object
    return jsonify(dialogTextToReturn)

# Expected json payload format : { 'samplePosition':samplePosition, 'character':character, 'audio':wavEncrypted15secAudio }
# Recieves a user's dialog in terms of audio that is wav encoded, along with the audio sequence and character information.
@app.route("/api/processWithAI", methods=["POST"])
async def processData():
    print("Hit processData api")
    # Get the JSON payload containing the audio data
    wavDialogJson = request.get_json()
    print("Got past wavDialogJson")
    # Send the audio data to the OpenAI Whisper API
    await asyncio.create_task(sendToWhisper(wavDialogJson))
    return "processing"

async def sendToWhisper(wavDialogJson):
    print("Hit sendToWhisper")
    async with aiohttp.ClientSession() as session:
        async with session.post(whisperUrl, 
                                data=wavDialogJson['audio'], 
                                headers={
                                'Content-Type': 'application/octet-stream',
                                #'Authorization': 'Bearer YOUR_OPENAI_API_KEY'
                                }) as resp:
            print("Recieved Response from Whisper")
            if resp.status == 200:
                whisperText = await resp.text()
                print("Passed awaiting whisper text")
                print(whisperText)
                #Format the dialogObjectForUser
                userDialog = { 
                    "samplePosition": wavDialogJson["samplePosition"], 
                    "character":  wavDialogJson["character"], 
                    "fromUser": True, 
                    "textStatement": whisperText
                }
                print("set userDialog")
                print(userDialog)
                await dialogTextToReturn.append(userDialog)
                print("appended user dialog to be returned")
                #return the text response from whisper as a text.
                asyncio.run(talkToGPT3(userDialog))
            else:
                print("recieved non-200 response from whisper")
                raise ValueError(f'Received non-200 status code: {resp.status}')

async def talkToGPT3(userDialog):
    print("Hit talkToGPT3 function")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.openai.com/v1/completions', params={
            'prompt': userDialog["textStatement"],
            'model': 'gpt-3',
            'max_tokens': 512,
            'temperature': 0.5,
            'key':'YOUR_API_KEY_HERE (DO NOT PUSH WITH API KEY)'
        }) as response:
            print("Recieved GPT-3 Response")
            if response.status == 200:
                print("Response was 200 code")
                gptText = await response.text()
                print("Got gptText")
                print(gptText)
                gptDialog = { 
                        "samplePosition": userDialog["samplePosition"], 
                        "character":  userDialog["character"], 
                        "fromUser": False, 
                        "textStatement": gptText
                }
                print(gptDialog)
                await dialogTextToReturn.append(gptDialog)
                print("Appended dialog to be returned")
            else:
                print("got non-200 status from GPT-3")
                raise ValueError(f'Received non-200 status code: {response.status}')

if __name__ == "__main__":
    app.run()