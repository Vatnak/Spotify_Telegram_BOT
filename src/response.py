def handle_response(text: str) -> str:
    processed: str = text.lower()
    if "hello" in processed:
        return "hi welcome to my bot"
    
    if "how are you" in processed:
        return "Im fine thank you"
    
    return "i do not understand"

