import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import wikipedia
import pyjokes
import requests
import webbrowser
import smtplib
import os

listener = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def talk(text):
    engine.say(text)
    engine.runAndWait()

def take_command():
    command = ""
    try:
        with sr.Microphone() as source:
            print('Listening...')
            listener.adjust_for_ambient_noise(source)
            voice = listener.listen(source)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'alexa' in command:
                command = command.replace('alexa', '')
                print(command)
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    except Exception as e:
        print(f"Error: {e}")
    return command

def run_alexa():
    command = take_command()
    print(f"User said: {command}")
    
    if 'play' in command:
        song = command.replace('play', '')
        talk('playing ' + song)
        pywhatkit.playonyt(song)
        
    elif 'time' in command:
        time = datetime.datetime.now().strftime('%I:%M %p')
        talk('The current time is ' + time)
        print(time)
        
    elif 'date' in command:
        date = datetime.datetime.now().strftime('%B %d, %Y')
        talk('Today is ' + date)
        print(date)
        
    elif 'who is' in command:
        person = command.replace('who is', '')
        info = wikipedia.summary(person, 1)
        print(info)
        talk(info)
        
    elif 'joke' in command:
        talk(pyjokes.get_joke())
        
    elif 'hello' in command:
        talk('Hi!')
        
    elif 'how are you doing' in command:
        talk('I am doing good! Thanks for asking!')
   
        
    elif 'bye' in command:
        talk('Goodbye!')
        quit()
        
    elif 'weather in pakistan' in command:
        weather_api_key = 'ae2ca5b091034484b0e191525241107'
        weather_url = f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q=Pakistan"
        response = requests.get(weather_url)
        weather_data = response.json()
        
        if 'error' in weather_data:
            talk("Sorry, I couldn't fetch the weather information for Pakistan at the moment.")
        else:
            description = weather_data['current']['condition']['text']
            temperature = weather_data['current']['temp_c']
            talk(f"The weather in Pakistan is currently {description}. The temperature is {temperature} degrees Celsius.")
            
    elif 'search' in command:
        search_term = command.replace('search', '')
        url = f"https://www.google.com/search?q={search_term}"
        webbrowser.open(url)
        talk(f"Here are the search results for {search_term}")
            
    elif 'open website' in command:
        try:
            website = command.replace('open website', '')
            url = f"https://{website}.com"
            webbrowser.open(url)
            talk(f"Opening {website}")
        except Exception as e:
            print(e)
            talk(f"Sorry, I can't open {website} right now.")
            
    elif 'calculate' in command:
        try:
            calculation = command.replace('calculate', '')
            result = eval(calculation)
            talk(f"The result of {calculation} is {result}")
        except Exception as e:
            print(e)
            talk('Sorry, I could not perform the calculation.')
            
    else:
        talk('Please say the command again.')

while True:
    run_alexa()
