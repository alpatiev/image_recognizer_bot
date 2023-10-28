# Simple telegram bot for OCR text recognition tasks
Bot can recognize multiple languages, it depends on model you choose. Supports english and russian languages.
Project will be refactored soon, it's just MVP for now. Feel free to open the issues! 

# Installation
1. Clone the repository:
```
git clone https://github.com/alpatiev/image_recognizer_bot.git
```
2. Navigate to the project directory:
```
cd image_recognizer_bot
```
3. Install all libraries if needed:
```
pip install -r requirements.txt
```
4. Load the models:
```
easyocr -l en ru -f .
```

# Usage
Go to project directory, open config.py and paste bot token from @BotFather:
```
TOKEN = "your_token"
```
Then just just run:
```
python main.py
```

# Credits
This project based on [EasyOCR](https://github.com/JaidedAI/EasyOCR) model.

