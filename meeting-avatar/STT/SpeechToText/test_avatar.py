from avatar import Avatar

def test_avatar():
    avatar = Avatar()
    
    # Test text summarization and speech
    test_text = """
    Artificial Intelligence (AI) is transforming the way we live and work. 
    It powers everything from smart assistants to autonomous vehicles. 
    Machine learning, a subset of AI, enables systems to learn from data and improve over time.
    Natural Language Processing helps computers understand and generate human language.
    Computer vision allows machines to interpret and analyze visual information from the world.
    """
    
    print("1. Testing text summarization and speech...")
    success = avatar.summarize_and_speak(test_text)
    print(f"Text-to-speech successful: {success}\n")
    
    print("2. Testing speech recording and recognition...")
    print("Please speak for 5 seconds when recording starts...")
    full_text, summary = avatar.process_speech(duration=5)
    
    if full_text and summary:
        print("\nTranscribed Text:")
        print(full_text)
        print("\nSummary:")
        print(summary)
    else:
        print("Speech processing failed")
    
    # Cleanup
    avatar.cleanup_temp_files()

if __name__ == "__main__":
    test_avatar()