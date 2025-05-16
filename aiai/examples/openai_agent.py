#!/usr/bin/env python3

import os

import openai


def generate_text() -> str:
    prompt = """You are a product manager for a smart home device company. 
        Create a detailed product description for our new AI-powered home security system that includes:
        1. The key features and benefits
        2. Technical specifications
        3. How it integrates with other smart home devices
        4. Privacy and security measures
        5. Pricing options (basic, premium, and professional tiers)
        
        The description should be persuasive and suitable for our website's product page."""

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    # Return the generated text
    return response.choices[0].message.content


def analyze_text(text: str) -> dict:
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    analysis_prompt = f"Analyze this text and provide a summary, sentiment, and key points:\n{text}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": analysis_prompt}],
    )
    return response.choices[0].message.content


def main():
    generated_text = generate_text()
    analysis_result = analyze_text(generated_text)
    return analysis_result


if __name__ == "__main__":
    main()
