import requests
from bs4 import BeautifulSoup
import json
import time
import csv
import pandas as pd
import subprocess

class GPT:
    def init(self, api_key):
        self.url = 'https://app.gpt-trainer.com/api/v1/chatbot/create'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        self.uuid = b5357df6092a408396bdfb3df1c08e65
        self.sessionuuid = None

    def create_session(self):
        if not self.uuid:
            print("UUID not found. Create the chatbot first.")
            return
        sessionurl = f'https://app.gpt-trainer.com/api/v1/chatbot/{self.uuid}/session/create'
        response = requests.post(sessionurl, headers=self.headers)
        if response.status_code == 200:
            print("Session creation successful!")
            response_json = response.json()
            print(response_json)
            self.sessionuuid = response_json.get('uuid')
        else:
            print("Session creation failed with status code:", response.status_code)
            print(response.text)

    def create_message(self, message_data):
        if not self.sessionuuid:
            print("Session UUID not found. Create the session first.")
            return None
        messageurl = f'https://app.gpt-trainer.com/api/v1/session/{self.sessionuuid}/message/stream'
        response = requests.post(messageurl, headers=self.headers, json=message_data, stream=True)
        if response.status_code == 200:
            output_text = ""
            for line in response.iter_lines(decode_unicode=True):
                output_text += line + '\n'
            if output_text.strip():
                return output_text
            else:
                print("Empty response received from the server.")
                return None
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response content: {response.text}")
            return None

    def count_nuclei_with_fiji(self, image_path, macro_path="/workspaces/Counter/count_nuclei.ijm"):
        fiji_path = "/path/to/Fiji.app/ImageJ-linux64"  # Update this path to your Fiji installation
        cmd = [
            fiji_path,
            "--headless",
            "--run", macro_path,
            f"input='{image_path}'"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            output = result.stdout + result.stderr
            # Parse output for nuclei count
            for line in output.splitlines():
                if "Count:" in line:
                    count = int(line.split("Count:")[1].strip())
                    return count
            print("Nuclei count not found in Fiji output.")
            print(output)
            return None
        except Exception as e:
            print(f"Error running Fiji: {e}")
            return None
 