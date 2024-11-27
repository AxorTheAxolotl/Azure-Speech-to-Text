# Speech-to-Text with Azure
### This script sets you up to talk to the microphone, and with Azure's Speech SDK, it will transcribe it and read it back to you in a chosen voice. The default key to toggle listening is `Z`. Windows only. Please note that a Speech SDK key is required to use this program. Create your Azure account before continuing.

## Setup
### Executable
Simply run `AzureTTS.exe` and it'll guide you from creating for `config.json` file. You will not go through this again until you move/delete the json or if some variables are blank, excluding `toggle_key`.
### Source
The latest version of Python and pip is recommended. Download/update python at https://www.python.org/downloads/windows/, and pip with
```
python -m pip install --upgrade pip
```
Then, after installing/updating both, clone this repository, and download the required dependencies.
```
git clone https://github.com/AxorTheAxolotl/Azure-Speech-to-Text.git
cd Azure-Speech-to-Text
pip install -r requirements.txt
```
Finally, run the Python script `AzureTTS.py` and it'll guide you from creating for `config.json` file. You will not go through this again until you move/delete the json or if some variables are blank, excluding `toggle_key`.
```
python AzureTTS.py
```
## `config.json` Sample
Your json will be created at a first run, however, if you want to make your own, the format is as follows:
```
{
  "toggle_key": "z",
  
  "azure_speech_key": "[YOUR SDK KEY]",
  "azure_service_region": "[YOUR NEAREST REGION]",
  
  "voicename": "en-US-AnaNeural",
  "rate": "+0%",
  "pitch": "+0%",
  "volume": "+0%"
}
```

To find a list of service regions and voices, follow these links:
https://learn.microsoft.com/en-us/azure/databricks/resources/supported-regions
https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
