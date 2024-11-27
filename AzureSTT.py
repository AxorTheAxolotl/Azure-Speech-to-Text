import os
import azure.cognitiveservices.speech as speechsdk
import sounddevice as sd
import numpy as np
import threading
import json
import time

# this alone might be why it'll probably only work on windows. oops. dunno how to test on other systems.
import win32gui
import win32con
import ctypes
import keyboard

hwnd = ctypes.windll.kernel32.GetConsoleWindow()
user32 = ctypes.windll.user32
x_position = max(0, user32.GetSystemMetrics(0) - 450 - 0)
y_position = max(0, user32.GetSystemMetrics(1) - 290 - 40)

def get_console_window():
    kernel32 = ctypes.WinDLL('kernel32')
    return kernel32.GetConsoleWindow()

def set_window_always_on_top(window_handle):
    win32gui.SetWindowPos(window_handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

console_window = get_console_window()

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

# load configuration from the json file
def load_config():
    with open('config.json', 'r') as file:
        config = json.load(file)
    return config
    
def create_config_json():
    config_data = {
        "toggle_key": 'z',
        
        "azure_speech_key": azure_speech_key,
        "azure_service_region": azure_service_region,
        
        "voicename": voicename,
        "rate": rate,
        "pitch": pitch,
        "volume": volume
    }
    
    with open('config.json', 'w') as json_file:
        json.dump(config_data, json_file, indent=4)
    input("config.json has been created. To change it later, edit the json file. Press enter to proceed...")

def get_user_input():
    global azure_speech_key, azure_service_region, voicename, rate, pitch, volume
    
    if not azure_speech_key:
        azure_speech_key = input("Enter your Azure Speech API Key: ")
    if not azure_service_region:
        azure_service_region = input("Enter your Azure service region (List can be found at https://learn.microsoft.com/en-us/azure/databricks/resources/supported-regions ; Closest region is recommended.): ")
    if not voicename:
        voicename = input("Enter the synthesized voice (List will be found at https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts): ")
    
    if not rate:
        rate_input = input("\nThe default value will be +0.\nEnter speech rate: ")
        rate = f"{rate_input}%" if rate_input else "+0%"
    if not pitch:
        pitch_input = input("Enter pitch value: ")
        pitch = f"{pitch_input}%" if pitch_input else "-2%"
    if not volume:
        volume_input = input("Enter volume value: ")
        volume = f"{volume_input}%" if volume_input else "+0%"
        
def get_user_input_create():
    global azure_speech_key, azure_service_region, voicename, rate, pitch, volume

    azure_speech_key = input("Enter your Azure Speech API Key: ")
    azure_service_region = input("Enter your Azure service region (List can be found at https://learn.microsoft.com/en-us/azure/databricks/resources/supported-regions ; Closest region is recommended.): ")
    
    voicename = input("Enter the synthesized voice (List will be found at https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts): ")
    rate_input = input("\nThe default value will be +0.\nEnter speech rate: ")
    rate = f"{rate_input}%" if rate_input else "+0%"
    pitch_input = input("Enter pitch value: ")
    pitch = f"{pitch_input}%" if pitch_input else "-2%"
    volume_input = input("Enter volume value: ")
    volume = f"{volume_input}%" if volume_input else "+0%"

def group_sound_devices():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()  # get host devices/apis
    group_devices = {api['name']: [] for api in hostapis}  # categorize based on said hosts
    group_devices["Other"] = []  # add an "Other" category for uncategorized devices

    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            hostapi_name = hostapis[device['hostapi']]['name']  # get api name from index
            if hostapi_name in group_devices:
                group_devices[hostapi_name].append((i, device))
            else:
                group_devices["Other"].append((i, device))

    return group_devices

# select output device (attempting to select an *input* just breaks the script, sorry)
def select_output_device():
    group_devices = group_sound_devices()
    
    print("Available audio output devices:")
    for api, devices in group_devices.items():
        if devices:
            print(f"\n{api}:")
            for idx, device in devices:
                print(f"  {idx}: {device['name']}")
    
    while True:
        try:
            selected_device = int(input("\nSelect the output device number for playback: "))
            if any(selected_device == idx for api_devices in group_devices.values() for idx, _ in api_devices):
                sd.default.device = (sd.default.device[0], selected_device)
                print(f"Selected device: {sd.query_devices()[selected_device]['name']}")
                break
            else:
                print("Invalid device number. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

# convert text to speech and play the audio
def text_to_speech(text):
    global rate, pitch, volume
    
    speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_service_region)
    speech_config.speech_synthesis_voice_name = voicename
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm)
    
    # ssml... whatever works lol
    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{speech_config.speech_synthesis_voice_name}'>
            <prosody rate='{rate}' pitch='{pitch}' volume='{volume}'>{text}</prosody>
        </voice>
    </speak>
    """

    audio_config = speechsdk.audio.PullAudioOutputStream()
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        # print("Speech synthesized!")
        play_audio(result.audio_data)
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error synthesising speech: {cancellation_details.error_details}")

# play the synthesized speech audio
def play_audio(audio_data):
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    sd.play(audio_array, samplerate=24000)

# capture live speech with azure's speech sdk
def recognize_speech():
    speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_service_region)
    speech_config.set_profanity(speechsdk.ProfanityOption.Raw)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    def recognized_handler(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = evt.result.text.strip()
            if recognized_text:
                print(f"You said: {recognized_text}      ")
                time.sleep(0.5)
                threading.Thread(target=text_to_speech, args=(recognized_text,)).start()
    
    def recognizing_handler(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            partial_text = evt.result.text.strip()
            if partial_text:
                print(f"Transcribing: {partial_text}...", end='\r')
    
    recognizer.recognized.connect(recognized_handler)
    recognizer.recognizing.connect(recognizing_handler)
    
    # start listening for the given key to toggle recognition
    print(f"Ready! Press '{toggle_key}' to toggle listening.")
    
    is_listening = False
    
    while True:
        focused_window = win32gui.GetForegroundWindow()
    
        if focused_window == console_window:
            if keyboard.is_pressed(toggle_key):
                if is_listening:
                    recognizer.stop_continuous_recognition_async()
                    print("Stopped listening.")
                else:
                    recognizer.start_continuous_recognition()
                    print("Started listening. Speak into the microphone.")
                is_listening = not is_listening
                time.sleep(1)  # add delay to avoid accidental instant toggles
    
        time.sleep(0.15)

def main():
    global config, toggle_key, azure_speech_key, azure_service_region, voicename, rate, pitch, volume
    
    # grabs the default input device index
    devices = sd.query_devices()
    default_input_device_index = sd.default.device[0]
    default_microphone_name = devices[default_input_device_index]['name']
    
    os.system('title Azure STT Synthesizer')
    cls()
    print("Welcome! This Python program transcribes your voice, then uses the transcription to use a voice from Azure! An API key is required.\nPlease note that it chooses your default microphone. To change it, open Windows settings\n\nThis input device will be used:")
    print(default_microphone_name)
    input("Press enter to start...")
    
    if os.path.isfile('config.json'):
        config = load_config()
    else: 
        input("config.json does not exist. Since it's likely your first time, we'll create a new one from setup. Press enter to begin...")
        cls()
        get_user_input_create()
        create_config_json()
        config = load_config()
    cls()
    if config["toggle_key"] != "":
        toggle_key = config["toggle_key"]
    else:
        toggle_key = 'z'
    azure_speech_key = config["azure_speech_key"]
    azure_service_region = config["azure_service_region"]
    voicename = config["voicename"]
    rate = config["rate"]
    pitch = config["pitch"]
    volume = config["volume"]
    
    get_user_input() # incase if config.json exists but some variables are still blank
    select_output_device() # adding the same function but for input devices break, so you have to change your mic settings for it. 
    input("Press enter to start...")
    cls()
    set_window_always_on_top(console_window)
    ctypes.windll.user32.MoveWindow(hwnd, x_position, y_position, 450, 290, True)
    recognize_speech()

if __name__ == "__main__":
    main()