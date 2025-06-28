from openai import OpenAI
import os
from dotenv import load_dotenv
import random

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_tweet(context_file="context.txt"):
    """Generate tweet using enhanced context from multiple sources"""
    
    # Read the limited context (should be ~100 tokens)
    context = ""
    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            context = f.read().strip()

    # Tweet style variations
    tweet_styles = [
        "professional_insight",
        "thought_provoking", 
        "trend_analysis",
        "educational",
        "conversational"
    ]
    
    style = random.choice(tweet_styles)
    
    # Build enhanced prompt based on context availability
    if context:
        base_prompt = f"""Current tech landscape context: {context}

Based on this real-time information, create an engaging tweet that:"""
        
        style_prompts = {
            "professional_insight": """
- Provides a professional insight or analysis
- Connects multiple trends or pieces of information  
- Uses 1-2 relevant hashtags naturally
- Maintains authoritative but approachable tone
- 100-120 strictly characters""",
            
            "thought_provoking": """
- Asks a compelling question or presents a contrarian view
- Challenges conventional thinking about current trends
- Encourages discussion and engagement
- Uses 1-2 hashtags strategically
- 100-120 strictly characters""",
            
            "trend_analysis": """
- Synthesizes multiple data points into a clear trend observation
- Provides forward-looking perspective
- Uses specific examples from the context
- Includes 2-3 relevant hashtags
- 100-140 strictly characters""",
            
            "educational": """
- Explains a complex concept in simple terms
- Breaks down recent developments for broader audience
- Uses analogies or examples when helpful
- Includes 1-2 educational hashtags
- 120-130 strictly characters""",
            
            "conversational": """
- Shares a personal observation or "hot take"
- Uses casual but professional language
- Relates to current events in relatable way
- Includes 1-2 hashtags naturally
- 100-120 characters strictly"""
        }
        
        prompt = base_prompt + style_prompts[style]
        
    else:
        # Fallback when no context available
        prompt = """Create a fresh, insightful AI/tech tweet that:
- Discusses recent developments in AI, machine learning, or tech
- Provides unique perspective or analysis
- Uses 1-2 relevant hashtags (#AI #MachineLearning #Tech #Innovation)
- Maintains professional but engaging tone
- Avoids generic statements
- 130-150 characters Strictly
- Uses only BMP-compatible emojis if needed"""

    # Add some randomization to prevent repetitive outputs
    creativity_boosters = [
        "\n\nMake it memorable and shareable.",
        "\n\nEnsure it sparks curiosity.",
        "\n\nFocus on the 'why this matters' angle.",
        "\n\nConnect it to broader implications.",
        "\n\nMake it actionable or thought-provoking."
    ]
    
    prompt += random.choice(creativity_boosters)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Slightly higher for more creativity
            max_tokens=70,     # Increased slightly for longer tweets
            presence_penalty=0.1,  # Encourage new topics
            frequency_penalty=0.2  # Reduce repetition
        )

        tweet = response.choices[0].message.content.strip()
        
        # Clean up common issues
        tweet = tweet.replace('"', '"').replace('"', '"')  # Fix smart quotes
        tweet = tweet.replace(''', "'").replace(''', "'")  # Fix smart apostrophes
        
        # Remove any leading/trailing punctuation that might get added
        if tweet.startswith(('Tweet:', 'Post:', '"', "'")):
            tweet = tweet.split(':', 1)[-1].strip(' "\'')
        
        print(f"📝 Generated tweet ({len(tweet)} chars): {tweet}")
        return tweet
        
    except Exception as e:
        print(f"❌ Tweet generation failed: {e}")
        return None

def validate_tweet(tweet):
    """Validate tweet meets basic requirements"""
    if not tweet:
        return False, "Tweet is empty"
    
    if len(tweet) > 280:
        return False, f"Tweet too long: {len(tweet)} characters"
    
    if len(tweet) < 50:
        return False, f"Tweet too short: {len(tweet)} characters"
    
    # Check for hashtags
    if "#" not in tweet:
        return False, "No hashtags found"
    
    return True, "Valid"

def generate_tweet_with_validation(context_file="context.txt", max_attempts=3):
    """Generate tweet with validation and retry logic"""
    
    for attempt in range(max_attempts):
        tweet = generate_tweet(context_file)
        
        if tweet:
            is_valid, message = validate_tweet(tweet)
            if is_valid:
                return tweet
            else:
                print(f"⚠️ Attempt {attempt + 1}: {message}")
        
        if attempt < max_attempts - 1:
            print("🔄 Retrying tweet generation...")
    
    print("❌ Failed to generate valid tweet after all attempts")
    return None