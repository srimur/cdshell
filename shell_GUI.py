import ctypes
from tkinter import *
from tkterm import Terminal
import os
import json
import logging
from groq import Groq

# Set the API key directly in the script
GROQ_API_KEY = ''

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

# Load the shared library
libshell = ctypes.CDLL('./libshell.so')
libshell.execute_command.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

BUFFER_SIZE = 1024

# Setup logging
logging.basicConfig(filename='cloud_defense.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

def send_to_llm(command):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant who provides security analysis of AWS CLI commands and returns the response in JSON format."
            },
            {
                "role": "user",
                "content": f"Identify security issues with this AWS CLI command and suggest up to 3 improvements, including an updated command if necessary: {command}",
            }
        ],
        model="llama3-8b-8192",
    )
    response = chat_completion.choices[0].message.content
    return json.loads(response)

def parse_command(command):
    parts = command.split()
    provider = parts[0] if len(parts) > 0 else ''
    service = parts[1] if len(parts) > 1 else ''
    action = parts[2] if len(parts) > 2 else ''
    resource = ' '.join(parts[3:]) if len(parts) > 3 else ''
    
    return {
        "provider": provider,
        "service": service,
        "action": action,
        "resource": resource
    }

def execute_command():
    command = terminal.get_command()
    parsed_command = parse_command(command)
    
    # Send the command to LLM for analysis
    analysis = send_to_llm(json.dumps(parsed_command))
    
    # Extract details from the JSON response
    risk_level = analysis.get("risk_level", "Unknown")
    explanation = analysis.get("explanation", "No explanation provided.")
    suggested_command = analysis.get("suggested_safe_command", None)
    
    # Log the command and analysis
    logging.info(f"Command: {command}")
    logging.info(f"Risk Level: {risk_level}")
    logging.info(f"Explanation: {explanation}")
    
    # Display risk level and explanation
    terminal.write(f"Risk Level: {risk_level}\n")
    terminal.write("Explanation:\n")
    for item in explanation:
        terminal.write(f"- {item}\n")
    
    # Automatically use the recommended command if provided
    if suggested_command:
        terminal.write(f"Using Recommended Command: {suggested_command}\n")
        command = suggested_command
    
    # Confirm execution if risk is high
    if risk_level == "High":
        if not terminal.confirm('High risk detected. Do you want to proceed with the recommended command?'):
            return
    
    output = ctypes.create_string_buffer(BUFFER_SIZE)
    libshell.execute_command(command.encode('utf-8'), output)
    terminal.write(output.value.decode('utf-8'))

root = Tk()
root.title("Shell")

terminal = Terminal(root)
terminal.execute_command = execute_command

terminal.pack(fill=BOTH, expand=True)

root.mainloop()
